#!/usr/bin/env python
"""
Script de teste para verificar se a aplicação Flask está configurada corretamente.
Uso: python test_flask_app.py
"""

import sys
from pathlib import Path

# Adiciona o projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Testa se as importações estão funcionando."""
    print("✓ Testando importações...")
    try:
        from flask import Flask, render_template, jsonify
        print("  ✅ Flask importado com sucesso")
    except ImportError as e:
        print(f"  ❌ Erro ao importar Flask: {e}")
        return False
    
    try:
        import requests
        print("  ✅ Requests importado com sucesso")
    except ImportError as e:
        print(f"  ❌ Erro ao importar requests: {e}")
        return False
    
    return True

def test_app_creation():
    """Testa se a app Flask pode ser criada."""
    print("\n✓ Testando criação da app Flask...")
    try:
        from src.app.app import create_app
        app = create_app()
        print("  ✅ App criada com sucesso")
        
        # Verifica se os arquivos estão nos lugares certos
        templates = Path("src/app/templates/index.html")
        js = Path("src/app/static/js/app.js")
        
        if templates.exists():
            print(f"  ✅ Template encontrado: {templates}")
        else:
            print(f"  ❌ Template não encontrado: {templates}")
            return False
        
        if js.exists():
            print(f"  ✅ JavaScript encontrado: {js}")
        else:
            print(f"  ❌ JavaScript não encontrado: {js}")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao criar app: {e}")
        return False

def test_routes():
    """Testa se as rotas estão registradas."""
    print("\n✓ Testando rotas...")
    try:
        from src.app.app import create_app
        app = create_app()
        
        routes = [
            "/",
            "/dashboard",
            "/pacientes",
            "/mapa",
            "/relatorios",
            "/configuracoes",
            "/health",
            "/api/v1/kpis",
            "/api/v1/pacientes",
            "/api/v1/distribuicao/grau",
            "/api/v1/distribuicao/risco",
        ]
        
        registered_routes = {rule.rule for rule in app.url_map.iter_rules()}
        
        for route in routes:
            if route in registered_routes or any(route in str(r) for r in registered_routes):
                print(f"  ✅ Rota registrada: {route}")
            else:
                print(f"  ⚠️  Rota não encontrada: {route}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao testar rotas: {e}")
        return False

def test_client_requests():
    """Testa requisições com o cliente de teste Flask."""
    print("\n✓ Testando requisições HTTP...")
    try:
        from src.app.app import create_app
        app = create_app()
        client = app.test_client()
        
        # Testa GET /
        response = client.get("/")
        if response.status_code == 200:
            print(f"  ✅ GET / retornou 200")
        else:
            print(f"  ❌ GET / retornou {response.status_code}")
        
        # Testa GET /health
        response = client.get("/health")
        if response.status_code == 200:
            print(f"  ✅ GET /health retornou 200")
            print(f"     Resposta: {response.get_json()}")
        else:
            print(f"  ❌ GET /health retornou {response.status_code}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao testar requisições: {e}")
        return False

def main():
    print("=" * 60)
    print("TESTE DA APLICAÇÃO FLASK - SAD Dashboard")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("App Creation", test_app_creation),
        ("Routes", test_routes),
        ("Client Requests", test_client_requests),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erro fatal em {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("\nPróximas etapas:")
        print("1. Iniciar a API backend: python src/backend/api/app.py")
        print("2. Iniciar o frontend: python src/app/app.py")
        print("3. Acessar: http://localhost:5000")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("\nVerifique os erros acima e corrija os problemas.")
    print("=" * 60)

if __name__ == "__main__":
    main()
