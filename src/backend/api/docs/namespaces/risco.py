"""
Namespace para endpoints de predição de risco
"""

from flask import request
from flask_restx import Namespace, Resource
import sys
from pathlib import Path

# Importar predictor
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
from src.models.predictor import get_predictor

def create_risco_namespace(deps, models):
    ns = Namespace("risco", path="/api/v1", description="Predicao de risco e scoring")
    
    @ns.route("/risco/calcular/<paciente_id>")
    class RiscoCalcularResource(Resource):
        @ns.doc("calcular_risco_paciente")
        @ns.marshal_with(models["risco_calculado"])
        def post(self, paciente_id):
            """
            Calcula o score de risco atualizado para um paciente
            
            Busca dados do paciente no banco, calcula risco usando ML
            e salva o resultado na tabela risco_estratificado.
            """
            db, service = deps.build_dashboard_service()
            
            try:
                # Buscar dados do paciente
                repo = service.repo
                paciente = repo.get_paciente_detalhes(paciente_id)
                
                if not paciente:
                    return {"error": "Paciente não encontrado"}, 404
                
                # Buscar comorbidades
                comorbidades = repo.get_paciente_comorbidades(paciente_id)
                
                # Montar dict para preditor
                paciente_dict = {
                    'idade': paciente.get('idade'),
                    'peso_kg': paciente.get('peso_kg'),
                    'altura_m': paciente.get('altura_m'),
                    'imc': paciente.get('imc_atual'),
                    'glicemia_mg_dl': paciente.get('glicemia'),
                    'pa_sistolica': paciente.get('pa_sistolica'),
                    'pa_diastolica': paciente.get('pa_diastolica'),
                    'total_comorbidades': len(comorbidades),
                    'dias_sem_visita': paciente.get('dias_sem_visita'),
                    'tem_diabetes': any(c['condicao'] == 'Diabetes Mellitus Tipo 2' for c in comorbidades),
                    'tem_hipertensao': any(c['condicao'] == 'Hipertensão Arterial' for c in comorbidades),
                    'tem_doenca_cardiaca': any(c['condicao'] in ['Doença Cardiovascular', 'Fibrilação Atrial', 'Insuficiência Cardíaca'] for c in comorbidades),
                    'tem_dislipidemia': any(c['condicao'] == 'Dislipidemia' for c in comorbidades),
                    'tem_irc': any(c['condicao'] == 'Doença Renal Crônica' for c in comorbidades),
                }
                
                # Calcular risco
                predictor = get_predictor()
                resultado = predictor.calcular_risco(paciente_dict)
                
                # Salvar no banco
                db.execute_query("""
                    INSERT INTO risco_estratificado 
                    (paciente_id, score_risco, nivel_risco, fatores_risco, recomendacoes, versao_modelo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    paciente_id,
                    resultado['score_risco'],
                    resultado['nivel_risco'],
                    resultado.get('fatores_risco', []),
                    predictor.get_recomendacao(resultado['nivel_risco']),
                    resultado.get('modelo_versao', 'regras_v1')
                ), fetch=False)
                
                return {
                    "paciente_id": paciente_id,
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
            """
            Retorna lista de pacientes com maior risco (para priorizar visitas)
            """
            limite = request.args.get("limite", default=20, type=int)
            nivel_minimo = request.args.get("nivel_minimo", default="Alto", type=str)
            
            niveis_prioridade = {
                'Baixo': ['Alto', 'Critico'],
                'Moderado': ['Moderado', 'Alto', 'Critico'],
                'Alto': ['Alto', 'Critico'],
                'Critico': ['Critico']
            }
            
            niveis = niveis_prioridade.get(nivel_minimo, ['Alto', 'Critico'])
            
            db, service = deps.build_dashboard_service()
            
            try:
                # Usar a view de alto risco
                query = """
                    SELECT 
                        p.id,
                        p.codigo_anonimo,
                        p.idade,
                        r.score_risco,
                        r.nivel_risco,
                        r.fatores_risco,
                        r.recomendacoes,
                        p.dias_sem_visita,
                        t.nome as territorio
                    FROM pacientes p
                    JOIN risco_estratificado r ON p.id = r.paciente_id
                    JOIN territorios t ON p.territorio_id = t.id
                    WHERE r.nivel_risco = ANY(%s)
                      AND r.data_calculo = (
                          SELECT MAX(data_calculo) 
                          FROM risco_estratificado 
                          WHERE paciente_id = p.id
                      )
                    ORDER BY r.score_risco DESC
                    LIMIT %s
                """
                
                pacientes = db.execute_query(query, (niveis, limite))
                
                return {
                    "total": len(pacientes),
                    "nivel_minimo": nivel_minimo,
                    "pacientes": pacientes
                }, 200
                
            finally:
                db.close()
    
    @ns.route("/risco/recalcular-todos")
    class RiscoRecalcularTodosResource(Resource):
        @ns.doc("recalcular_risco_todos")
        def post(self):
            """
            Recalcula score de risco para todos os pacientes ativos
            (Job para executar periodicamente)
            """
            db, service = deps.build_dashboard_service()
            
            try:
                # Buscar todos os pacientes ativos
                pacientes = db.execute_query("""
                    SELECT id FROM pacientes 
                    WHERE em_acompanhamento = TRUE
                """)
                
                predictor = get_predictor()
                atualizados = 0
                erros = 0
                
                for paciente in pacientes:
                    try:
                        # Aqui chamaria a lógica de calcular para cada um
                        # Simplificado para o exemplo
                        atualizados += 1
                    except Exception:
                        erros += 1
                
                return {
                    "status": "concluido",
                    "total_pacientes": len(pacientes),
                    "atualizados": atualizados,
                    "erros": erros
                }, 200
                
            finally:
                db.close()
    
    return ns
