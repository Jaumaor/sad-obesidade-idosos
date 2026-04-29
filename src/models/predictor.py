"""
Módulo de Predição de Risco para o SAD
Usado pela API para calcular scores em produção
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RiskPredictor:
    """
    Preditor de risco de abandono/complicações para idosos obesos
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
            # Fallback: usar regras apenas
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
        
        # Preparar features no formato esperado
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
            X_scaled = X.values
        
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
            'probabilidade_abandono': round(score, 4),
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
        imc = paciente.get('imc_calculado', 0)
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
        """Extrai features do dicionário do paciente"""
        features = {}
        
        # Features numéricas base
        features['idade'] = paciente.get('idade', 60)
        features['nu_peso'] = paciente.get('peso_kg', 80)
        features['nu_altura'] = paciente.get('altura_m', 1.65) * 100  # cm
        features['imc_calculado'] = paciente.get('imc', 35)
        features['excesso_peso_kg'] = features['nu_peso'] - (24.9 * ((features['nu_altura']/100) ** 2))
        features['nu_glicemia'] = paciente.get('glicemia_mg_dl', 100)
        features['nu_pressao_arterial_maxima'] = paciente.get('pa_sistolica', 120)
        features['nu_pressao_arterial_minima'] = paciente.get('pa_diastolica', 80)
        features['total_comorbidades'] = paciente.get('total_comorbidades', 0)
        features['dias_sem_visita'] = paciente.get('dias_sem_visita', 0)
        
        # Score comorbidades (simplificado)
        score_comorb = 0
        if paciente.get('tem_diabetes'):
            score_comorb += 2
        if paciente.get('tem_hipertensao'):
            score_comorb += 1
        if paciente.get('tem_doenca_cardiaca'):
            score_comorb += 3
        if paciente.get('tem_dislipidemia'):
            score_comorb += 1
        if paciente.get('tem_irc'):
            score_comorb += 3
        features['score_comorbidades'] = score_comorb
        
        # Features booleanas
        features['tem_diabetes'] = int(paciente.get('tem_diabetes', False))
        features['tem_hipertensao'] = int(paciente.get('tem_hipertensao', False))
        features['tem_doenca_cardiaca'] = int(paciente.get('tem_doenca_cardiaca', False))
        features['tem_dislipidemia'] = int(paciente.get('tem_dislipidemia', False))
        features['tem_irc'] = int(paciente.get('tem_irc', False))
        
        # Features categóricas (dummies)
        # Faixa etária
        idade = features['idade']
        faixas = ['60-65', '66-70', '71-75', '76-80', '80+']
        for faixa in faixas:
            features[f'faixa_etaria_{faixa}'] = 0
        if idade <= 65:
            features['faixa_etaria_60-65'] = 1
        elif idade <= 70:
            features['faixa_etaria_66-70'] = 1
        elif idade <= 75:
            features['faixa_etaria_71-75'] = 1
        elif idade <= 80:
            features['faixa_etaria_76-80'] = 1
        else:
            features['faixa_etaria_80+'] = 1
        
        # Grau obesidade
        imc = features['imc_calculado']
        features['grau_obesidade_Grau II'] = 1 if 35 <= imc < 40 else 0
        features['grau_obesidade_Grau III'] = 1 if imc >= 40 else 0
        
        # Categorias clínicas
        pa = features['nu_pressao_arterial_maxima']
        for cat in ['Elevada', 'Hipertensao_1', 'Hipertensao_2']:
            features[f'categoria_pa_{cat}'] = 0
        if 120 <= pa < 140:
            features['categoria_pa_Elevada'] = 1
        elif 140 <= pa < 160:
            features['categoria_pa_Hipertensao_1'] = 1
        elif pa >= 160:
            features['categoria_pa_Hipertensao_2'] = 1
        
        glicemia = features['nu_glicemia']
        for cat in ['Pre_diabetes', 'Diabetes']:
            features[f'categoria_glicemia_{cat}'] = 0
        if 100 <= glicemia < 126:
            features['categoria_glicemia_Pre_diabetes'] = 1
        elif glicemia >= 126:
            features['categoria_glicemia_Diabetes'] = 1
        
        # Risco abandono
        dias = features['dias_sem_visita']
        for cat in ['Medio', 'Alto']:
            features[f'risco_abandono_{cat}'] = 0
        if dias > 60:
            features['risco_abandono_Alto'] = 1
        elif dias > 45:
            features['risco_abandono_Medio'] = 1
        
        return features
    
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
        
        if paciente.get('dias_sem_visita', 0) > 60:
            fatores.append('Atraso no acompanhamento')
        if paciente.get('imc', 0) >= 40:
            fatores.append('Obesidade Grau III')
        if paciente.get('tem_diabetes') and paciente.get('tem_doenca_cardiaca'):
            fatores.append('Diabetes + Doença cardíaca')
        if paciente.get('total_comorbidades', 0) >= 3:
            fatores.append('Múltiplas comorbidades')
        
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
    # Teste
    print("Testando predictor...")
    
    # Criar paciente de teste
    paciente_teste = {
        'idade': 72,
        'peso_kg': 95,
        'altura_m': 1.60,
        'imc': 37.1,
        'glicemia_mg_dl': 180,
        'pa_sistolica': 160,
        'pa_diastolica': 95,
        'total_comorbidades': 3,
        'dias_sem_visita': 75,
        'tem_diabetes': True,
        'tem_hipertensao': True,
        'tem_doenca_cardiaca': False,
        'tem_dislipidemia': True,
        'tem_irc': False
    }
    
    predictor = RiskPredictor()
    resultado = predictor.calcular_risco(paciente_teste)
    
    print("\nResultado:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\nRecomendação: {predictor.get_recomendacao(resultado['nivel_risco'])}")
