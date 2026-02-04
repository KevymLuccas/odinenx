<script setup>
/**
 * 📺 LiveRooms.vue - Lista de Salas ao Vivo
 * ODINENX v2.0
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { useGameRoom } from '../lib/useGameRoom'
import { getSubscriptionStatus, plans, getMaxPrivateRooms } from '../lib/stripe'

const router = useRouter()

const {
  fetchLiveRooms,
  createPrivateRoom,
  joinPrivateRoom,
  isLoading,
  error
} = useGameRoom()

// State
const user = ref(null)
const userPlan = ref('free')
const rooms = ref([])
const showPrivateModal = ref(false)
const privateCode = ref('')
const activeTab = ref('live') // 'live', 'scheduled', 'private'

// Jogos mockados (em produção, viriam da API Football)
const mockGames = [
  {
    id: 'room_1',
    fixture_id: 1001,
    home_team: 'Flamengo',
    away_team: 'Palmeiras',
    home_team_logo: 'https://media.api-sports.io/football/teams/127.png',
    away_team_logo: 'https://media.api-sports.io/football/teams/121.png',
    home_score: 2,
    away_score: 1,
    minute: 67,
    status: 'live',
    league: 'Brasileirão Série A',
    viewers_count: 342
  },
  {
    id: 'room_2',
    fixture_id: 1002,
    home_team: 'Real Madrid',
    away_team: 'Barcelona',
    home_team_logo: 'https://media.api-sports.io/football/teams/541.png',
    away_team_logo: 'https://media.api-sports.io/football/teams/529.png',
    home_score: 1,
    away_score: 1,
    minute: 34,
    status: 'live',
    league: 'La Liga',
    viewers_count: 1523
  },
  {
    id: 'room_3',
    fixture_id: 1003,
    home_team: 'Manchester City',
    away_team: 'Liverpool',
    home_team_logo: 'https://media.api-sports.io/football/teams/50.png',
    away_team_logo: 'https://media.api-sports.io/football/teams/40.png',
    home_score: 0,
    away_score: 0,
    minute: 0,
    status: 'scheduled',
    league: 'Premier League',
    start_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
    viewers_count: 0
  },
  {
    id: 'room_4',
    fixture_id: 1004,
    home_team: 'Corinthians',
    away_team: 'São Paulo',
    home_team_logo: 'https://media.api-sports.io/football/teams/131.png',
    away_team_logo: 'https://media.api-sports.io/football/teams/126.png',
    home_score: 0,
    away_score: 0,
    minute: 0,
    status: 'scheduled',
    league: 'Brasileirão Série A',
    start_time: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
    viewers_count: 0
  }
]

onMounted(async () => {
  // Verificar autenticação
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  
  // Buscar plano
  const sub = await getSubscriptionStatus(user.value.id)
  userPlan.value = sub.plan || 'free'
  
  // Buscar salas (usando mock por enquanto)
  rooms.value = mockGames
  
  // Em produção: 
  // rooms.value = await fetchLiveRooms()
})

// Computed
const liveRooms = computed(() => rooms.value.filter(r => r.status === 'live'))
const scheduledRooms = computed(() => rooms.value.filter(r => r.status === 'scheduled'))
const privateRooms = computed(() => rooms.value.filter(r => r.is_private && r.owner_id === user.value?.id))

const filteredRooms = computed(() => {
  switch (activeTab.value) {
    case 'live': return liveRooms.value
    case 'scheduled': return scheduledRooms.value
    case 'private': return privateRooms.value
    default: return rooms.value
  }
})

const canCreatePrivateRoom = computed(() => {
  const max = getMaxPrivateRooms(userPlan.value)
  if (max === -1) return true // Ilimitado
  if (max === 0) return false // Free não pode
  return privateRooms.value.length < max
})

// Formatar hora
function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Entrar na sala
function enterRoom(room) {
  router.push(`/live/${room.id}`)
}

// Entrar com código privado
async function handlePrivateJoin() {
  if (!privateCode.value.trim()) return
  
  const success = await joinPrivateRoom(privateCode.value, user.value.id, {
    username: user.value.email?.split('@')[0],
    plan: userPlan.value
  })
  
  if (success) {
    showPrivateModal.value = false
    privateCode.value = ''
  }
}

// Criar sala privada
async function handleCreatePrivate(game) {
  if (!canCreatePrivateRoom.value) {
    alert('Você atingiu o limite de salas privadas do seu plano')
    return
  }
  
  const room = await createPrivateRoom(user.value.id, userPlan.value, {
    fixture_id: game.fixture_id,
    home_team: game.home_team,
    away_team: game.away_team,
    home_logo: game.home_team_logo,
    away_logo: game.away_team_logo,
    league: game.league
  })
  
  if (room) {
    // Copiar código para clipboard
    navigator.clipboard.writeText(room.private_code)
    alert(`Sala criada! Código: ${room.private_code} (copiado para área de transferência)`)
    router.push(`/live/${room.id}`)
  }
}
</script>

<template>
  <div class="live-rooms-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-content">
        <router-link to="/dashboard" class="back-link">
          ← Voltar
        </router-link>
        <h1>🏟️ Jogos ao Vivo</h1>
        <p>Acompanhe partidas em tempo real com a comunidade</p>
      </div>
      
      <!-- Private Room Actions -->
      <div class="header-actions">
        <button 
          class="btn-private"
          @click="showPrivateModal = true"
        >
          🔑 Entrar com Código
        </button>
      </div>
    </header>
    
    <!-- Tabs -->
    <div class="tabs">
      <button 
        class="tab" 
        :class="{ active: activeTab === 'live' }"
        @click="activeTab = 'live'"
      >
        🔴 Ao Vivo ({{ liveRooms.length }})
      </button>
      <button 
        class="tab" 
        :class="{ active: activeTab === 'scheduled' }"
        @click="activeTab = 'scheduled'"
      >
        📅 Em Breve ({{ scheduledRooms.length }})
      </button>
      <button 
        class="tab" 
        :class="{ active: activeTab === 'private' }"
        @click="activeTab = 'private'"
      >
        🔒 Minhas Salas ({{ privateRooms.length }})
      </button>
    </div>
    
    <!-- Loading -->
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>Carregando jogos...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="error">
      <p>❌ {{ error }}</p>
    </div>
    
    <!-- Rooms Grid -->
    <div v-else class="rooms-grid">
      <div 
        v-for="room in filteredRooms" 
        :key="room.id"
        class="room-card"
        :class="{ live: room.status === 'live' }"
        @click="enterRoom(room)"
      >
        <!-- Live Badge -->
        <div class="live-badge" v-if="room.status === 'live'">
          <span class="dot"></span>
          AO VIVO
        </div>
        
        <!-- League -->
        <div class="league">{{ room.league }}</div>
        
        <!-- Teams -->
        <div class="match">
          <div class="team">
            <img :src="room.home_team_logo" :alt="room.home_team" class="team-logo" />
            <span class="team-name">{{ room.home_team }}</span>
          </div>
          
          <div class="score-section">
            <template v-if="room.status === 'live'">
              <div class="score">
                {{ room.home_score }} - {{ room.away_score }}
              </div>
              <div class="minute">{{ room.minute }}'</div>
            </template>
            <template v-else>
              <div class="vs">VS</div>
              <div class="start-time">{{ formatTime(room.start_time) }}</div>
            </template>
          </div>
          
          <div class="team">
            <img :src="room.away_team_logo" :alt="room.away_team" class="team-logo" />
            <span class="team-name">{{ room.away_team }}</span>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="card-footer">
          <div class="viewers" v-if="room.viewers_count > 0">
            👁️ {{ room.viewers_count }} assistindo
          </div>
          
          <div class="actions">
            <button 
              class="btn-enter"
              @click.stop="enterRoom(room)"
            >
              Entrar
            </button>
            
            <button 
              v-if="room.status !== 'live' && canCreatePrivateRoom"
              class="btn-private-create"
              @click.stop="handleCreatePrivate(room)"
              title="Criar sala privada"
            >
              🔒
            </button>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-if="filteredRooms.length === 0" class="empty-state">
        <p v-if="activeTab === 'live'">Nenhum jogo ao vivo no momento</p>
        <p v-else-if="activeTab === 'scheduled'">Nenhum jogo agendado</p>
        <p v-else>Você não tem salas privadas</p>
      </div>
    </div>
    
    <!-- Private Room Modal -->
    <Teleport to="body">
      <div v-if="showPrivateModal" class="modal-overlay" @click="showPrivateModal = false">
        <div class="modal" @click.stop>
          <h2>🔑 Entrar em Sala Privada</h2>
          <p>Digite o código da sala para entrar</p>
          
          <input 
            type="text" 
            v-model="privateCode"
            placeholder="Ex: ABC123"
            class="code-input"
            @keyup.enter="handlePrivateJoin"
          />
          
          <div class="modal-actions">
            <button class="btn-secondary" @click="showPrivateModal = false">
              Cancelar
            </button>
            <button class="btn-primary" @click="handlePrivateJoin">
              Entrar
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.live-rooms-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
  color: white;
  padding: 2rem;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-content h1 {
  font-size: 2rem;
  margin: 0.5rem 0;
}

.header-content p {
  color: #888;
  margin: 0;
}

.back-link {
  color: #888;
  text-decoration: none;
  font-size: 0.9rem;
}

.back-link:hover {
  color: white;
}

.btn-private {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-private:hover {
  background: rgba(255,255,255,0.2);
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1rem;
}

.tab {
  background: transparent;
  border: none;
  color: #888;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.tab:hover {
  color: white;
  background: rgba(255,255,255,0.05);
}

.tab.active {
  color: #ffd700;
  background: rgba(255,215,0,0.1);
}

/* Loading */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
  color: #888;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #ffd700;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Rooms Grid */
.rooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

/* Room Card */
.room-card {
  background: rgba(255,255,255,0.05);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255,255,255,0.1);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.room-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255,215,0,0.3);
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.room-card.live {
  border-color: rgba(255,68,68,0.3);
}

.room-card.live::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #ff4444, #ff8844);
}

/* Live Badge */
.live-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #ff4444;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.live-badge .dot {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* League */
.league {
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 1rem;
}

/* Match */
.match {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.team {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.team-logo {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.team-name {
  font-size: 0.85rem;
  font-weight: 500;
  text-align: center;
}

.score-section {
  text-align: center;
}

.score {
  font-size: 1.8rem;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
}

.minute {
  color: #ff4444;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.vs {
  font-size: 1.2rem;
  color: #666;
  font-weight: 600;
}

.start-time {
  font-size: 0.9rem;
  color: #888;
  margin-top: 0.25rem;
}

/* Card Footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.viewers {
  font-size: 0.85rem;
  color: #888;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn-enter {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-enter:hover {
  transform: scale(1.05);
}

.btn-private-create {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-private-create:hover {
  background: rgba(255,255,255,0.2);
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem;
  color: #666;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1e1e3f;
  border-radius: 20px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  border: 1px solid rgba(255,255,255,0.1);
}

.modal h2 {
  margin: 0 0 0.5rem 0;
}

.modal p {
  color: #888;
  margin: 0 0 1.5rem 0;
}

.code-input {
  width: 100%;
  padding: 1rem;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  background: rgba(255,255,255,0.05);
  color: white;
  font-size: 1.5rem;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5rem;
  outline: none;
}

.code-input:focus {
  border-color: #ffd700;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-primary {
  flex: 1;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-secondary {
  flex: 1;
  background: transparent;
  color: white;
  padding: 0.75rem;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 8px;
  cursor: pointer;
}

/* Responsive */
@media (max-width: 768px) {
  .live-rooms-page {
    padding: 1rem;
  }
  
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .tab {
    white-space: nowrap;
  }
  
  .rooms-grid {
    grid-template-columns: 1fr;
  }
}
</style>
