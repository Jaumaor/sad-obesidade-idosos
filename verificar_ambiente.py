"""
Script de Verificação do Ambiente
Verifica se todas as dependências e configurações estão corretas
"""

import sys
from pathlib import Path


def check_python_version():
    """Verifica a versão do Python"""
    print("\nPython:")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"  [OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"  [ERRO] Python {version.major}.{version.minor}.{version.micro}")
        print("     Versão mínima requerida: Python 3.10")
        return False


def check_libraries():
    """Verifica bibliotecas essenciais"""
    print("\nBibliotecas:")

    libraries = {
        'pandas': 'Manipulação de dados',
        'numpy': 'Computação numérica',
        'sklearn': 'Machine Learning',
        'geopandas': 'Análise geoespacial',
        'streamlit': 'Dashboard interativo',
        'psycopg2': 'Conexão PostgreSQL',
        'sqlalchemy': 'ORM',
        'matplotlib': 'Visualização',
        'plotly': 'Gráficos interativos'
    }

    all_ok = True

    for lib, desc in libraries.items():
        try:
            __import__(lib)
            print(f"  [OK] {lib:<15} - {desc}")
        except ImportError:
            print(f"  [ERRO] {lib:<15} - {desc} (NÃO INSTALADO)")
            all_ok = False

    return all_ok


def check_env_file():
    """Verifica se o arquivo .env existe"""
    print("\nArquivos de Configuração:")

    env_path = Path(__file__).resolve().parent / '.env'

    if env_path.exists():
        print(f"  [OK] Arquivo .env encontrado")
        return True
    else:
        print(f"  [ERRO] Arquivo .env NÃO encontrado")
        print(f"     Copie .env.example para .env e configure as variáveis")
        return False


def check_database_connection():
    """Verifica conexão com o banco de dados"""
    print("\nBanco de Dados:")

    try:
        sys.path.append(str(Path(__file__).resolve().parent))
        from src.database.connection import DatabaseConnection

        db = DatabaseConnection()
        db.connect_psycopg2()

        info = db.test_connection()

        print(f"  [OK] Conexão bem-sucedida!")
        print(f"     PostgreSQL: {info['postgres_version'].split(',')[0]}")
        print(f"     PostGIS: {info['postgis_version']}")
        print(f"     Tabelas: {info['total_tables']}")

        db.close()
        return True

    except ImportError as e:
        print(f"  [ERRO] Erro ao importar módulo: {e}")
        return False
    except Exception as e:
        print(f"  [ERRO] Erro na conexão: {e}")
        print(f"     Verifique se o PostgreSQL está rodando")
        print(f"     Verifique as credenciais no arquivo .env")
        return False


def check_directories():
    """Verifica estrutura de diretórios"""
    print("\nEstrutura de Diretórios:")

    base_dir = Path(__file__).resolve().parent

    required_dirs = [
        'data/raw',
        'data/processed',
        'data/geojson',
        'src/database',
        'src/models',
        'src/app',
        'notebooks'
    ]

    all_ok = True

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [ERRO] {dir_path} (AUSENTE)")
            all_ok = False

    return all_ok


def check_postgresql_available():
    """Verifica se o PostgreSQL está instalado"""
    print("\nPostgreSQL:")

    import subprocess

    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  [OK] {version}")
            return True
        else:
            print(f"  [ERRO] PostgreSQL não encontrado")
            return False

    except FileNotFoundError:
        print(f"  [ERRO] PostgreSQL não encontrado no PATH")
        print(f"     Instale o PostgreSQL: https://www.postgresql.org/download/")
        return False
    except Exception as e:
        print(f"  [AVISO] Erro ao verificar PostgreSQL: {e}")
        return False


def main():
    """Executa todas as verificações"""
    print("=" * 70)
    print("SAD - Verificação do Ambiente de Desenvolvimento")
    print("=" * 70)

    checks = {
        'Python': check_python_version(),
        'Bibliotecas': check_libraries(),
        'PostgreSQL': check_postgresql_available(),
        'Arquivo .env': check_env_file(),
        'Diretórios': check_directories(),
        'Banco de Dados': check_database_connection()
    }

    print("\n" + "=" * 70)
    print("RESUMO DA VERIFICAÇÃO")
    print("=" * 70)

    total = len(checks)
    passed = sum(checks.values())

    for check, status in checks.items():
        icon = "[OK]" if status else "[ERRO]"
        print(f"{icon} {check}")

    print("\n" + "=" * 70)

    if passed == total:
        print("SUCESSO! Ambiente configurado com sucesso!")
        print("\nPróximos passos:")
        print("   1. Inserir dados de teste:")
        print("      python src/database/insert_test_data.py")
        print("\n   2. Executar o dashboard:")
        print("      streamlit run src/app/app.py")
    else:
        print(f"ATENCAO: {total - passed} problema(s) encontrado(s)")
        print("\nConsulte o arquivo GUIA_INICIO.md para instruções detalhadas")

    print("=" * 70)


if __name__ == "__main__":
    main()
