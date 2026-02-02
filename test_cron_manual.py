#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 SCRIPT DE TESTE MANUAL - CRON TRIAL CHECK
Execute para testar a verificação de trials manualmente
"""

import requests
import json
from datetime import datetime

# Configurações
SUPABASE_URL = "https://mzamszcpbverpadjelck.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ1NDM4MjQsImV4cCI6MjA1MDExOTgyNH0.TJYeR1rBmjxMEe5rjGMojsEtX2z_1oK4lR8QcbK3o8g"

def test_cron_execution():
    print("🕐 TESTE MANUAL DO CRON - VERIFICAÇÃO DE TRIALS")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # URL da Edge Function
    edge_function_url = f"{SUPABASE_URL}/functions/v1/check-trial"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Executando verificação de trials...")
        print(f"📡 URL: {edge_function_url}")
        
        # Fazer chamada para Edge Function
        response = requests.post(
            edge_function_url,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCESSO! Edge Function executada")
            
            try:
                result = response.json()
                print("\n📈 RESULTADO:")
                print(f"   • Total usuários: {result.get('stats', {}).get('totalUsers', 'N/A')}")
                print(f"   • Trials ativos: {result.get('stats', {}).get('activeTrials', 'N/A')}")
                print(f"   • Trials expirados: {result.get('stats', {}).get('expiredUsers', 'N/A')}")
                print(f"   • Mensagem: {result.get('message', 'N/A')}")
                
            except json.JSONDecodeError:
                print("📄 Resposta (texto):")
                print(response.text[:500])
                
        else:
            print(f"❌ ERRO! Status: {response.status_code}")
            print(f"📄 Resposta: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT! Edge Function demorou mais de 30 segundos")
    except requests.exceptions.ConnectionError:
        print("🔌 ERRO DE CONEXÃO! Verifique sua internet")
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📋 COMO CONFIGURAR CRON AUTOMÁTICO:")
    print()
    print("1️⃣ GITHUB ACTIONS (Recomendado):")
    print("   • Arquivo já criado: .github/workflows/check-trials.yml")
    print("   • Executa automaticamente todo dia às 00:00 UTC")
    print("   • Gratuito no GitHub")
    print()
    print("2️⃣ CRON-JOB.ORG:")
    print(f"   • URL: {edge_function_url}")
    print("   • Method: POST")
    print(f"   • Header: Authorization: Bearer {SUPABASE_KEY}")
    print("   • Schedule: 0 0 * * * (diário)")
    print()
    print("3️⃣ SUPABASE PG_CRON:")
    print("   • Execute: 008_cron_job_setup.sql no Supabase SQL Editor")
    print("   • Funciona apenas em planos pagos")
    print()
    print("🌐 Supabase Dashboard:")
    print("   https://supabase.com/dashboard/project/mzamszcpbverpadjelck")

def test_sql_function():
    """Testar a função SQL diretamente"""
    print("\n🗄️ TESTE DA FUNÇÃO SQL:")
    print("=" * 40)
    
    # Testar via Supabase REST API
    sql_url = f"{SUPABASE_URL}/rest/v1/rpc/check_trial_expiration"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    try:
        response = requests.post(sql_url, headers=headers, json={})
        
        if response.status_code == 200:
            print("✅ Função SQL executada com sucesso")
        else:
            print(f"⚠️ Função SQL - Status: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao testar função SQL: {str(e)}")

if __name__ == "__main__":
    test_cron_execution()
    test_sql_function()