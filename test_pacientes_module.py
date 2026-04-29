#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar os endpoints do modulo de pacientes.
Versao compatible com Windows
"""

import requests
import json
from pprint import pprint
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_busca_pacientes():
    """Testa busca com filtros"""
    print_section("[1] Buscar Pacientes")
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/buscar?limite=5")
        response.raise_for_status()
        data = response.json()
        
        print(f"[OK] Status: {response.status_code}")
        print(f"[INFO] Pacientes retornados: {len(data)}")
        
        if data:
            paciente_exemplo = data[0]
            print(f"\nExemplo de paciente:")
            pprint(paciente_exemplo)
            return paciente_exemplo.get('id')
        else:
            print("[AVISO] Nenhum paciente encontrado no banco")
            return None
            
    except Exception as e:
        print(f"[ERRO] {e}")
        return None

def test_detalhes_paciente(paciente_id):
    """Testa obtencao de detalhes de um paciente"""
    print_section("[2] Detalhes do Paciente")
    
    if not paciente_id:
        print("[AVISO] ID do paciente nao disponivel")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/{paciente_id}")
        response.raise_for_status()
        data = response.json()
        
        print(f"[OK] Status: {response.status_code}")
        print(f"Nome: {data.get('codigo_anonimo')}")
        print(f"Idade: {data.get('idade')} anos")
        print(f"IMC: {data.get('imc_atual')}")
        print(f"Risco: {data.get('nivel_risco')} (score: {data.get('score_risco')})")
        print(f"Territorio: {data.get('territorio')}")
        print(f"Unidade: {data.get('unidade_saude')}")
        print(f"Comorbidades: {data.get('total_comorbidades')}")
        print(f"Alertas pendentes: {data.get('total_alertas_pendentes')}")
        
    except Exception as e:
        print(f"[ERRO] {e}")

def test_acompanhamentos(paciente_id):
    """Testa historico de acompanhamentos"""
    print_section("[3] Historico de Acompanhamentos (Visitas)")
    
    if not paciente_id:
        print("[AVISO] ID do paciente nao disponivel")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/{paciente_id}/acompanhamentos?limite=5")
        response.raise_for_status()
        data = response.json()
        
        print(f"[OK] Status: {response.status_code}")
        print(f"Total de registros: {len(data)}\n")
        
        for i, acomp in enumerate(data, 1):
            print(f"Visita {i}:")
            print(f"  Data: {acomp.get('data_registro')}")
            print(f"  Tipo: {acomp.get('tipo_atendimento')}")
            print(f"  IMC: {acomp.get('imc')}")
            print(f"  Peso: {acomp.get('peso_kg')}kg | Altura: {acomp.get('altura_m')}m")
            print(f"  Obs: {acomp.get('observacoes', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"[ERRO] {e}")

def test_comorbidades(paciente_id):
    """Testa comorbidades do paciente"""
    print_section("[4] Condicoes Cronicas (Comorbidades)")
    
    if not paciente_id:
        print("[AVISO] ID do paciente nao disponivel")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/{paciente_id}/comorbidades")
        response.raise_for_status()
        data = response.json()
        
        print(f"[OK] Status: {response.status_code}")
        print(f"Total de condicoes: {len(data)}\n")
        
        if data:
            for comorbidade in data:
                status = "ATIVA" if comorbidade.get('ativo') else "INATIVA"
                print(f"* {comorbidade.get('condicao')} [{status}]")
                if comorbidade.get('descricao_adicional'):
                    print(f"  Detalhes: {comorbidade.get('descricao_adicional')}")
        else:
            print("Nenhuma comorbidade registrada")
            
    except Exception as e:
        print(f"[ERRO] {e}")

def test_alertas(paciente_id):
    """Testa alertas do paciente"""
    print_section("[5] Alertas Gerados")
    
    if not paciente_id:
        print("[AVISO] ID do paciente nao disponivel")
        return
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/{paciente_id}/alertas?limite=10")
        response.raise_for_status()
        data = response.json()
        
        print(f"[OK] Status: {response.status_code}")
        print(f"Total de alertas: {len(data)}\n")
        
        if data:
            for alerta in data:
                status = "RESOLVIDO" if alerta.get('resolvido') else "PENDENTE"
                print(f"[{alerta.get('tipo_alerta')}] [{status}]")
                print(f"  Prioridade: {alerta.get('prioridade')}")
                print(f"  Titulo: {alerta.get('titulo')}")
                print(f"  Gerado ha: {alerta.get('dias_alerta')} dias")
                print()
        else:
            print("Nenhum alerta registrado")
            
    except Exception as e:
        print(f"[ERRO] {e}")

def test_status_modulo():
    """Testa status do modulo"""
    print_section("[6] Status do Modulo de Pacientes")
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/modulo-status")
        response.raise_for_status()
        data = response.json()
        
        print(f"[OK] Status HTTP: {response.status_code}")
        print(f"Modulo: {data.get('modulo')}")
        print(f"Status: {data.get('status')}")
        print(f"Mensagem: {data.get('mensagem')}")
        
    except Exception as e:
        print(f"[ERRO] {e}")

def main():
    print("""
================================================================================
    TESTE DO MODULO DE PACIENTES - API SAD
    Endpoints Funcionais
================================================================================
    """)
    
    paciente_id = test_busca_pacientes()
    
    if paciente_id:
        test_detalhes_paciente(paciente_id)
        test_acompanhamentos(paciente_id)
        test_comorbidades(paciente_id)
        test_alertas(paciente_id)
    
    test_status_modulo()
    
    print_section("TESTES CONCLUIDOS")
    print("""
Documentacao dos Endpoints:
  GET  /pacientes/buscar                    - Buscar com filtros
  GET  /pacientes/<id>                      - Detalhes completos
  GET  /pacientes/<id>/acompanhamentos      - Historico de visitas
  GET  /pacientes/<id>/comorbidades         - Condicoes cronicas
  GET  /pacientes/<id>/alertas              - Alertas gerados
  GET  /pacientes/modulo-status             - Status do modulo
  GET  /docs                                - Swagger/OpenAPI

Acesse: http://localhost:8000/docs
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nErro fatal: {e}")
        sys.exit(1)

