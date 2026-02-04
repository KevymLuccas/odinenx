"""
🧪 Testes de Simulação de Sala ao Vivo - ODINENX v2.0
Simula o comportamento de uma sala de jogo completa
"""

import json
import random
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from enum import Enum


# ============================================
# 📦 MODELOS DE DADOS
# ============================================

class UserPlan(Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ELITE = "elite"


class OddStatus(Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"


class MessageType(Enum):
    TEXT = "text"
    GIF = "gif"
    STICKER = "sticker"
    REACTION = "reaction"
    SYSTEM = "system"


@dataclass
class UserOdd:
    """Odd selecionada pelo usuário"""
    odd_type: str  # "1x2", "over_under", "btts", etc
    pick: str  # "home", "draw", "away", "over_2.5", etc
    odds_value: float
    status: OddStatus = OddStatus.PENDING


@dataclass
class RoomUser:
    """Usuário presente na sala"""
    user_id: str
    username: str
    plan: UserPlan
    selected_odds: List[UserOdd]
    joined_at: datetime
    is_online: bool = True
    
    def get_badge(self) -> str:
        badges = {
            UserPlan.FREE: "",
            UserPlan.BASIC: "🥉",
            UserPlan.PRO: "⭐",
            UserPlan.ELITE: "👑"
        }
        return badges[self.plan]
    
    def get_display_name(self) -> str:
        badge = self.get_badge()
        plan_tag = f"[{self.plan.value.upper()}]" if self.plan != UserPlan.FREE else "[FREE]"
        return f"{badge} {plan_tag} {self.username}".strip()
    
    def can_send_gif(self) -> bool:
        return self.plan != UserPlan.FREE
    
    def can_send_sticker(self) -> bool:
        return self.plan in [UserPlan.PRO, UserPlan.ELITE]
    
    def get_celebration_effect(self) -> str:
        effects = {
            UserPlan.FREE: "confete_simples",
            UserPlan.BASIC: "confete_colorido",
            UserPlan.PRO: "animacao_premium",
            UserPlan.ELITE: "full_customizado"
        }
        return effects[self.plan]


@dataclass
class ChatMessage:
    """Mensagem do chat"""
    id: str
    user: RoomUser
    content: str
    message_type: MessageType
    created_at: datetime


@dataclass
class GameRoom:
    """Sala de jogo ao vivo"""
    room_id: str
    fixture_id: int
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    minute: int = 0
    status: str = "scheduled"  # scheduled, live, halftime, finished
    users: List[RoomUser] = None
    messages: List[ChatMessage] = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = []
        if self.messages is None:
            self.messages = []
    
    def get_viewers_count(self) -> int:
        return len([u for u in self.users if u.is_online])
    
    def get_users_by_plan(self) -> Dict[UserPlan, List[RoomUser]]:
        """Retorna usuários agrupados por plano (Elite primeiro)"""
        result = {plan: [] for plan in UserPlan}
        for user in self.users:
            if user.is_online:
                result[user.plan].append(user)
        return result
    
    def get_sorted_users_list(self) -> List[RoomUser]:
        """Lista de usuários ordenada por plano (Elite no topo)"""
        plan_order = [UserPlan.ELITE, UserPlan.PRO, UserPlan.BASIC, UserPlan.FREE]
        sorted_users = []
        for plan in plan_order:
            sorted_users.extend([u for u in self.users if u.plan == plan and u.is_online])
        return sorted_users


# ============================================
# 🎮 SIMULADOR DE SALA
# ============================================

class RoomSimulator:
    """Simulador de sala de jogo ao vivo"""
    
    def __init__(self):
        self.room: Optional[GameRoom] = None
        self.event_log: List[Dict] = []
    
    def create_room(self, fixture_id: int, home_team: str, away_team: str) -> GameRoom:
        """Cria uma nova sala de jogo"""
        self.room = GameRoom(
            room_id=f"room_{fixture_id}_{int(time.time())}",
            fixture_id=fixture_id,
            home_team=home_team,
            away_team=away_team,
            status="live",
            minute=0
        )
        
        self._log_event("room_created", {
            "room_id": self.room.room_id,
            "match": f"{home_team} vs {away_team}"
        })
        
        return self.room
    
    def add_user(self, username: str, plan: UserPlan, odds: List[Dict]) -> RoomUser:
        """Adiciona usuário à sala"""
        user_odds = [
            UserOdd(
                odd_type=o["type"],
                pick=o["pick"],
                odds_value=o["odds"]
            ) for o in odds
        ]
        
        user = RoomUser(
            user_id=f"user_{username.lower()}_{random.randint(1000, 9999)}",
            username=username,
            plan=plan,
            selected_odds=user_odds,
            joined_at=datetime.now()
        )
        
        self.room.users.append(user)
        
        self._log_event("user_joined", {
            "user": user.get_display_name(),
            "odds_count": len(user_odds)
        })
        
        # Mensagem de sistema
        self._add_system_message(f"{user.get_display_name()} entrou na sala!")
        
        return user
    
    def send_message(self, user: RoomUser, content: str, msg_type: MessageType = MessageType.TEXT) -> Optional[ChatMessage]:
        """Envia mensagem no chat"""
        
        # Validar permissões
        if msg_type == MessageType.GIF and not user.can_send_gif():
            self._log_event("message_blocked", {
                "reason": "GIFs apenas para Basic+",
                "user": user.username
            })
            return None
        
        if msg_type == MessageType.STICKER and not user.can_send_sticker():
            self._log_event("message_blocked", {
                "reason": "Stickers apenas para Pro+",
                "user": user.username
            })
            return None
        
        message = ChatMessage(
            id=f"msg_{int(time.time() * 1000)}",
            user=user,
            content=content,
            message_type=msg_type,
            created_at=datetime.now()
        )
        
        self.room.messages.append(message)
        
        self._log_event("message_sent", {
            "user": user.get_display_name(),
            "type": msg_type.value,
            "content": content[:50]
        })
        
        return message
    
    def update_score(self, home_score: int, away_score: int, minute: int, scorer: str = None):
        """Atualiza placar e dispara eventos"""
        old_home = self.room.home_score
        old_away = self.room.away_score
        
        self.room.home_score = home_score
        self.room.away_score = away_score
        self.room.minute = minute
        
        # Detectar gol
        if home_score > old_home:
            self._trigger_goal_event("home", scorer, minute)
        elif away_score > old_away:
            self._trigger_goal_event("away", scorer, minute)
        
        # Verificar odds dos usuários
        self._check_user_odds()
    
    def _trigger_goal_event(self, team: str, scorer: str, minute: int):
        """Dispara evento de gol"""
        team_name = self.room.home_team if team == "home" else self.room.away_team
        
        self._log_event("goal", {
            "team": team_name,
            "scorer": scorer,
            "minute": minute,
            "score": f"{self.room.home_score} x {self.room.away_score}"
        })
        
        # Mensagem de sistema
        self._add_system_message(f"⚽ GOOOL! {team_name} - {scorer} ({minute}')")
        
        # Disparar celebrações por plano
        self._trigger_celebrations()
    
    def _check_user_odds(self):
        """Verifica status das odds dos usuários"""
        for user in self.room.users:
            for odd in user.selected_odds:
                if odd.status != OddStatus.PENDING:
                    continue
                
                # Verificar 1x2
                if odd.odd_type == "1x2":
                    if self.room.home_score > self.room.away_score and odd.pick == "home":
                        # Home está ganhando - odd "home" em potencial
                        pass  # Só confirma no final
                    elif self.room.home_score < self.room.away_score and odd.pick == "home":
                        odd.status = OddStatus.LOST
                        self._log_event("odd_lost", {
                            "user": user.username,
                            "odd": f"{odd.odd_type} - {odd.pick}"
                        })
                
                # Verificar Over/Under
                if odd.odd_type == "over_under":
                    total_goals = self.room.home_score + self.room.away_score
                    if "over" in odd.pick:
                        threshold = float(odd.pick.split("_")[1])
                        if total_goals > threshold:
                            odd.status = OddStatus.WON
                            self._trigger_user_celebration(user, odd)
    
    def _trigger_celebrations(self):
        """Dispara celebrações para todos na sala"""
        for user in self.room.users:
            effect = user.get_celebration_effect()
            self._log_event("celebration", {
                "user": user.username,
                "effect": effect,
                "plan": user.plan.value
            })
    
    def _trigger_user_celebration(self, user: RoomUser, odd: UserOdd):
        """Dispara celebração individual quando odd é acertada"""
        self._log_event("odd_won", {
            "user": user.get_display_name(),
            "odd": f"{odd.odd_type} - {odd.pick}",
            "odds_value": odd.odds_value,
            "celebration": user.get_celebration_effect()
        })
        
        # Mensagem de sistema
        msg = f"🎉 {user.get_display_name()} ACERTOU: {odd.odd_type} {odd.pick} @ {odd.odds_value}!"
        self._add_system_message(msg)
    
    def _add_system_message(self, content: str):
        """Adiciona mensagem de sistema"""
        system_user = RoomUser(
            user_id="system",
            username="Sistema",
            plan=UserPlan.FREE,
            selected_odds=[],
            joined_at=datetime.now()
        )
        
        message = ChatMessage(
            id=f"sys_{int(time.time() * 1000)}",
            user=system_user,
            content=content,
            message_type=MessageType.SYSTEM,
            created_at=datetime.now()
        )
        
        self.room.messages.append(message)
    
    def _log_event(self, event_type: str, data: Dict):
        """Registra evento no log"""
        self.event_log.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_room_state(self) -> Dict:
        """Retorna estado atual da sala"""
        return {
            "room_id": self.room.room_id,
            "match": f"{self.room.home_team} {self.room.home_score} x {self.room.away_score} {self.room.away_team}",
            "minute": self.room.minute,
            "status": self.room.status,
            "viewers": self.room.get_viewers_count(),
            "users_by_plan": {
                plan.value: len(users) 
                for plan, users in self.room.get_users_by_plan().items()
            },
            "messages_count": len(self.room.messages)
        }


# ============================================
# 🧪 EXECUTAR SIMULAÇÃO
# ============================================

def run_simulation():
    """Executa simulação completa de uma sala"""
    
    print("\n" + "🎮"*25)
    print("  SIMULAÇÃO DE SALA AO VIVO")
    print("🎮"*25)
    
    # Criar simulador
    sim = RoomSimulator()
    
    # 1. Criar sala
    print("\n\n📦 CRIANDO SALA...")
    room = sim.create_room(
        fixture_id=12345,
        home_team="Flamengo",
        away_team="Palmeiras"
    )
    print(f"   ✅ Sala criada: {room.room_id}")
    
    # 2. Adicionar usuários com diferentes planos
    print("\n\n👥 ADICIONANDO USUÁRIOS...")
    
    users_data = [
        {
            "username": "João_Apostador",
            "plan": UserPlan.ELITE,
            "odds": [
                {"type": "1x2", "pick": "home", "odds": 1.85},
                {"type": "over_under", "pick": "over_2.5", "odds": 2.10}
            ]
        },
        {
            "username": "Maria_Odds",
            "plan": UserPlan.PRO,
            "odds": [
                {"type": "1x2", "pick": "draw", "odds": 3.40},
                {"type": "btts", "pick": "yes", "odds": 1.75}
            ]
        },
        {
            "username": "Pedro_Bet",
            "plan": UserPlan.BASIC,
            "odds": [
                {"type": "1x2", "pick": "away", "odds": 4.20}
            ]
        },
        {
            "username": "Carlos_Free",
            "plan": UserPlan.FREE,
            "odds": [
                {"type": "1x2", "pick": "home", "odds": 1.85}
            ]
        }
    ]
    
    users = []
    for data in users_data:
        user = sim.add_user(data["username"], data["plan"], data["odds"])
        users.append(user)
        print(f"   ✅ {user.get_display_name()}")
    
    # 3. Lista de usuários ordenada
    print("\n\n📋 LISTA DE USUÁRIOS NA SALA (ordenada por plano):")
    for user in sim.room.get_sorted_users_list():
        print(f"   {user.get_display_name()}")
    
    # 4. Simular chat
    print("\n\n💬 SIMULANDO CHAT...")
    
    sim.send_message(users[0], "Vamooos Mengão! 🔴⚫", MessageType.TEXT)
    sim.send_message(users[1], "Hoje o Porco empata!", MessageType.TEXT)
    sim.send_message(users[0], "gif_comemoracao.gif", MessageType.GIF)  # Elite pode
    sim.send_message(users[2], "gif_torcida.gif", MessageType.GIF)  # Basic pode
    sim.send_message(users[3], "gif_test.gif", MessageType.GIF)  # Free NÃO pode
    
    print(f"   📨 Mensagens enviadas: {len(sim.room.messages)}")
    
    # 5. Simular gol
    print("\n\n⚽ SIMULANDO GOL...")
    sim.update_score(1, 0, 34, "Gabigol")
    
    # 6. Mais gols para testar Over 2.5
    print("\n\n⚽ MAIS GOLS...")
    sim.update_score(2, 0, 45, "Arrascaeta")
    sim.update_score(2, 1, 67, "Endrick")
    
    # 7. Estado final
    print("\n\n📊 ESTADO FINAL DA SALA:")
    state = sim.get_room_state()
    for key, value in state.items():
        print(f"   {key}: {value}")
    
    # 8. Log de eventos
    print("\n\n📜 LOG DE EVENTOS:")
    for event in sim.event_log[-10:]:
        print(f"   [{event['type']}] {event['data']}")
    
    # 9. Status das odds
    print("\n\n🎯 STATUS DAS ODDS DOS USUÁRIOS:")
    for user in sim.room.users:
        print(f"\n   {user.get_display_name()}:")
        for odd in user.selected_odds:
            status_emoji = {
                OddStatus.PENDING: "⏳",
                OddStatus.WON: "✅",
                OddStatus.LOST: "❌"
            }[odd.status]
            print(f"      {status_emoji} {odd.odd_type} {odd.pick} @ {odd.odds_value}")
    
    print("\n\n✅ Simulação concluída!")
    return sim


# ============================================
# 🎨 TESTE DE EFEITOS DE CELEBRAÇÃO
# ============================================

def test_celebration_effects():
    """Testa os efeitos de celebração por plano"""
    
    print("\n" + "🎉"*25)
    print("  TESTE DE EFEITOS DE CELEBRAÇÃO")
    print("🎉"*25)
    
    effects = {
        UserPlan.FREE: {
            "nome": "Confete Simples",
            "duracao_ms": 1000,
            "animacoes": ["confete_basico"],
            "sons": ["som_basico"],
            "destaque_chat": False,
            "popup_sala": False
        },
        UserPlan.BASIC: {
            "nome": "Confete Colorido",
            "duracao_ms": 2000,
            "animacoes": ["confete_colorido", "estrelas"],
            "sons": ["som_festivo"],
            "destaque_chat": True,
            "popup_sala": False
        },
        UserPlan.PRO: {
            "nome": "Animação Premium",
            "duracao_ms": 3000,
            "animacoes": ["confete_explosao", "fogos", "estrelas_brilhantes"],
            "sons": ["som_premium", "torcida"],
            "destaque_chat": True,
            "popup_sala": True
        },
        UserPlan.ELITE: {
            "nome": "Full Customizado",
            "duracao_ms": 5000,
            "animacoes": ["customizavel"],
            "sons": ["customizavel"],
            "destaque_chat": True,
            "popup_sala": True,
            "destaque_tela_todos": True,
            "replay_exclusivo": True,
            "customizacao": {
                "temas_confete": ["copa", "neon", "ouro", "fogo"],
                "sons_celebracao": ["narracao", "torcida", "meme"],
                "molduras": ["animada_dourada", "fogo", "diamante"]
            }
        }
    }
    
    for plan, config in effects.items():
        print(f"\n{'='*50}")
        print(f"{'👑' if plan == UserPlan.ELITE else '⭐' if plan == UserPlan.PRO else '🥉' if plan == UserPlan.BASIC else '  '} PLANO {plan.value.upper()}")
        print(f"{'='*50}")
        print(f"   Efeito: {config['nome']}")
        print(f"   Duração: {config['duracao_ms']}ms")
        print(f"   Animações: {', '.join(config['animacoes'])}")
        print(f"   Sons: {', '.join(config['sons'])}")
        print(f"   Destaque no chat: {'✅' if config['destaque_chat'] else '❌'}")
        print(f"   Popup na sala: {'✅' if config['popup_sala'] else '❌'}")
        
        if plan == UserPlan.ELITE:
            print(f"   Destaque para todos: ✅ (5 segundos)")
            print(f"   Replay exclusivo: ✅")
            print(f"   Customização disponível:")
            for cat, items in config["customizacao"].items():
                print(f"      • {cat}: {', '.join(items)}")
    
    return effects


# ============================================
# 🏪 TESTE DE LOJA DE CUSTOMIZAÇÃO (ELITE)
# ============================================

def test_customization_store():
    """Testa sistema de loja de customização"""
    
    print("\n" + "🏪"*25)
    print("  LOJA DE CUSTOMIZAÇÃO (ELITE)")
    print("🏪"*25)
    
    store_items = {
        "confetes": [
            {"id": "confete_copa", "nome": "Copa do Mundo", "preco": 0, "incluso": True},
            {"id": "confete_neon", "nome": "Neon Party", "preco": 9.90},
            {"id": "confete_ouro", "nome": "Chuva de Ouro", "preco": 14.90},
            {"id": "confete_fogo", "nome": "Chamas", "preco": 19.90}
        ],
        "sons": [
            {"id": "som_torcida", "nome": "Torcida", "preco": 0, "incluso": True},
            {"id": "som_narracao", "nome": "Narração Épica", "preco": 4.90},
            {"id": "som_galvao", "nome": "É TETRA!", "preco": 9.90},
            {"id": "som_meme", "nome": "Pack Memes", "preco": 14.90}
        ],
        "molduras": [
            {"id": "moldura_dourada", "nome": "Dourada Animada", "preco": 0, "incluso": True},
            {"id": "moldura_fogo", "nome": "Moldura de Fogo", "preco": 19.90},
            {"id": "moldura_diamante", "nome": "Diamante", "preco": 29.90},
            {"id": "moldura_neon", "nome": "Neon Pulsante", "preco": 24.90}
        ],
        "entradas": [
            {"id": "entrada_normal", "nome": "Entrada Normal", "preco": 0, "incluso": True},
            {"id": "entrada_fogos", "nome": "Entrada com Fogos", "preco": 9.90},
            {"id": "entrada_real", "nome": "Entrada Real", "preco": 19.90}
        ]
    }
    
    total_items = 0
    potencial_receita = 0
    
    for categoria, items in store_items.items():
        print(f"\n📦 {categoria.upper()}")
        print("-" * 40)
        
        for item in items:
            incluso = item.get("incluso", False)
            preco = item["preco"]
            
            if incluso:
                print(f"   ✅ {item['nome']} - INCLUSO")
            else:
                print(f"   💰 {item['nome']} - R$ {preco:.2f}")
                potencial_receita += preco
            
            total_items += 1
    
    print(f"\n{'='*40}")
    print(f"📊 RESUMO DA LOJA:")
    print(f"   Total de items: {total_items}")
    print(f"   Potencial de receita por usuário: R$ {potencial_receita:.2f}")
    
    # Estimativa de receita
    elite_users = 50  # Estimativa de 50 usuários Elite
    conversion_rate = 0.3  # 30% compram algo
    avg_spend = potencial_receita * 0.25  # Gasto médio de 25% do total
    
    monthly_store_revenue = elite_users * conversion_rate * avg_spend
    print(f"\n💰 ESTIMATIVA DE RECEITA DA LOJA:")
    print(f"   Usuários Elite: {elite_users}")
    print(f"   Taxa de conversão: {conversion_rate*100}%")
    print(f"   Gasto médio: R$ {avg_spend:.2f}")
    print(f"   Receita mensal estimada: R$ {monthly_store_revenue:.2f}")
    
    return store_items


# ============================================
# 🚀 EXECUTAR TODOS OS TESTES
# ============================================

if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("     ODINENX v2.0 - TESTES DE SIMULAÇÃO")
    print("🚀"*30)
    
    # Executar simulação de sala
    sim = run_simulation()
    
    # Testar efeitos de celebração
    effects = test_celebration_effects()
    
    # Testar loja de customização
    store = test_customization_store()
    
    print("\n\n" + "✅"*30)
    print("     TODOS OS TESTES CONCLUÍDOS!")
    print("✅"*30)
    
    print("""
    
    📋 PRÓXIMOS PASSOS DE IMPLEMENTAÇÃO:
    
    1. Criar tabelas no Supabase baseadas nos modelos testados
    2. Implementar componentes Vue:
       - GameRoom.vue (sala principal)
       - LiveChat.vue (chat em tempo real)
       - OddsPanel.vue (painel de odds)
       - UserList.vue (lista de usuários ordenada)
       - CelebrationOverlay.vue (efeitos de celebração)
    
    3. Configurar Supabase Realtime para:
       - Mensagens do chat
       - Atualização de placar
       - Status das odds
       - Presença de usuários
    
    4. Criar sistema de planos no Stripe:
       - Basic: R$19.90
       - Pro: R$49.90
       - Elite: R$99.90
    
    5. Implementar loja de customização para Elite
    
    """)
