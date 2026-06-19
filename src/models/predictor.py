"""
Módulo de Predição de Risco para o SAD
Usado pela API para calcular scores em produção.

Gera as 33 features numéricas esperadas pelo GradientBoosting treinado.
"""

import pickle
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Estatísticas do dataset de treino (para Z-scores em produção)
_TRAIN_STATS = {
    'imc': {'mean': 39.32, 'std': 4.49},
    'idade': {'mean': 67.50, 'std': 6.48},
}


class RiskPredictor:
    """
    Preditor de risco de abandono/complicações para idosos obesos.
    Gera as 33 features numéricas alinhadas com o modelo treinado.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializa o preditor carregando o modelo treinado
        """
        if model_path is None:
            model_path = Path(__file__).parent / "risk_model.pkl"
        
        self.model_path = Path(model_path)
        self.model_package = None
        self.modelo = None
        self.scaler = None
        self.feature_names = None
        self.regras = None
        
        self._load_model()
        self._load_regras()
    
    def _load_model(self):
        """Carrega o modelo do disco"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model_package = pickle.load(f)
            
            self.modelo = self.model_package['modelo']
            self.scaler = self.model_package.get('scaler')
            self.feature_names = self.model_package['feature_names']
            
            logger.info(f"Modelo carregado: {self.model_package.get('algoritmo', 'desconhecido')}")
            logger.info(f"Features: {len(self.feature_names)}")
            
        except FileNotFoundError:
            logger.error(f"Modelo não encontrado em {self.model_path}")
            self.modelo = None
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            self.modelo = None
    
    def _load_regras(self):
        """Carrega regras de negócio como fallback"""
        regras_path = Path(__file__).parent / "regras_risco.json"
        try:
            with open(regras_path, 'r') as f:
                self.regras = json.load(f)
        except FileNotFoundError:
            logger.warning("Arquivo de regras não encontrado")
            self.regras = None
    
    def calcular_risco_ml(self, paciente: Dict) -> Dict:
        """
        Calcula risco usando o modelo de ML
        
        Args:
            paciente: Dicionário com dados do paciente
            
        Returns:
            Dict com score, nível de risco e fatores
        """
        if self.modelo is None:
            raise ValueError("Modelo não carregado")
        
        # Preparar features no formato esperado (33 numéricas)
        features = self._extrair_features(paciente)
        
        # Criar DataFrame com mesma ordem de features do treino
        X = pd.DataFrame([features])
        
        # Garantir todas as features estão presentes
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0
        
        X = X[self.feature_names]
        
        # Normalizar se necessário
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Predição
        score = self.modelo.predict_proba(X_scaled)[0][1]  # Prob classe 1 (alto risco)
        score_int = int(score * 100)  # 0-100
        
        # Classificar nível
        nivel = self._classificar_nivel(score_int)
        
        # Identificar fatores de risco
        fatores = self._identificar_fatores(paciente)
        
        return {
            'score_risco': round(score_int, 1),
            'nivel_risco': nivel,
            'probabilidade_alto_risco': round(score, 4),
            'fatores_risco': fatores,
            'metodo': 'machine_learning',
            'modelo_versao': self.model_package.get('version', '1.0.0')
        }
    
    def calcular_risco_regras(self, paciente: Dict) -> Dict:
        """
        Calcula risco usando regras de negócio (fallback)
        """
        score = 0
        fatores = []
        
        # 1. Tempo sem visita
        dias = paciente.get('dias_sem_visita', 0)
        if dias > 90:
            score += 40
            fatores.append(f'Sem visita há {dias} dias')
        elif dias > 60:
            score += 25
            fatores.append(f'Sem visita há {dias} dias')
        elif dias > 45:
            score += 10
        
        # 2. IMC
        imc = paciente.get('imc', 0) or paciente.get('imc_calculado', 0)
        if imc >= 45:
            score += 25
            fatores.append(f'IMC crítico ({imc:.1f})')
        elif imc >= 40:
            score += 15
            fatores.append(f'Obesidade Grau III ({imc:.1f})')
        elif imc >= 35:
            score += 10
        
        # 3. Comorbidades
        comorbidades = paciente.get('total_comorbidades', 0)
        if comorbidades >= 4:
            score += 20
            fatores.append(f'{comorbidades} comorbidades ativas')
        elif comorbidades >= 2:
            score += 10
            fatores.append(f'{comorbidades} comorbidades ativas')
        
        # 4. Condições específicas
        if paciente.get('tem_diabetes'):
            score += 10
            fatores.append('Diabetes Mellitus')
        if paciente.get('tem_doenca_cardiaca'):
            score += 15
            fatores.append('Doença cardiovascular')
        if paciente.get('tem_irc'):
            score += 15
            fatores.append('Insuficiência renal')
        
        # 5. Idade avançada
        idade = paciente.get('idade', 60)
        if idade >= 80:
            score += 10
            fatores.append(f'Idade avançada ({idade} anos)')
        elif idade >= 75:
            score += 5
        
        # Normalizar score (0-100)
        score = min(score, 100)
        
        nivel = self._classificar_nivel(score)
        
        return {
            'score_risco': score,
            'nivel_risco': nivel,
            'fatores_risco': fatores,
            'metodo': 'regras_negocio'
        }
    
    def calcular_risco(self, paciente: Dict) -> Dict:
        """
        Calcula risco usando ML se disponível, senão regras
        """
        try:
            if self.modelo is not None:
                return self.calcular_risco_ml(paciente)
        except Exception as e:
            logger.warning(f"Falha no ML, usando regras: {e}")
        
        return self.calcular_risco_regras(paciente)
    
    def _extrair_features(self, paciente: Dict) -> Dict:
        """
        Extrai as 33 features numéricas esperadas pelo modelo.
        
        Chaves aceitas no dict paciente:
            idade, peso_kg, altura_cm (ou altura_m), imc,
            pa_sistolica, pa_diastolica, glicemia_mg_dl,
            total_comorbidades, dias_sem_visita,
            tem_diabetes, tem_hipertensao, tem_doenca_cardiaca,
            tem_dislipidemia, tem_irc, tem_depressao, tem_artrose,
            sexo ('F' ou 'M')
        """
        f = {}
        
        # --- Valores base ---
        idade = float(paciente.get('idade', 65))
        imc = float(paciente.get('imc', 0) or paciente.get('imc_calculado', 35))
        peso = float(paciente.get('peso_kg', 80))
        
        # altura: aceita cm ou metros
        alt = float(paciente.get('altura_cm', 0) or 0)
        if alt == 0:
            alt_m = float(paciente.get('altura_m', 1.55) or 1.55)
            alt = alt_m * 100  # converter para cm
        
        pa_sis = paciente.get('pa_sistolica')
        pa_dia = paciente.get('pa_diastolica')
        glicemia = paciente.get('glicemia_mg_dl')
        dias = float(paciente.get('dias_sem_visita', 0) or 0)
        sexo = paciente.get('sexo', paciente.get('no_sexo', 'F'))
        
        # ─── 1. ANTROPOMÉTRICAS ────────────────────────────────────
        f['imc'] = imc
        f['imc_z'] = (imc - _TRAIN_STATS['imc']['mean']) / _TRAIN_STATS['imc']['std']
        
        peso_ideal = 24.9 * ((alt / 100) ** 2)
        f['excesso_peso_kg'] = peso - peso_ideal
        f['excesso_peso_pct'] = (f['excesso_peso_kg'] / peso_ideal) * 100 if peso_ideal > 0 else 0
        
        if imc >= 50:
            f['grau_obesidade_num'] = 3
        elif imc >= 40:
            f['grau_obesidade_num'] = 2
        else:
            f['grau_obesidade_num'] = 1
        
        # ─── 2. DEMOGRÁFICAS ──────────────────────────────────────
        f['idade'] = idade
        f['idade_z'] = (idade - _TRAIN_STATS['idade']['mean']) / _TRAIN_STATS['idade']['std']
        f['sexo_feminino'] = 1 if str(sexo).upper().startswith('F') else 0
        
        if idade <= 65:
            f['faixa_etaria_num'] = 1
        elif idade <= 70:
            f['faixa_etaria_num'] = 2
        elif idade <= 75:
            f['faixa_etaria_num'] = 3
        elif idade <= 80:
            f['faixa_etaria_num'] = 4
        else:
            f['faixa_etaria_num'] = 5
        
        # ─── 3. CLÍNICAS ─────────────────────────────────────────
        f['pa_sistolica'] = float(pa_sis) if pa_sis is not None else 130.0
        f['pa_diastolica'] = float(pa_dia) if pa_dia is not None else 80.0
        f['pa_pulso'] = f['pa_sistolica'] - f['pa_diastolica']
        f['pa_media'] = f['pa_diastolica'] + (f['pa_pulso'] / 3)
        
        # Categoria PA numérica
        if pa_sis is None:
            f['pa_categoria_num'] = -1
        elif f['pa_sistolica'] < 120:
            f['pa_categoria_num'] = 0
        elif f['pa_sistolica'] < 140:
            f['pa_categoria_num'] = 1
        elif f['pa_sistolica'] < 160:
            f['pa_categoria_num'] = 2
        else:
            f['pa_categoria_num'] = 3
        
        f['glicemia'] = float(glicemia) if glicemia is not None else 110.0
        
        # Categoria glicemia numérica
        if glicemia is None:
            f['glicemia_categoria_num'] = -1
        elif f['glicemia'] < 100:
            f['glicemia_categoria_num'] = 0
        elif f['glicemia'] < 126:
            f['glicemia_categoria_num'] = 1
        else:
            f['glicemia_categoria_num'] = 2
        
        # ─── 4. COMORBIDADES ─────────────────────────────────────
        f['total_comorbidades'] = int(paciente.get('total_comorbidades', 0) or 0)
        
        # Flags binárias
        comorb_keys = ['tem_diabetes', 'tem_hipertensao', 'tem_doenca_cardiaca',
                       'tem_dislipidemia', 'tem_irc', 'tem_depressao', 'tem_artrose']
        for k in comorb_keys:
            f[k] = int(bool(paciente.get(k, False)))
        
        # Score ponderado
        pesos = {'tem_diabetes': 2, 'tem_hipertensao': 1, 'tem_doenca_cardiaca': 3,
                 'tem_dislipidemia': 1, 'tem_irc': 3, 'tem_depressao': 1, 'tem_artrose': 1}
        f['score_comorbidades'] = sum(f[k] * p for k, p in pesos.items())
        
        f['n_condicoes_ativas'] = sum(f[k] for k in comorb_keys)
        f['multimorbidade'] = 1 if f['n_condicoes_ativas'] >= 3 else 0
        
        # ─── 5. COMPORTAMENTAIS ──────────────────────────────────
        f['dias_sem_visita'] = dias
        f['dias_sem_visita_log'] = math.log1p(dias)
        
        # ─── 6. INTERAÇÕES ───────────────────────────────────────
        f['imc_x_idade'] = imc * idade / 100
        f['imc_x_comorbidades'] = imc * f['score_comorbidades']
        f['idade_x_comorbidades'] = idade * f['score_comorbidades'] / 10
        f['imc_x_dias_sem_visita'] = imc * f['dias_sem_visita_log']
        
        return f
    
    def _classificar_nivel(self, score: int) -> str:
        """Classifica o nível de risco baseado no score"""
        if score >= 80:
            return 'Critico'
        elif score >= 60:
            return 'Alto'
        elif score >= 30:
            return 'Moderado'
        else:
            return 'Baixo'
    
    def _identificar_fatores(self, paciente: Dict) -> List[str]:
        """Identifica principais fatores de risco"""
        fatores = []
        
        imc = paciente.get('imc', 0) or paciente.get('imc_calculado', 0)
        
        if paciente.get('dias_sem_visita', 0) > 60:
            fatores.append('Atraso no acompanhamento')
        if imc >= 40:
            fatores.append('Obesidade Grau III')
        elif imc >= 50:
            fatores.append('Super Obesidade')
        if paciente.get('tem_diabetes'):
            fatores.append('Diabetes Mellitus')
        if paciente.get('tem_doenca_cardiaca'):
            fatores.append('Doença cardiovascular')
        if paciente.get('tem_irc'):
            fatores.append('Insuficiência renal crônica')
        if paciente.get('total_comorbidades', 0) >= 3:
            fatores.append('Multimorbidade (≥3 condições)')
        
        pa = paciente.get('pa_sistolica')
        if pa and pa >= 160:
            fatores.append('Hipertensão Estágio 2')
        
        glic = paciente.get('glicemia_mg_dl')
        if glic and glic >= 200:
            fatores.append('Glicemia muito elevada')
        
        idade = paciente.get('idade', 60)
        if idade >= 80:
            fatores.append(f'Idade avançada ({idade} anos)')
        
        return fatores
    
    def get_recomendacao(self, nivel_risco: str) -> str:
        """Retorna recomendação baseada no nível de risco"""
        recomendacoes = {
            'Critico': 'Visita domiciliar prioritária em 24-48h. Avaliar internação.',
            'Alto': 'Agendar consulta em 7 dias. Telemonitoramento diário.',
            'Moderado': 'Agendar retorno em 15 dias. Orientações por telefone.',
            'Baixo': 'Manter acompanhamento regular. Retorno em 30 dias.'
        }
        return recomendacoes.get(nivel_risco, 'Avaliar caso a caso.')


# Singleton para uso na API
_predictor_instance = None

def get_predictor() -> RiskPredictor:
    """Retorna instância singleton do preditor"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = RiskPredictor()
    return _predictor_instance


