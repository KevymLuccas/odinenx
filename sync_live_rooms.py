#!/usr/bin/env python3
"""
🏟️ ODINENX - Sincronizador de Salas ao Vivo
Busca jogos reais da Football-Data.org e sincroniza com Supabase

Uso:
  python sync_live_rooms.py

Requisitos:
  pip install httpx python-dotenv
"""

import os
import httpx
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Configurações
SUPABASE_URL = 'https://mzamszcpbverpadjelck.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTA5NjIsImV4cCI6MjA4NTM2Njk2Mn0.I8uUlJxgm2UgyavzRA6ATcaoV3SRVd9Z-NgeENzzUN4'

# Football-Data.org (API gratuita)
FOOTBALL_DATA_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'

# Ligas disponíveis no Football-Data.org (free tier)
LIGAS = {
    'BSA': 'Brasileirão Série A',
    'PL': 'Premier League',
    'PD': 'La Liga',
    'SA': 'Serie A',
    'BL1': 'Bundesliga',
    'FL1': 'Ligue 1',
    'CL': 'Champions League',
    'EC': 'Euro Championship'
}

# Mapeamento de status Football-Data.org
STATUS_MAP = {
    'SCHEDULED': 'scheduled',
    'TIMED': 'scheduled',
    'IN_PLAY': 'live',
    'PAUSED': 'halftime',
    'FINISHED': 'finished',
    'SUSPENDED': 'cancelled',
    'POSTPONED': 'cancelled',
    'CANCELLED': 'cancelled',
    'AWARDED': 'finished'
}


async def fetch_fixtures(client: httpx.AsyncClient, league: str = None):
    """Buscar jogos da Football-Data.org"""
    
    headers = {
        'X-Auth-Token': FOOTBALL_DATA_KEY
    }
    
    fixtures = []
    
    # Buscar de cada liga
    leagues_to_fetch = [league] if league else list(LIGAS.keys())
    
    for league_code in leagues_to_fetch:
        try:
            print(f"🔄 Buscando {LIGAS.get(league_code, league_code)}...")
            
            # Buscar jogos de hoje
            today = datetime.now().strftime('%Y-%m-%d')
            
            response = await client.get(
                f"{FOOTBALL_DATA_URL}/competitions/{league_code}/matches",
                params={'dateFrom': today, 'dateTo': today},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 429:
                print(f"   ⚠️ Rate limit para {league_code}, pulando...")
                await asyncio.sleep(1)
                continue
            
            if response.status_code != 200:
                print(f"   ⚠️ Erro {response.status_code} para {league_code}")
                continue
            
            data = response.json()
            matches = data.get('matches', [])
            
            for match in matches:
                status_str = match.get('status', 'SCHEDULED')
                
                # Calcular minuto (Football-Data não fornece diretamente)
                minute = 0
                if status_str == 'IN_PLAY':
                    # Estimar baseado no horário de início
                    start_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                    now = datetime.now(start_time.tzinfo)
                    elapsed = (now - start_time).total_seconds() / 60
                    minute = max(0, min(90, int(elapsed)))
                elif status_str == 'PAUSED':
                    minute = 45
                
                fixtures.append({
                    'fixture_id': match['id'],
                    'home_team': match['homeTeam']['name'],
                    'away_team': match['awayTeam']['name'],
                    'home_team_logo': match['homeTeam'].get('crest', ''),
                    'away_team_logo': match['awayTeam'].get('crest', ''),
                    'home_score': match['score']['fullTime']['home'] or 0,
                    'away_score': match['score']['fullTime']['away'] or 0,
                    'minute': minute,
                    'status': STATUS_MAP.get(status_str, 'scheduled'),
                    'league': LIGAS.get(league_code, league_code),
                    'league_logo': data.get('competition', {}).get('emblem', ''),
                    'start_time': match['utcDate']
                })
            
            print(f"   ✅ {len(matches)} jogos em {LIGAS.get(league_code, league_code)}")
            
            # Rate limit da API gratuita
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Erro em {league_code}: {e}")
    
    print(f"\n✅ Total: {len(fixtures)} jogos encontrados")
    return fixtures


async def sync_to_supabase(client: httpx.AsyncClient, fixtures: list):
    """Sincronizar jogos com Supabase"""
    
    if not fixtures:
        print("⚠️ Nenhum jogo para sincronizar")
        return
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }
    
    # Upsert jogos (insere ou atualiza)
    for fixture in fixtures:
        try:
            # Verificar se já existe
            check_url = f"{SUPABASE_URL}/rest/v1/game_rooms?fixture_id=eq.{fixture['fixture_id']}&select=id"
            check_response = await client.get(check_url, headers=headers)
            existing = check_response.json()
            
            if existing:
                # Atualizar
                room_id = existing[0]['id']
                update_data = {
                    'home_score': fixture['home_score'],
                    'away_score': fixture['away_score'],
                    'minute': fixture['minute'],
                    'status': fixture['status'],
                    'updated_at': datetime.now().isoformat()
                }
                
                update_url = f"{SUPABASE_URL}/rest/v1/game_rooms?id=eq.{room_id}"
                await client.patch(update_url, json=update_data, headers=headers)
                print(f"🔄 Atualizado: {fixture['home_team']} vs {fixture['away_team']} ({fixture['status']} {fixture['minute']}')")
            else:
                # Inserir novo
                insert_url = f"{SUPABASE_URL}/rest/v1/game_rooms"
                await client.post(insert_url, json=fixture, headers=headers)
                print(f"➕ Criado: {fixture['home_team']} vs {fixture['away_team']}")
                
        except Exception as e:
            print(f"❌ Erro ao sincronizar {fixture['home_team']} vs {fixture['away_team']}: {e}")
    
    print(f"\n✅ Sincronização completa!")


async def remove_demo_games(client: httpx.AsyncClient):
    """Remover jogos de demonstração (fixture_id 1001-1004)"""
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("🗑️ Removendo jogos de demonstração...")
    
    delete_url = f"{SUPABASE_URL}/rest/v1/game_rooms?fixture_id=in.(1001,1002,1003,1004)"
    
    try:
        response = await client.delete(delete_url, headers=headers)
        print("✅ Jogos de demonstração removidos!")
    except Exception as e:
        print(f"⚠️ Erro ao remover demos (pode não existir): {e}")


async def main():
    print("=" * 50)
    print("🏟️ ODINENX - Sincronizador de Salas ao Vivo")
    print("=" * 50)
    
    print(f"📡 Supabase: {SUPABASE_URL}")
    print(f"🔑 Football-Data.org API")
    print()
    
    async with httpx.AsyncClient() as client:
        # 1. Remover demos
        await remove_demo_games(client)
        print()
        
        # 2. Buscar jogos de hoje de todas as ligas
        fixtures = await fetch_fixtures(client)
        
        # 3. Sincronizar
        await sync_to_supabase(client, fixtures)
        
        # Resumo
        print("\n" + "=" * 50)
        print("📋 RESUMO")
        print("=" * 50)
        live = [f for f in fixtures if f['status'] == 'live']
        scheduled = [f for f in fixtures if f['status'] == 'scheduled']
        finished = [f for f in fixtures if f['status'] == 'finished']
        
        print(f"🔴 Ao vivo: {len(live)}")
        print(f"⏰ Agendados: {len(scheduled)}")
        print(f"✅ Finalizados: {len(finished)}")
        
        if live:
            print("\n🔴 JOGOS AO VIVO:")
            for f in live:
                print(f"   {f['home_team']} {f['home_score']}-{f['away_score']} {f['away_team']} ({f['minute']}')")


if __name__ == '__main__':
    asyncio.run(main())
