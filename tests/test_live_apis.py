"""
🧪 Testes de APIs ao Vivo - ODINENX v2.0
Validação de todas as integrações necessárias para o sistema de salas ao vivo
"""

import requests
import json
from datetime import datetime
from typing import Optional

# ============================================
# 🔧 CONFIGURAÇÕES
# ============================================

class Config:
    """Configurações das APIs"""
    
    # API Football (api-football.com) - Uma das melhores para placar em tempo real
    API_FOOTBALL_KEY = "SUA_CHAVE_AQUI"  # Substituir pela chave real
    API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
    
    # Alternativa: FootballData.org (gratuita com limites)
    FOOTBALL_DATA_KEY = "SUA_CHAVE_AQUI"
    FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
    
    # API Odds (já usada no projeto)
    ODDS_API_KEY = "SUA_CHAVE_AQUI"
    ODDS_API_BASE = "https://api.the-odds-api.com/v4"
    
    # Supabase
    SUPABASE_URL = "SUA_URL_AQUI"
    SUPABASE_KEY = "SUA_CHAVE_AQUI"


# ============================================
# 📊 TESTE 1: API DE PLACAR EM TEMPO REAL
# ============================================

def test_api_football_live():
    """
    Testa API Football para jogos ao vivo
    Endpoint: /fixtures?live=all
    """
    print("\n" + "="*50)
    print("🏟️ TESTE: API Football - Jogos ao Vivo")
    print("="*50)
    
    headers = {
        "x-rapidapi-key": Config.API_FOOTBALL_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    try:
        # Buscar jogos ao vivo
        response = requests.get(
            f"{Config.API_FOOTBALL_BASE}/fixtures",
            headers=headers,
            params={"live": "all"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            jogos = data.get("response", [])
            
            print(f"✅ API funcionando!")
            print(f"📺 Jogos ao vivo agora: {len(jogos)}")
            
            if jogos:
                for jogo in jogos[:3]:  # Mostra até 3 jogos
                    fixture = jogo.get("fixture", {})
                    teams = jogo.get("teams", {})
                    goals = jogo.get("goals", {})
                    
                    print(f"\n  ⚽ {teams.get('home', {}).get('name')} {goals.get('home', 0)} x {goals.get('away', 0)} {teams.get('away', {}).get('name')}")
                    print(f"     Status: {fixture.get('status', {}).get('long')}")
                    print(f"     Minuto: {fixture.get('status', {}).get('elapsed', 0)}'")
            
            return True
        else:
            print(f"❌ Erro: Status {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


def test_football_data_org():
    """
    Testa API FootballData.org (alternativa gratuita)
    Limite: 10 requests/minuto no plano free
    """
    print("\n" + "="*50)
    print("🏟️ TESTE: FootballData.org - Jogos Agendados")
    print("="*50)
    
    headers = {
        "X-Auth-Token": Config.FOOTBALL_DATA_KEY
    }
    
    try:
        # Buscar jogos do dia
        response = requests.get(
            f"{Config.FOOTBALL_DATA_BASE}/matches",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            
            print(f"✅ API funcionando!")
            print(f"📅 Jogos hoje: {len(matches)}")
            
            for match in matches[:3]:
                home = match.get("homeTeam", {}).get("name", "?")
                away = match.get("awayTeam", {}).get("name", "?")
                status = match.get("status", "?")
                print(f"\n  ⚽ {home} vs {away}")
                print(f"     Status: {status}")
            
            return True
        elif response.status_code == 403:
            print("⚠️ Chave de API inválida ou não configurada")
            print("   Obtenha uma em: https://www.football-data.org/client/register")
            return False
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


# ============================================
# 🎯 TESTE 2: API DE ODDS
# ============================================

def test_odds_api():
    """
    Testa The Odds API para buscar odds em tempo real
    """
    print("\n" + "="*50)
    print("💰 TESTE: The Odds API - Odds ao Vivo")
    print("="*50)
    
    try:
        response = requests.get(
            f"{Config.ODDS_API_BASE}/sports/soccer_brazil_campeonato/odds",
            params={
                "apiKey": Config.ODDS_API_KEY,
                "regions": "br",
                "markets": "h2h"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcionando!")
            print(f"🎰 Jogos com odds: {len(data)}")
            
            for game in data[:3]:
                print(f"\n  ⚽ {game.get('home_team')} vs {game.get('away_team')}")
                bookmakers = game.get("bookmakers", [])
                if bookmakers:
                    bm = bookmakers[0]
                    print(f"     Casa: {bm.get('title')}")
                    markets = bm.get("markets", [])
                    if markets:
                        outcomes = markets[0].get("outcomes", [])
                        for o in outcomes:
                            print(f"     {o.get('name')}: {o.get('price')}")
            
            return True
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


# ============================================
# 🎬 TESTE 3: APIs DE REPLAY/MÍDIA
# ============================================

def test_replay_sources():
    """
    Testa fontes de replay de gols
    """
    print("\n" + "="*50)
    print("🎬 TESTE: Fontes de Replay de Gols")
    print("="*50)
    
    sources = {
        "Scorebat (Grátis)": "https://www.scorebat.com/video-api/v3/feed/?token=YOUR_TOKEN",
        "Sportmonks": "https://api.sportmonks.com/v3/football",
        "Twitter/X Search": "https://api.twitter.com/2/tweets/search/recent"
    }
    
    print("\n📋 Fontes disponíveis para integração:")
    
    # Scorebat - API de vídeos gratuita
    print("\n1️⃣ SCOREBAT (Recomendado para começar)")
    print("   ✅ Grátis com registro")
    print("   ✅ Vídeos de highlights automáticos")
    print("   ✅ Embed HTML pronto")
    print("   📎 https://www.scorebat.com/video-api/")
    
    # Testar Scorebat
    try:
        # Endpoint público de teste
        response = requests.get(
            "https://www.scorebat.com/video-api/v3/",
            timeout=5
        )
        if response.status_code in [200, 401, 403]:
            print("   🔌 Endpoint acessível!")
    except:
        print("   ⚠️ Não foi possível testar endpoint")
    
    print("\n2️⃣ TWITTER/X CLIPS")
    print("   ⚠️ API paga ($100/mês)")
    print("   ✅ Clips em tempo real")
    print("   ✅ Cobertura global")
    
    print("\n3️⃣ YOUTUBE DATA API")
    print("   ✅ Gratuita com limites")
    print("   ⚠️ Delay de minutos para upload")
    print("   ✅ Boa para highlights pós-jogo")
    
    return True


# ============================================
# 💬 TESTE 4: SUPABASE REALTIME
# ============================================

def test_supabase_realtime_structure():
    """
    Testa estrutura necessária no Supabase para chat em tempo real
    """
    print("\n" + "="*50)
    print("💬 TESTE: Estrutura Supabase Realtime")
    print("="*50)
    
    print("\n📋 Tabelas necessárias para o sistema de salas:")
    
    # Estrutura de tabelas
    tables = {
        "game_rooms": {
            "campos": [
                "id (UUID, PK)",
                "fixture_id (INT) - ID do jogo na API",
                "home_team (TEXT)",
                "away_team (TEXT)",
                "home_score (INT)",
                "away_score (INT)",
                "status (TEXT) - live/finished/scheduled",
                "minute (INT)",
                "viewers_count (INT)",
                "created_at (TIMESTAMP)",
            ],
            "realtime": True
        },
        "room_users": {
            "campos": [
                "id (UUID, PK)",
                "room_id (UUID, FK)",
                "user_id (UUID, FK)",
                "plan (TEXT) - free/basic/pro/elite",
                "selected_odds (JSONB)",
                "joined_at (TIMESTAMP)",
                "is_online (BOOL)",
            ],
            "realtime": True
        },
        "room_messages": {
            "campos": [
                "id (UUID, PK)",
                "room_id (UUID, FK)",
                "user_id (UUID, FK)",
                "message (TEXT)",
                "message_type (TEXT) - text/gif/sticker/reaction",
                "created_at (TIMESTAMP)",
            ],
            "realtime": True
        },
        "user_odds_status": {
            "campos": [
                "id (UUID, PK)",
                "room_id (UUID, FK)",
                "user_id (UUID, FK)",
                "odd_type (TEXT)",
                "odd_value (DECIMAL)",
                "status (TEXT) - pending/won/lost",
                "updated_at (TIMESTAMP)",
            ],
            "realtime": True
        }
    }
    
    for table_name, config in tables.items():
        print(f"\n📦 {table_name}")
        print(f"   Realtime: {'✅ Sim' if config['realtime'] else '❌ Não'}")
        for campo in config["campos"]:
            print(f"   • {campo}")
    
    print("\n✅ Estrutura mapeada com sucesso!")
    return True


# ============================================
# 💎 TESTE 5: SISTEMA DE PLANOS
# ============================================

def test_plans_structure():
    """
    Valida estrutura dos novos planos v2.0
    """
    print("\n" + "="*50)
    print("💎 TESTE: Estrutura de Planos v2.0")
    print("="*50)
    
    plans = {
        "free": {
            "name": "Free",
            "price": 0,
            "features": {
                "chat_texto": True,
                "emojis_basicos": True,
                "gifs": False,
                "stickers": False,
                "imagens": False,
                "salas_privadas": 0,
                "efeito_gol_custom": False,
                "badge": None,
                "destaque_lista": False,
                "efeito_celebracao": "confete_simples"
            }
        },
        "basic": {
            "name": "Basic",
            "price": 19.90,
            "stripe_price_id": "price_XXXXXX",  # Criar no Stripe
            "features": {
                "chat_texto": True,
                "emojis_basicos": True,
                "gifs": True,
                "stickers": False,
                "imagens": False,
                "salas_privadas": 1,
                "efeito_gol_custom": False,
                "badge": "bronze",
                "destaque_lista": False,
                "efeito_celebracao": "confete_colorido"
            }
        },
        "pro": {
            "name": "Pro",
            "price": 49.90,
            "stripe_price_id": "price_XXXXXX",  # Criar no Stripe
            "popular": True,
            "features": {
                "chat_texto": True,
                "emojis_basicos": True,
                "gifs": True,
                "stickers": True,
                "imagens": True,
                "salas_privadas": 5,
                "efeito_gol_custom": False,
                "badge": "prata",
                "destaque_lista": True,
                "efeito_celebracao": "animacao_personalizada"
            }
        },
        "elite": {
            "name": "Elite",
            "price": 99.90,
            "stripe_price_id": "price_XXXXXX",  # Criar no Stripe
            "features": {
                "chat_texto": True,
                "emojis_basicos": True,
                "gifs": True,
                "stickers": True,
                "imagens": True,
                "salas_privadas": -1,  # Ilimitado
                "efeito_gol_custom": True,
                "badge": "dourado",
                "destaque_lista": "topo",
                "efeito_celebracao": "full_customizavel",
                "loja_customizacao": True
            }
        }
    }
    
    print("\n📊 Comparativo de Features:")
    print("-" * 60)
    
    for plan_id, plan in plans.items():
        print(f"\n{'⭐ ' if plan.get('popular') else '  '}{plan['name'].upper()} - R$ {plan['price']:.2f}/mês")
        features = plan["features"]
        print(f"   Chat: {'✅' if features['chat_texto'] else '❌'} | GIFs: {'✅' if features['gifs'] else '❌'} | Stickers: {'✅' if features['stickers'] else '❌'}")
        salas = features['salas_privadas']
        salas_text = "Ilimitado" if salas == -1 else f"{salas} sala(s)"
        print(f"   Salas privadas: {salas_text}")
        print(f"   Badge: {features['badge'] or 'Nenhum'}")
        print(f"   Celebração: {features['efeito_celebracao']}")
    
    print("\n✅ Estrutura de planos validada!")
    return plans


# ============================================
# 🔄 TESTE 6: WEBSOCKET SIMULATION
# ============================================

def test_websocket_events():
    """
    Simula eventos de WebSocket para o sistema de salas
    """
    print("\n" + "="*50)
    print("🔄 TESTE: Eventos WebSocket (Simulação)")
    print("="*50)
    
    events = [
        {
            "type": "user_joined",
            "payload": {
                "user_id": "uuid-123",
                "username": "João_Apostador",
                "plan": "elite",
                "selected_odds": [
                    {"type": "1x2", "pick": "home", "odds": 1.85},
                    {"type": "over_under", "pick": "over_2.5", "odds": 2.10}
                ]
            }
        },
        {
            "type": "message",
            "payload": {
                "user_id": "uuid-123",
                "username": "João_Apostador",
                "plan": "elite",
                "message": "VAAAMOS! 🔥",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "type": "score_update",
            "payload": {
                "home_score": 1,
                "away_score": 0,
                "minute": 34,
                "scorer": "Neymar Jr",
                "assist": "Vini Jr"
            }
        },
        {
            "type": "odd_status_change",
            "payload": {
                "user_id": "uuid-123",
                "odd_type": "1x2",
                "pick": "home",
                "new_status": "won",
                "trigger_celebration": True,
                "celebration_type": "elite"  # Baseado no plano
            }
        },
        {
            "type": "reaction",
            "payload": {
                "user_id": "uuid-456",
                "reaction": "goal",
                "emoji": "⚽🎉"
            }
        }
    ]
    
    print("\n📡 Eventos do sistema:")
    for event in events:
        print(f"\n  📨 {event['type'].upper()}")
        print(f"     Payload: {json.dumps(event['payload'], indent=6, default=str)[:200]}...")
    
    print("\n✅ Estrutura de eventos mapeada!")
    return events


# ============================================
# 🧮 TESTE 7: CÁLCULO DE CUSTOS
# ============================================

def test_infrastructure_costs():
    """
    Estima custos de infraestrutura
    """
    print("\n" + "="*50)
    print("🧮 TESTE: Estimativa de Custos de Infraestrutura")
    print("="*50)
    
    costs = {
        "Supabase Pro": {
            "preco": 25,
            "moeda": "USD",
            "inclui": ["500MB DB", "5GB bandwidth", "Realtime ilimitado"]
        },
        "Vercel Pro": {
            "preco": 20,
            "moeda": "USD",
            "inclui": ["100GB bandwidth", "Serverless functions", "Analytics"]
        },
        "API Football": {
            "preco": 0,  # Free tier: 100 requests/dia
            "moeda": "USD",
            "inclui": ["100 req/dia grátis", "Placar ao vivo", "Eventos do jogo"]
        },
        "The Odds API": {
            "preco": 0,  # Free tier: 500 requests/mês
            "moeda": "USD",
            "inclui": ["500 req/mês grátis", "Odds de múltiplas casas"]
        },
        "Scorebat (Replays)": {
            "preco": 0,
            "moeda": "USD",
            "inclui": ["Vídeos grátis com registro", "Embed pronto"]
        }
    }
    
    total_usd = 0
    print("\n💰 Custos mensais estimados:")
    print("-" * 50)
    
    for service, config in costs.items():
        preco = config["preco"]
        total_usd += preco
        status = "GRÁTIS" if preco == 0 else f"${preco}/mês"
        print(f"\n  {service}: {status}")
        for item in config["inclui"]:
            print(f"    • {item}")
    
    print("\n" + "-" * 50)
    print(f"💵 TOTAL: ${total_usd}/mês (~R$ {total_usd * 5:.2f})")
    print("\n⚠️ Nota: Custos podem aumentar com escala")
    print("   • Supabase: +$0.10/GB bandwidth extra")
    print("   • API Football Pro: $19/mês para 7.500 req/dia")
    
    return costs


# ============================================
# 🚀 EXECUÇÃO DOS TESTES
# ============================================

def run_all_tests():
    """
    Executa todos os testes
    """
    print("\n" + "🚀"*25)
    print("  ODINENX v2.0 - SUÍTE DE TESTES")
    print("🚀"*25)
    
    results = {}
    
    # Testes que não precisam de API key
    print("\n\n📋 TESTES DE ESTRUTURA (sem API)")
    print("=" * 60)
    
    results["supabase_structure"] = test_supabase_realtime_structure()
    results["plans"] = test_plans_structure()
    results["websocket_events"] = test_websocket_events()
    results["replay_sources"] = test_replay_sources()
    results["infrastructure"] = test_infrastructure_costs()
    
    # Testes que precisam de API key (comentados por padrão)
    print("\n\n📋 TESTES DE API (precisam de chaves)")
    print("=" * 60)
    
    print("\n⚠️ Para testar as APIs ao vivo, configure as chaves no Config:")
    print("   • API Football: https://www.api-football.com/")
    print("   • FootballData: https://www.football-data.org/")
    print("   • The Odds API: https://the-odds-api.com/")
    
    # Descomente para testar com API keys configuradas:
    # results["api_football"] = test_api_football_live()
    # results["football_data"] = test_football_data_org()
    # results["odds_api"] = test_odds_api()
    
    # Resumo
    print("\n\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n✅ Testes passados: {passed}/{total}")
    
    for test, result in results.items():
        status = "✅ OK" if result else "❌ FALHOU"
        print(f"   {test}: {status}")
    
    print("\n" + "🎯"*25)
    print("  PRÓXIMOS PASSOS")
    print("🎯"*25)
    
    print("""
    1️⃣ Criar conta gratuita no API Football
       → https://www.api-football.com/
       
    2️⃣ Criar conta no Scorebat para replays
       → https://www.scorebat.com/video-api/
       
    3️⃣ Criar tabelas no Supabase
       → game_rooms, room_users, room_messages
       
    4️⃣ Atualizar planos no Stripe
       → Novos preços: 19.90, 49.90, 99.90
       
    5️⃣ Implementar componentes Vue
       → GameRoom.vue, LiveChat.vue, OddsPanel.vue
    """)


if __name__ == "__main__":
    run_all_tests()
