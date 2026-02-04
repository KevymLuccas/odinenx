# ODINENX - Plataforma de Apostas Sociais v2.0

## 🎯 Sobre

ODINENX é uma plataforma SaaS de apostas esportivas com experiência social integrada. Os usuários podem acompanhar jogos ao vivo em salas com chat em tempo real, compartilhar odds e celebrar juntos.

## 🚀 Novidades v2.0

### Salas ao Vivo
- 🏟️ Salas de jogos com placar em tempo real
- 💬 Chat ao vivo com emojis, GIFs e stickers
- 👥 Lista de usuários com badges por plano
- 🎉 Celebrações animadas quando há gols
- 🔒 Salas privadas com código de convite
- 🎬 Replays de gols (com delay legal)

### Sistema de Planos
| Plano | Preço | Badge | Recursos |
|-------|-------|-------|----------|
| Free | R$ 0 | - | Chat texto, 3 análises/dia |
| Basic | R$ 19,90 | 🥉 | + Emojis, 1 sala privada |
| Pro | R$ 49,90 | ⭐ | + GIFs, 5 salas privadas, IA |
| Elite | R$ 99,90 | 👑 | + Stickers, salas ilimitadas, loja |

### Loja de Customização (Elite)
- ✨ Efeitos visuais
- 🎨 Cores personalizadas
- 🖼️ Molduras de avatar
- 🎉 Celebrações exclusivas
- 🔊 Sons personalizados

## 📁 Estrutura

```
src/
├── components/
│   ├── LiveChat.vue          # Chat em tempo real
│   ├── OddsPanel.vue         # Painel de odds
│   ├── UserList.vue          # Lista de usuários
│   ├── CelebrationOverlay.vue # Efeitos de celebração
│   ├── CustomizationStore.vue # Loja Elite
│   ├── PrivateRoomModal.vue  # Modal sala privada
│   ├── GoalReplay.vue        # Replays de gols
│   ├── FloatingReactions.vue # Reações flutuantes
│   ├── ReactionBar.vue       # Barra de reações
│   └── LiveScore.vue         # Placar ao vivo
├── views/
│   ├── LiveRooms.vue         # Lista de jogos ao vivo
│   ├── GameRoom.vue          # Sala do jogo
│   └── PricingV2.vue         # Nova página de preços
├── lib/
│   ├── useGameRoom.js        # Composable de salas
│   ├── stripe.js             # Planos e pagamento
│   └── supabase.js           # Cliente Supabase
└── types/
    └── index.ts              # Tipos TypeScript

api/
├── live-odds.js              # API de odds em tempo real
├── live-fixtures.js          # API de jogos ao vivo
├── fixture-events.js         # API de eventos do jogo
└── goal-replays.js           # API de replays (Scorebat)

supabase/migrations/
└── 012_live_rooms_system.sql # Schema das salas
```

## 🔧 Instalação

```bash
# Instalar dependências
npm install

# Desenvolvimento
npm run dev

# Build
npm run build
```

## ⚙️ Variáveis de Ambiente

```env
VITE_SUPABASE_URL=sua_url
VITE_SUPABASE_ANON_KEY=sua_key
VITE_STRIPE_PUBLIC_KEY=sua_key_stripe
API_FOOTBALL_KEY=sua_api_football
ODDS_API_KEY=sua_odds_api
SCOREBAT_TOKEN=seu_token_scorebat
```

## 🛠️ Tecnologias

- **Frontend**: Vue 3 + Vite + Vue Router
- **Backend**: Supabase (PostgreSQL + Realtime)
- **Pagamentos**: Stripe
- **APIs**: 
  - API Football (jogos/placar)
  - The Odds API (odds)
  - Scorebat (replays)

## 📊 Supabase Setup

Execute a migration `012_live_rooms_system.sql` para criar as tabelas:
- `game_rooms` - Salas de jogos
- `room_users` - Usuários nas salas
- `room_messages` - Mensagens do chat
- `user_odds` - Odds selecionadas
- `room_reactions` - Reações
- `user_customizations` - Customizações Elite
- `store_items` - Itens da loja

## 🔒 Políticas RLS

Todas as tabelas têm Row Level Security (RLS) configurado:
- Usuários só podem ver/editar seus próprios dados
- Mensagens são visíveis para todos na sala
- Apenas o owner pode gerenciar salas privadas

## 📱 Rotas

```
/live           - Lista de jogos ao vivo
/live/:roomId   - Sala do jogo
/pricing        - Planos e preços
/dashboard      - Dashboard do usuário
```

## 📄 Licença

Proprietary - ODINENX © 2025