if __name__ == "__main__":
    # Teste com 3 perfis diferentes
    print("=" * 60)
    print("TESTE DO PREDITOR DE RISCO")
    print("=" * 60)
    
    casos = [
        {
            'nome': 'Baixo Risco',
            'dados': {
                'idade': 62, 'peso_kg': 90, 'altura_cm': 160,
                'imc': 35.2, 'glicemia_mg_dl': 95,
                'pa_sistolica': 125, 'pa_diastolica': 80,
                'total_comorbidades': 1, 'dias_sem_visita': 15,
                'tem_diabetes': False, 'tem_hipertensao': True,
                'tem_doenca_cardiaca': False, 'tem_dislipidemia': False,
                'tem_irc': False, 'tem_depressao': False, 'tem_artrose': False,
                'sexo': 'F'
            }
        },
        {
            'nome': 'Alto Risco',
            'dados': {
                'idade': 72, 'peso_kg': 105, 'altura_cm': 158,
                'imc': 42.1, 'glicemia_mg_dl': 180,
                'pa_sistolica': 165, 'pa_diastolica': 100,
                'total_comorbidades': 4, 'dias_sem_visita': 95,
                'tem_diabetes': True, 'tem_hipertensao': True,
                'tem_doenca_cardiaca': False, 'tem_dislipidemia': True,
                'tem_irc': False, 'tem_depressao': False, 'tem_artrose': True,
                'sexo': 'F'
            }
        },
        {
            'nome': 'Risco Crítico',
            'dados': {
                'idade': 81, 'peso_kg': 120, 'altura_cm': 155,
                'imc': 49.9, 'glicemia_mg_dl': 250,
                'pa_sistolica': 180, 'pa_diastolica': 110,
                'total_comorbidades': 6, 'dias_sem_visita': 200,
                'tem_diabetes': True, 'tem_hipertensao': True,
                'tem_doenca_cardiaca': True, 'tem_dislipidemia': True,
                'tem_irc': True, 'tem_depressao': False, 'tem_artrose': True,
                'sexo': 'M'
            }
        }
    ]
    
    predictor = RiskPredictor()
    
    for caso in casos:
        print(f"\n--- {caso['nome']} ---")
        resultado = predictor.calcular_risco(caso['dados'])
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print(f"Recomendação: {predictor.get_recomendacao(resultado['nivel_risco'])}")
