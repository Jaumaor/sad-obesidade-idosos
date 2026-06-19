"""
Namespace para endpoints de predição de risco.
Usa mv_idosos_obesos_atual (dados do e-SUS) + risco_estratificado (scores ML).
"""

import datetime
import json
import sys
from decimal import Decimal
from pathlib import Path

from flask import request
from flask_restx import Namespace, Resource
from psycopg2.extras import RealDictRow

# Importar predictor
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
from src.models.predictor import get_predictor


def _sanitize(obj):
    """Converte Decimal, date e RealDictRow para tipos JSON-serializáveis."""
    if isinstance(obj, RealDictRow):
        return {k: _sanitize(v) for k, v in dict(obj).items()}
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    return obj


def create_risco_namespace(deps, models):
    ns = Namespace("risco", path="/api/v1", description="Predicao de risco e scoring")
    
    @ns.route("/risco/calcular/<paciente_id>")
    class RiscoCalcularResource(Resource):
        @ns.doc("calcular_risco_paciente")
        @ns.marshal_with(models["risco_calculado"])
        def post(self, paciente_id):
            """
            Calcula o score de risco para um paciente (co_seq_cidadao).
            Busca dados da mv_idosos_obesos_atual, calcula via ML e salva resultado.
            """
            db, service = deps.build_dashboard_service()
            
            try:
                repo = service.repo
                paciente = repo.get_paciente_detalhes(paciente_id)
                
                if not paciente:
                    return {"error": "Paciente não encontrado"}, 404
                
                # Montar dict para o predictor
                paciente_dict = {
                    'idade': paciente.get('idade'),
                    'peso_kg': paciente.get('peso_kg'),
                    'altura_m': paciente.get('altura_m'),
                    'imc': paciente.get('imc_atual'),
                    'glicemia_mg_dl': paciente.get('glicemia'),
                    'pa_sistolica': paciente.get('pa_sistolica'),
                    'pa_diastolica': paciente.get('pa_diastolica'),
                    'total_comorbidades': paciente.get('total_comorbidades', 0),
                    'dias_sem_visita': paciente.get('dias_sem_visita', 0),
                    'tem_diabetes': paciente.get('tem_diabetes', False),
                    'tem_hipertensao': paciente.get('tem_hipertensao', False),
                    'tem_doenca_cardiaca': paciente.get('tem_doenca_cardiaca', False),
                    'tem_dislipidemia': paciente.get('tem_dislipidemia', False),
                    'tem_irc': paciente.get('tem_irc', False),
                    'tem_depressao': paciente.get('tem_depressao', False),
                    'tem_artrose': paciente.get('tem_artrose', False),
                    'sexo': paciente.get('sexo', 'F'),
                }
                
                # Calcular risco
                predictor = get_predictor()
                resultado = predictor.calcular_risco(paciente_dict)
                
                # Salvar na tabela risco_estratificado
                fatores_json = json.dumps(resultado.get('fatores_risco', []), ensure_ascii=False)
                db.execute_query("""
                    INSERT INTO risco_estratificado 
                    (co_seq_cidadao, score_risco, nivel_risco, fatores_risco, recomendacoes, versao_modelo)
                    VALUES (%(cid)s, %(score)s, %(nivel)s, %(fatores)s::jsonb, %(rec)s, %(ver)s)
                """, {
                    'cid': int(paciente_id),
                    'score': resultado['score_risco'],
                    'nivel': resultado['nivel_risco'],
                    'fatores': fatores_json,
                    'rec': predictor.get_recomendacao(resultado['nivel_risco']),
                    'ver': resultado.get('modelo_versao', '1.0.0'),
                }, fetch=False)
                
                return {
                    "paciente_id": str(paciente_id),
                    "score_risco": resultado['score_risco'],
                    "nivel_risco": resultado['nivel_risco'],
                    "fatores_risco": resultado.get('fatores_risco', []),
                    "metodo": resultado.get('metodo', 'desconhecido'),
                    "recomendacao": predictor.get_recomendacao(resultado['nivel_risco'])
                }, 200
                
            except Exception as e:
                return {"error": f"Erro ao calcular risco: {str(e)}"}, 500
            finally:
                db.close()
    
    @ns.route("/risco/predict")
    class RiscoPredictResource(Resource):
        @ns.doc("predict_risco_direto")
        def post(self):
            """
            Calcula risco a partir de um JSON com dados clínicos (sem banco).
            Útil para testes e integrações externas.
            """
            data = request.get_json()
            if not data:
                return {"error": "JSON body obrigatório"}, 400
            
            predictor = get_predictor()
            resultado = predictor.calcular_risco(data)
            resultado['recomendacao'] = predictor.get_recomendacao(resultado['nivel_risco'])
            return resultado, 200
    
    @ns.route("/risco/pacientes-prioritarios")
    class RiscoPrioritariosResource(Resource):
        @ns.doc(
            "pacientes_prioritarios",
            params={
                "limite": "Quantidade de pacientes (padrão: 20)",
                "nivel_minimo": "Nível mínimo de risco (Baixo, Moderado, Alto, Critico)"
            }
        )
        def get(self):
            """Retorna pacientes com maior risco (MV + risco_estratificado)."""
            limite = request.args.get("limite", default=20, type=int)
            nivel_minimo = request.args.get("nivel_minimo", default="Alto", type=str)
            
            niveis = {'Baixo': ['Alto', 'Critico'], 'Moderado': ['Moderado', 'Alto', 'Critico'],
                      'Alto': ['Alto', 'Critico'], 'Critico': ['Critico']}
            
            db, service = deps.build_dashboard_service()
            try:
                query = """
                    SELECT mv.co_seq_cidadao AS id, mv.codigo_anonimo, mv.idade,
                           r.score_risco, r.nivel_risco, r.fatores_risco, r.recomendacoes,
                           mv.dias_sem_visita, mv.bairro AS territorio
                    FROM mv_idosos_obesos_atual mv
                    JOIN LATERAL (
                        SELECT score_risco, nivel_risco, fatores_risco, recomendacoes
                        FROM risco_estratificado
                        WHERE co_seq_cidadao = mv.co_seq_cidadao
                        ORDER BY data_calculo DESC LIMIT 1
                    ) r ON TRUE
                    WHERE r.nivel_risco = ANY(%(niveis)s)
                    ORDER BY r.score_risco DESC
                    LIMIT %(limite)s
                """
                pacientes = db.execute_query(query, {
                    'niveis': niveis.get(nivel_minimo, ['Alto', 'Critico']),
                    'limite': limite
                })
                return {
                    "total": len(pacientes),
                    "nivel_minimo": nivel_minimo,
                    "pacientes": _sanitize(pacientes)
                }, 200
            except Exception as e:
                return {"error": str(e)}, 500
            finally:
                db.close()
    
    @ns.route("/risco/recalcular-todos")
    class RiscoRecalcularTodosResource(Resource):
        @ns.doc("recalcular_risco_todos")
        def post(self):
            """Recalcula score de risco para todos os pacientes da MV."""
            db, service = deps.build_dashboard_service()
            
            try:
                predictor = get_predictor()
                atualizados = 0
                erros = 0
                
                # Buscar todos da MV
                pacientes = db.execute_query("""
                    SELECT co_seq_cidadao, idade, sexo, peso_kg, altura_cm, imc_atual,
                           pa_sistolica, pa_diastolica, glicemia, total_comorbidades,
                           dias_sem_visita, tem_diabetes, tem_hipertensao,
                           tem_doenca_cardiaca, tem_dislipidemia, tem_irc,
                           tem_depressao, tem_artrose
                    FROM mv_idosos_obesos_atual
                """)
                
                for pac in pacientes:
                    try:
                        paciente_dict = {
                            'idade': pac['idade'],
                            'peso_kg': pac['peso_kg'],
                            'altura_cm': pac['altura_cm'],
                            'imc': pac['imc_atual'],
                            'glicemia_mg_dl': pac['glicemia'],
                            'pa_sistolica': pac['pa_sistolica'],
                            'pa_diastolica': pac['pa_diastolica'],
                            'total_comorbidades': pac['total_comorbidades'],
                            'dias_sem_visita': pac['dias_sem_visita'],
                            'tem_diabetes': pac['tem_diabetes'],
                            'tem_hipertensao': pac['tem_hipertensao'],
                            'tem_doenca_cardiaca': pac['tem_doenca_cardiaca'],
                            'tem_dislipidemia': pac['tem_dislipidemia'],
                            'tem_irc': pac['tem_irc'],
                            'tem_depressao': pac.get('tem_depressao', False),
                            'tem_artrose': pac.get('tem_artrose', False),
                            'sexo': pac['sexo'],
                        }
                        resultado = predictor.calcular_risco(paciente_dict)
                        
                        fatores_json = json.dumps(resultado.get('fatores_risco', []), ensure_ascii=False)
                        db.execute_query("""
                            INSERT INTO risco_estratificado
                            (co_seq_cidadao, score_risco, nivel_risco, fatores_risco, recomendacoes, versao_modelo)
                            VALUES (%(cid)s, %(score)s, %(nivel)s, %(fatores)s::jsonb, %(rec)s, %(ver)s)
                        """, {
                            'cid': pac['co_seq_cidadao'],
                            'score': resultado['score_risco'],
                            'nivel': resultado['nivel_risco'],
                            'fatores': fatores_json,
                            'rec': predictor.get_recomendacao(resultado['nivel_risco']),
                            'ver': resultado.get('modelo_versao', '1.0.0'),
                        }, fetch=False)
                        atualizados += 1
                    except Exception:
                        erros += 1
                
                return {
                    "status": "concluido",
                    "total_pacientes": len(pacientes),
                    "atualizados": atualizados,
                    "erros": erros
                }, 200
                
            except Exception as e:
                return {"error": str(e)}, 500
            finally:
                db.close()
    
    @ns.route("/risco/modelo-info")
    class RiscoModeloInfoResource(Resource):
        @ns.doc("info_modelo")
        def get(self):
            """Retorna informações sobre o modelo de ML em produção."""
            predictor = get_predictor()
            pkg = predictor.model_package or {}
            return {
                "algoritmo": pkg.get('algoritmo', 'não carregado'),
                "auc_roc": pkg.get('auc_roc', None),
                "n_features": len(pkg.get('feature_names', [])),
                "versao": pkg.get('version', 'desconhecida'),
                "data_treinamento": pkg.get('data_treinamento', None),
                "status": "ativo" if predictor.modelo is not None else "fallback_regras"
            }, 200
    
    return ns
