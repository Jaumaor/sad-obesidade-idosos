# ============================================================================
# SAD - Configurações do Sistema
# ============================================================================

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ===== DIRETÓRIOS DO PROJETO =====
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GEOJSON_DIR = DATA_DIR / "geojson"
MODELS_DIR = BASE_DIR / "src" / "models"

# Criar diretórios se não existirem
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, GEOJSON_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ===== BANCO DE DADOS =====


class DatabaseConfig:
    """Configurações do PostgreSQL/PostGIS"""

    HOST = os.getenv("DB_HOST", "localhost")
    PORT = os.getenv("DB_PORT", "5432")
    DATABASE = os.getenv("DB_NAME", "sad_obesidade")
    USER = os.getenv("DB_USER", "postgres")
    PASSWORD = os.getenv("DB_PASSWORD", "")

    # String de conexão SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    )

    # String de conexão psycopg2
    @classmethod
    def get_connection_string(cls):
        return (
            f"host={cls.HOST} "
            f"port={cls.PORT} "
            f"dbname={cls.DATABASE} "
            f"user={cls.USER} "
            f"password={cls.PASSWORD}"
        )

# ===== MODELO DE MACHINE LEARNING =====


class ModelConfig:
    """Configurações do modelo preditivo"""

    # Caminho do modelo treinado
    MODEL_PATH = MODELS_DIR / "risk_model.pkl"
    MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

    # Hiperparâmetros (podem ser ajustados)
    RANDOM_STATE = 42
    TEST_SIZE = 0.2

    # Features utilizadas no modelo
    FEATURES = [
        'idade',
        'imc',
        'dias_sem_visita',
        'total_comorbidades',
        'pressao_arterial_sistolica',
        'pressao_arterial_diastolica',
        'glicemia_mg_dl'
    ]

    # Thresholds de risco (score 0-100)
    RISK_THRESHOLDS = {
        'Baixo': (0, 30),
        'Moderado': (30, 60),
        'Alto': (60, 80),
        'Crítico': (80, 100)
    }

# ===== CRITÉRIOS CLÍNICOS =====


class ClinicalConfig:
    """Parâmetros clínicos e critérios de risco"""

    # Idade mínima para inclusão
    IDADE_MINIMA = 60

    # Classificação de obesidade por IMC
    IMC_OBESIDADE_GRAU_2 = 35.0
    IMC_OBESIDADE_GRAU_3 = 40.0

    # Critério de abandono (dias sem visita)
    DIAS_ABANDONO = 60
    DIAS_RISCO_ABANDONO = 45

    # Valores de referência (pressão arterial)
    PA_SISTOLICA_NORMAL_MAX = 120
    PA_DIASTOLICA_NORMAL_MAX = 80
    PA_HIPERTENSAO_ESTAGIO_1 = 140
    PA_HIPERTENSAO_ESTAGIO_2 = 160

    # Glicemia de jejum (mg/dL)
    GLICEMIA_NORMAL_MAX = 100
    GLICEMIA_PRE_DIABETES = 125
    GLICEMIA_DIABETES = 126

# ===== GEORREFERENCIAMENTO =====


class GeoConfig:
    """Configurações de geolocalização"""

    # SRID (Sistema de Referência de Coordenadas)
    SRID = 4326  # WGS84 (padrão GPS)

    # Coordenadas aproximadas de Vitória da Conquista - BA
    VITORIA_DA_CONQUISTA_LAT = -14.8615
    VITORIA_DA_CONQUISTA_LNG = -40.8442

    # Raio de aproximação para privacidade (metros)
    # Coordenadas de pacientes serão "arredondadas" para proteger identidade
    PRIVACY_RADIUS_METERS = 200

    # Estilo do mapa (Folium)
    MAP_TILES = "OpenStreetMap"  # Opções: "CartoDB positron", "Stamen Terrain"
    MAP_ZOOM_START = 13

# ===== DASHBOARD (STREAMLIT) =====


class DashboardConfig:
    """Configurações da interface web"""

    # Título da aplicação
    APP_TITLE = "SAD - Monitoramento de Idosos com Obesidade"
    PAGE_ICON = ""
    LAYOUT = "wide"

    # Tema de cores (baseado no SUS)
    COLOR_PALETTE = {
        'primary': '#009639',  # Verde SUS
        'secondary': '#0066CC',
        'risk_low': '#4CAF50',
        'risk_moderate': '#FFC107',
        'risk_high': '#FF9800',
        'risk_critical': '#F44336'
    }

    # Número de linhas a exibir por padrão em tabelas
    DEFAULT_TABLE_ROWS = 20

    # Atualização automática (em segundos, 0 = desabilitado)
    AUTO_REFRESH_SECONDS = 0

# ===== SEGURANÇA E PRIVACIDADE =====


class SecurityConfig:
    """Configurações de segurança (LGPD)"""

    # Habilitar logs de auditoria
    ENABLE_AUDIT_LOG = True

    # Algoritmo de hash para anonimização
    HASH_ALGORITHM = "sha256"

    # Campos sensíveis que nunca devem ser exibidos
    SENSITIVE_FIELDS = [
        'cpf', 'cns', 'nome_completo', 'endereco_completo',
        'telefone', 'email'
    ]

    # Tempo de retenção de dados (em meses)
    DATA_RETENTION_MONTHS = 36

# ===== AMBIENTE =====


class Environment:
    """Identificação do ambiente de execução"""

    MODE = os.getenv("ENVIRONMENT", "development")
    DEBUG = MODE == "development"

    @classmethod
    def is_production(cls):
        return cls.MODE == "production"

    @classmethod
    def is_development(cls):
        return cls.MODE == "development"


# ===== LOGGING =====

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'WARNING',
            'formatter': 'standard',
            'filename': BASE_DIR / 'app.log',
            'mode': 'a'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}

# Configurar logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# ===== VALIDAÇÃO DE CONFIGURAÇÕES =====


def validate_config():
    """Valida se as configurações essenciais estão presentes"""

    errors = []

    # Verificar conexão com banco de dados
    if not DatabaseConfig.PASSWORD:
        errors.append("[ERRO] DB_PASSWORD não configurado no arquivo .env")

    # Verificar diretórios
    if not DATA_DIR.exists():
        errors.append(f"[ERRO] Diretório de dados não encontrado: {DATA_DIR}")

    if errors:
        logger.error("Erros de configuração encontrados:")
        for error in errors:
            logger.error(error)
        return False

    logger.info("[OK] Configurações validadas com sucesso")
    return True


if __name__ == "__main__":
    # Testar configurações
    print("=" * 60)
    print("SAD - Configurações do Sistema")
    print("=" * 60)
    print(f"Ambiente: {Environment.MODE}")
    print(f"Base Dir: {BASE_DIR}")
    print(f"Banco de Dados: {DatabaseConfig.DATABASE}")
    print(f"Host: {DatabaseConfig.HOST}:{DatabaseConfig.PORT}")
    print(f"Modelo: {ModelConfig.MODEL_VERSION}")
    print("=" * 60)
    validate_config()
