#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 TESTE WEBHOOK CRON - Versão Simplificada
"""

import requests
import json
from datetime import datetime

SUPABASE_URL = "https://mzamszcpbverpadjelck.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ1NDM4MjQsImV4cCI6MjA1MDExOTgyNH0.TJYeR1rBmjxMEe5rjGMojsEtX2z_1oK4lR8QcbK3o8g"

def test_webhook_cron():
    print("🌐 TESTE WEBHOOK CRON - VERIFICAÇÃO DE TRIALS")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # URL da função SQL via REST API
    webhook_url = f"{SUPABASE_URL}/rest/v1/rpc/daily_trial_check"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY
    }
    
    try:
        print("🚀 Executando verificação via webhook...")
        print(f"📡 URL: {webhook_url}")
        
        response = requests.post(webhook_url, headers=headers, json={})
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCESSO! Webhook executado")
            
            try:
                result = response.json()
                print("\n📈 RESULTADO:")
                print(f"   • Sucesso: {result.get('success', 'N/A')}")
                print(f"   • Mensagem: {result.get('message', 'N/A')}")
                print(f"   • Timestamp: {result.get('timestamp', 'N/A')}")
                
                stats = result.get('stats', {})
                print(f"   • Total usuários: {stats.get('totalUsers', 'N/A')}")
                print(f"   • Trials ativos: {stats.get('activeTrials', 'N/A')}")
                print(f"   • Trials expirados: {stats.get('expiredUsers', 'N/A')}")
                
            except json.JSONDecodeError:
                print("📄 Resposta (texto):")
                print(response.text[:500])
                
        else:
            print(f"❌ ERRO! Status: {response.status_code}")
            print(f"📄 Resposta: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔧 CONFIGURAÇÃO DO CRON WEBHOOK:")
    print()
    print("1️⃣ Execute primeiro: 009_webhook_cron.sql no Supabase")
    print("2️⃣ Configure webhook em cron-job.org:")
    print(f"   • URL: {webhook_url}")
    print("   • Method: POST")
    print(f"   • Header: apikey: {SUPABASE_KEY}")
    print("   • Schedule: 0 0 * * *")
    print()
    print("3️⃣ Ou use o GitHub Actions que já está configurado!")

if __name__ == "__main__":
    test_webhook_cron()