"""
🧪 Testes de Websocket/Realtime - ODINENX v2.0
Simula eventos em tempo real do Supabase
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Dict, List, Callable
from dataclasses import dataclass
from enum import Enum


# ============================================
# 📡 SIMULADOR DE REALTIME
# ============================================

class RealtimeEventType(Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class RealtimeEvent:
    """Evento do Supabase Realtime"""
    table: str
    event_type: RealtimeEventType
    old_record: Dict = None
    new_record: Dict = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class SupabaseRealtimeSimulator:
    """Simulador do Supabase Realtime"""
    
    def __init__(self):
        self.channels: Dict[str, List[Callable]] = {}
        self.event_log: List[RealtimeEvent] = []
    
    def subscribe(self, channel: str, callback: Callable):
        """Inscreve-se em um canal"""
        if channel not in self.channels:
            self.channels[channel] = []
        self.channels[channel].append(callback)
        print(f"   ✅ Inscrito no canal: {channel}")
    
    def broadcast(self, channel: str, event: RealtimeEvent):
        """Envia evento para todos os inscritos"""
        self.event_log.append(event)
        
        if channel in self.channels:
            for callback in self.channels[channel]:
                callback(event)
    
    def simulate_message(self, room_id: str, user_id: str, message: str, plan: str):
        """Simula nova mensagem no chat"""
        event = RealtimeEvent(
            table="room_messages",
            event_type=RealtimeEventType.INSERT,
            new_record={
                "id": f"msg_{int(datetime.now().timestamp() * 1000)}",
                "room_id": room_id,
                "user_id": user_id,
                "message": message,
                "message_type": "text",
                "user_plan": plan,
                "created_at": datetime.now().isoformat()
            }
        )
        self.broadcast(f"room:{room_id}:messages", event)
        return event
    
    def simulate_user_join(self, room_id: str, user_data: Dict):
        """Simula entrada de usuário na sala"""
        event = RealtimeEvent(
            table="room_users",
            event_type=RealtimeEventType.INSERT,
            new_record={
                "id": f"ru_{int(datetime.now().timestamp())}",
                "room_id": room_id,
                **user_data,
                "joined_at": datetime.now().isoformat(),
                "is_online": True
            }
        )
        self.broadcast(f"room:{room_id}:users", event)
        return event
    
    def simulate_score_update(self, room_id: str, home_score: int, away_score: int, minute: int):
        """Simula atualização de placar"""
        event = RealtimeEvent(
            table="game_rooms",
            event_type=RealtimeEventType.UPDATE,
            old_record={"home_score": home_score - 1 if home_score > 0 else 0},
            new_record={
                "room_id": room_id,
                "home_score": home_score,
                "away_score": away_score,
                "minute": minute,
                "updated_at": datetime.now().isoformat()
            }
        )
        self.broadcast(f"room:{room_id}:score", event)
        return event
    
    def simulate_odd_status_change(self, room_id: str, user_id: str, odd_type: str, new_status: str):
        """Simula mudança de status de odd"""
        event = RealtimeEvent(
            table="user_odds_status",
            event_type=RealtimeEventType.UPDATE,
            old_record={"status": "pending"},
            new_record={
                "room_id": room_id,
                "user_id": user_id,
                "odd_type": odd_type,
                "status": new_status,
                "updated_at": datetime.now().isoformat()
            }
        )
        self.broadcast(f"room:{room_id}:odds", event)
        return event
    
    def simulate_reaction(self, room_id: str, user_id: str, reaction: str):
        """Simula reação rápida"""
        event = RealtimeEvent(
            table="room_reactions",
            event_type=RealtimeEventType.INSERT,
            new_record={
                "room_id": room_id,
                "user_id": user_id,
                "reaction": reaction,
                "created_at": datetime.now().isoformat()
            }
        )
        self.broadcast(f"room:{room_id}:reactions", event)
        return event


# ============================================
# 🎯 HANDLERS DE EVENTOS
# ============================================

def on_message_received(event: RealtimeEvent):
    """Handler para novas mensagens"""
    data = event.new_record
    plan_emoji = {"elite": "👑", "pro": "⭐", "basic": "🥉", "free": ""}
    emoji = plan_emoji.get(data.get("user_plan", "free"), "")
    print(f"      💬 {emoji} [{data['user_id']}]: {data['message']}")


def on_user_joined(event: RealtimeEvent):
    """Handler para entrada de usuário"""
    data = event.new_record
    print(f"      🚪 {data['username']} entrou na sala (Plano: {data['plan']})")


def on_score_update(event: RealtimeEvent):
    """Handler para atualização de placar"""
    data = event.new_record
    print(f"      ⚽ PLACAR: {data['home_score']} x {data['away_score']} ({data['minute']}')")


def on_odd_status_change(event: RealtimeEvent):
    """Handler para mudança de status de odd"""
    data = event.new_record
    status_emoji = {"won": "✅", "lost": "❌", "pending": "⏳"}
    print(f"      🎯 {status_emoji[data['status']]} {data['user_id']}: {data['odd_type']} = {data['status']}")


def on_reaction(event: RealtimeEvent):
    """Handler para reações"""
    data = event.new_record
    print(f"      🎭 Reação: {data['reaction']}")


# ============================================
# 🧪 TESTES DE REALTIME
# ============================================

def test_realtime_subscription():
    """Testa sistema de inscrição em canais"""
    
    print("\n" + "="*50)
    print("📡 TESTE: Sistema de Inscrição em Canais")
    print("="*50)
    
    sim = SupabaseRealtimeSimulator()
    room_id = "room_12345"
    
    # Inscrever nos canais
    print("\n   📺 Inscrevendo nos canais...")
    sim.subscribe(f"room:{room_id}:messages", on_message_received)
    sim.subscribe(f"room:{room_id}:users", on_user_joined)
    sim.subscribe(f"room:{room_id}:score", on_score_update)
    sim.subscribe(f"room:{room_id}:odds", on_odd_status_change)
    sim.subscribe(f"room:{room_id}:reactions", on_reaction)
    
    print(f"\n   ✅ Total de canais: {len(sim.channels)}")
    
    return sim, room_id


def test_message_flow():
    """Testa fluxo de mensagens"""
    
    print("\n" + "="*50)
    print("💬 TESTE: Fluxo de Mensagens em Tempo Real")
    print("="*50)
    
    sim, room_id = test_realtime_subscription()
    
    print("\n   📨 Enviando mensagens...")
    
    messages = [
        {"user_id": "user_joao", "message": "Vamooo Mengão! 🔥", "plan": "elite"},
        {"user_id": "user_maria", "message": "Empata hoje!", "plan": "pro"},
        {"user_id": "user_pedro", "message": "Bom jogo a todos", "plan": "basic"},
        {"user_id": "user_carlos", "message": "Primeira vez aqui", "plan": "free"},
    ]
    
    for msg in messages:
        sim.simulate_message(room_id, msg["user_id"], msg["message"], msg["plan"])
    
    print(f"\n   ✅ Mensagens enviadas: {len(messages)}")
    return True


def test_score_updates():
    """Testa atualizações de placar"""
    
    print("\n" + "="*50)
    print("⚽ TESTE: Atualizações de Placar em Tempo Real")
    print("="*50)
    
    sim, room_id = test_realtime_subscription()
    
    print("\n   🏟️ Simulando jogo...")
    
    # Simular progressão do jogo
    events = [
        {"home": 0, "away": 0, "minute": 0, "desc": "Início do jogo"},
        {"home": 1, "away": 0, "minute": 23, "desc": "GOL! Time da casa"},
        {"home": 1, "away": 1, "minute": 45, "desc": "GOL! Empate"},
        {"home": 2, "away": 1, "minute": 67, "desc": "GOL! Virada"},
        {"home": 2, "away": 2, "minute": 89, "desc": "GOL! Empate no final"},
    ]
    
    for evt in events:
        print(f"\n   📺 {evt['desc']}")
        sim.simulate_score_update(room_id, evt["home"], evt["away"], evt["minute"])
    
    print(f"\n   ✅ Eventos de placar: {len(events)}")
    return True


def test_odds_tracking():
    """Testa rastreamento de odds"""
    
    print("\n" + "="*50)
    print("🎯 TESTE: Rastreamento de Odds em Tempo Real")
    print("="*50)
    
    sim, room_id = test_realtime_subscription()
    
    print("\n   🎰 Simulando mudanças de status...")
    
    # Simular mudanças de status
    odds_updates = [
        {"user_id": "user_joao", "odd_type": "over_2.5", "status": "won"},
        {"user_id": "user_maria", "odd_type": "1x2_draw", "status": "lost"},
        {"user_id": "user_pedro", "odd_type": "btts_yes", "status": "won"},
    ]
    
    for update in odds_updates:
        sim.simulate_odd_status_change(
            room_id, 
            update["user_id"], 
            update["odd_type"], 
            update["status"]
        )
    
    print(f"\n   ✅ Atualizações de odds: {len(odds_updates)}")
    return True


def test_reactions():
    """Testa sistema de reações rápidas"""
    
    print("\n" + "="*50)
    print("🎭 TESTE: Sistema de Reações Rápidas")
    print("="*50)
    
    sim, room_id = test_realtime_subscription()
    
    print("\n   😊 Simulando reações...")
    
    reactions = ["⚽", "🔥", "😱", "👏", "🎉", "😭", "💪", "🙏"]
    
    for reaction in reactions[:5]:
        sim.simulate_reaction(room_id, f"user_{random.randint(1, 10)}", reaction)
    
    print(f"\n   ✅ Reações enviadas: 5")
    return True


def test_presence_system():
    """Testa sistema de presença de usuários"""
    
    print("\n" + "="*50)
    print("👥 TESTE: Sistema de Presença de Usuários")
    print("="*50)
    
    sim, room_id = test_realtime_subscription()
    
    print("\n   🚪 Simulando entradas...")
    
    users = [
        {"user_id": "u1", "username": "João_Elite", "plan": "elite", "selected_odds": ["1x2_home"]},
        {"user_id": "u2", "username": "Maria_Pro", "plan": "pro", "selected_odds": ["over_2.5"]},
        {"user_id": "u3", "username": "Pedro_Basic", "plan": "basic", "selected_odds": ["btts"]},
        {"user_id": "u4", "username": "Carlos_Free", "plan": "free", "selected_odds": []},
    ]
    
    for user in users:
        sim.simulate_user_join(room_id, user)
    
    print(f"\n   ✅ Usuários na sala: {len(users)}")
    
    # Ordenação por plano (Elite primeiro)
    print("\n   📋 Lista ordenada por plano:")
    plan_order = {"elite": 0, "pro": 1, "basic": 2, "free": 3}
    sorted_users = sorted(users, key=lambda x: plan_order[x["plan"]])
    
    badges = {"elite": "👑", "pro": "⭐", "basic": "🥉", "free": "  "}
    for user in sorted_users:
        print(f"      {badges[user['plan']]} [{user['plan'].upper()}] {user['username']}")
    
    return True


def test_full_game_simulation():
    """Simula um jogo completo com todos os eventos"""
    
    print("\n" + "="*60)
    print("🎮 SIMULAÇÃO COMPLETA: Jogo ao Vivo com Todos os Eventos")
    print("="*60)
    
    sim, room_id = test_realtime_subscription()
    
    # Timeline do jogo
    timeline = [
        {"time": 0, "type": "start", "desc": "🏟️ Jogo iniciado!"},
        {"time": 1, "type": "join", "user": "João", "plan": "elite"},
        {"time": 2, "type": "join", "user": "Maria", "plan": "pro"},
        {"time": 3, "type": "message", "user": "João", "msg": "Vai começar!", "plan": "elite"},
        {"time": 15, "type": "message", "user": "Maria", "msg": "Tá equilibrado", "plan": "pro"},
        {"time": 23, "type": "score", "home": 1, "away": 0},
        {"time": 23, "type": "reaction", "reaction": "⚽🎉"},
        {"time": 24, "type": "message", "user": "João", "msg": "GOOOOOL!", "plan": "elite"},
        {"time": 25, "type": "odd_update", "user": "João", "odd": "1x2_home", "status": "pending"},
        {"time": 45, "type": "score", "home": 1, "away": 1},
        {"time": 45, "type": "reaction", "reaction": "😱"},
        {"time": 46, "type": "message", "user": "Maria", "msg": "Empatou!", "plan": "pro"},
        {"time": 67, "type": "score", "home": 2, "away": 1},
        {"time": 67, "type": "reaction", "reaction": "🔥🔥🔥"},
        {"time": 68, "type": "odd_update", "user": "João", "odd": "over_2.5", "status": "won"},
        {"time": 90, "type": "end", "desc": "🏁 Fim de jogo: 2 x 1"},
        {"time": 91, "type": "odd_update", "user": "João", "odd": "1x2_home", "status": "won"},
        {"time": 91, "type": "odd_update", "user": "Maria", "odd": "1x2_draw", "status": "lost"},
    ]
    
    print("\n   ⏱️ Timeline do jogo:")
    
    for event in timeline:
        minute = event["time"]
        
        if event["type"] == "start":
            print(f"\n   [{minute:02d}'] {event['desc']}")
            
        elif event["type"] == "join":
            sim.simulate_user_join(room_id, {
                "user_id": f"u_{event['user'].lower()}",
                "username": event["user"],
                "plan": event["plan"]
            })
            
        elif event["type"] == "message":
            sim.simulate_message(room_id, event["user"], event["msg"], event["plan"])
            
        elif event["type"] == "score":
            print(f"\n   [{minute:02d}'] ⚽ GOL!")
            sim.simulate_score_update(room_id, event["home"], event["away"], minute)
            
        elif event["type"] == "reaction":
            sim.simulate_reaction(room_id, "varios", event["reaction"])
            
        elif event["type"] == "odd_update":
            sim.simulate_odd_status_change(room_id, event["user"], event["odd"], event["status"])
            
        elif event["type"] == "end":
            print(f"\n   [{minute:02d}'] {event['desc']}")
    
    print(f"\n\n   📊 ESTATÍSTICAS FINAIS:")
    print(f"      Total de eventos: {len(sim.event_log)}")
    
    # Contar por tipo
    event_counts = {}
    for evt in sim.event_log:
        key = evt.table
        event_counts[key] = event_counts.get(key, 0) + 1
    
    for table, count in event_counts.items():
        print(f"      {table}: {count}")
    
    return True


# ============================================
# 🚀 EXECUTAR TODOS OS TESTES
# ============================================

def run_all_realtime_tests():
    """Executa todos os testes de realtime"""
    
    print("\n" + "🚀"*30)
    print("     ODINENX v2.0 - TESTES DE REALTIME")
    print("🚀"*30)
    
    tests = [
        ("Inscrição em Canais", test_realtime_subscription),
        ("Fluxo de Mensagens", test_message_flow),
        ("Atualizações de Placar", test_score_updates),
        ("Rastreamento de Odds", test_odds_tracking),
        ("Reações Rápidas", test_reactions),
        ("Sistema de Presença", test_presence_system),
        ("Simulação Completa", test_full_game_simulation),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = "✅ PASSOU" if result else "❌ FALHOU"
        except Exception as e:
            results[name] = f"❌ ERRO: {str(e)}"
    
    # Resumo
    print("\n\n" + "="*60)
    print("📊 RESUMO DOS TESTES DE REALTIME")
    print("="*60)
    
    for test_name, result in results.items():
        print(f"   {result} - {test_name}")
    
    passed = sum(1 for r in results.values() if "PASSOU" in r)
    total = len(results)
    
    print(f"\n   Total: {passed}/{total} testes passaram")
    
    return results


if __name__ == "__main__":
    run_all_realtime_tests()
