"""
Script de teste para verificar a conexão com o Supabase
e os dados do painel administrativo ODINENX
"""
import requests
import json
from datetime import datetime

# Configurações do Supabase
SUPABASE_URL = "https://mzamszcpbverpadjelck.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTA5NjIsImV4cCI6MjA4NTM2Njk2Mn0.I8uUlJxgm2UgyavzRA6ATcaoV3SRVd9Z-NgeENzzUN4"

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

def test_connection():
    """Testa a conexão básica com o Supabase"""
    print("=" * 60)
    print("🔍 TESTE DE CONEXÃO COM SUPABASE")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles?select=count",
            headers={**headers, "Prefer": "count=exact"},
            timeout=10
        )
        print(f"✅ Conexão OK - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def get_profiles():
    """Lista todos os perfis de usuários"""
    print("\n" + "=" * 60)
    print("👥 USUÁRIOS (profiles)")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles?select=*&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            profiles = response.json()
            print(f"📊 Total de usuários: {len(profiles)}")
            print("-" * 60)
            
            for p in profiles:
                print(f"  ID: {p.get('id', 'N/A')[:8]}...")
                print(f"  Email: {p.get('email', 'N/A')}")
                print(f"  Nome: {p.get('full_name', 'Não informado')}")
                print(f"  Criado: {p.get('created_at', 'N/A')}")
                print("-" * 40)
            
            return profiles
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def get_subscriptions():
    """Lista todas as assinaturas"""
    print("\n" + "=" * 60)
    print("💳 ASSINATURAS (subscriptions)")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/subscriptions?select=*&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            subs = response.json()
            print(f"📊 Total de assinaturas: {len(subs)}")
            
            active = len([s for s in subs if s.get('status') == 'active'])
            print(f"✅ Ativas: {active}")
            
            print("-" * 60)
            
            for s in subs:
                print(f"  ID: {s.get('id', 'N/A')[:8]}...")
                print(f"  User ID: {s.get('user_id', 'N/A')[:8]}...")
                print(f"  Status: {s.get('status', 'N/A')}")
                print(f"  Price ID: {s.get('price_id', 'N/A')}")
                print(f"  Validade: {s.get('current_period_end', 'N/A')}")
                print("-" * 40)
            
            return subs
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def calculate_stats(profiles, subscriptions):
    """Calcula estatísticas do painel admin"""
    print("\n" + "=" * 60)
    print("📈 ESTATÍSTICAS DO ADMIN")
    print("=" * 60)
    
    total_users = len(profiles)
    active_subs = len([s for s in subscriptions if s.get('status') == 'active'])
    free_users = total_users - active_subs
    revenue = active_subs * 79  # R$ 79 por assinante
    conversion = (active_subs / total_users * 100) if total_users > 0 else 0
    
    print(f"👥 Total de Usuários: {total_users}")
    print(f"💳 Assinantes Ativos: {active_subs}")
    print(f"🆓 Usuários Free: {free_users}")
    print(f"💰 Receita Mensal: R$ {revenue:.2f}")
    print(f"📊 Taxa de Conversão: {conversion:.1f}%")
    print(f"💵 Receita Anual (projeção): R$ {revenue * 12:.2f}")

def test_admin_operations():
    """Testa operações que o admin pode fazer"""
    print("\n" + "=" * 60)
    print("🛡️ TESTE DE OPERAÇÕES ADMIN")
    print("=" * 60)
    
    # Teste 1: Listar usuários
    print("\n[1] Listar usuários: ", end="")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles?select=*&limit=5",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ OK")
        else:
            print(f"❌ Erro {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")
    
    # Teste 2: Listar assinaturas
    print("[2] Listar assinaturas: ", end="")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/subscriptions?select=*&limit=5",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ OK")
        else:
            print(f"❌ Erro {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")
    
    # Teste 3: Verificar estrutura da tabela profiles
    print("[3] Estrutura profiles: ", end="")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles?select=*&limit=1",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                campos = list(data[0].keys())
                print(f"✅ Campos: {', '.join(campos)}")
            else:
                print("✅ (tabela vazia)")
        else:
            print(f"❌ Erro {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")

def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " ODINENX - TESTE DO PAINEL ADMINISTRATIVO ".center(58) + "║")
    print("║" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Teste de conexão
    if not test_connection():
        print("\n❌ Falha na conexão. Verifique as credenciais.")
        return
    
    # Carregar dados
    profiles = get_profiles()
    subscriptions = get_subscriptions()
    
    # Calcular estatísticas
    calculate_stats(profiles, subscriptions)
    
    # Testes de operação
    test_admin_operations()
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 60)
    print("\n🌐 Acesse o painel admin em: https://odinenx.vercel.app/admin")
    print("📧 Login com: kevynhoooz@gmail.com")

if __name__ == "__main__":
    main()
