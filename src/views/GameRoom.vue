<script setup>
/**
 * 🏟️ GameRoom.vue - Sala de Jogo ao Vivo
 * ODINENX v2.0
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { useGameRoom } from '../lib/useGameRoom'
import { getSubscriptionStatus, plans } from '../lib/stripe'
import LiveChat from '../components/LiveChat.vue'
import OddsPanel from '../components/OddsPanel.vue'
import UserList from '../components/UserList.vue'
import CelebrationOverlay from '../components/CelebrationOverlay.vue'

const route = useRoute()
const router = useRouter()

// Composable
const {
  currentRoom,
  roomUsers,
  roomMessages,
  userOdds,
  reactions,
  isConnected,
  isLoading,
  error,
  celebrationEvent,
  viewersCount,
  sortedUsers,
  matchScore,
  isLive,
  joinRoom,
  leaveRoom,
  sendMessage,
  sendReaction,
  getPlanBadge
} = useGameRoom()

// State local
const user = ref(null)
const userProfile = ref(null)
const subscription = ref(null)
const showOddsSelector = ref(true)
const selectedOdds = ref([])
const chatInput = ref('')
const showUserList = ref(true)

// Reactions disponíveis
const availableReactions = ['⚽', '🔥', '😱', '👏', '🎉', '😭', '💪', '🙏']

onMounted(async () => {
  // Verificar autenticação
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  
  // Buscar perfil e plano
  const [profileData, subData] = await Promise.all([
    supabase.from('profiles').select('*').eq('id', user.value.id).single(),
    getSubscriptionStatus(user.value.id)
  ])
  
  userProfile.value = {
    ...profileData.data,
    plan: subData.plan || 'free'
  }
  subscription.value = subData
  
  // Se tiver roomId na URL, tentar entrar
  if (route.params.roomId) {
    showOddsSelector.value = false
    await handleJoinRoom()
  }
})

onUnmounted(() => {
  if (currentRoom.value && user.value) {
    leaveRoom(currentRoom.value.id, user.value.id)
  }
})

// Entrar na sala
async function handleJoinRoom() {
  if (!user.value || !userProfile.value) return
  
  const roomId = route.params.roomId
  const success = await joinRoom(roomId, user.value.id, userProfile.value, selectedOdds.value)
  
  if (success) {
    showOddsSelector.value = false
  }
}

// Enviar mensagem
async function handleSendMessage() {
  if (!chatInput.value.trim() || !currentRoom.value) return
  
  await sendMessage(
    currentRoom.value.id,
    user.value.id,
    userProfile.value,
    chatInput.value.trim()
  )
  
  chatInput.value = ''
}

// Enviar reação
async function handleReaction(reaction) {
  if (!currentRoom.value) return
  await sendReaction(currentRoom.value.id, user.value.id, reaction)
}

// Sair da sala
async function handleLeaveRoom() {
  if (currentRoom.value && user.value) {
    await leaveRoom(currentRoom.value.id, user.value.id)
    router.push('/live')
  }
}

// Computed para plano atual
const currentPlan = computed(() => {
  return plans[userProfile.value?.plan] || plans.free
})
</script>

<template>
  <div class="game-room-page">
    <!-- Loading -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner-large"></div>
      <p>Entrando na sala...</p>
    </div>
    
    <!-- Seletor de Odds (antes de entrar) -->
    <div v-else-if="showOddsSelector" class="odds-selector-modal">
      <div class="modal-content">
        <h2>🎯 Selecione suas Odds</h2>
        <p>Escolha os palpites que você quer acompanhar neste jogo</p>
        
        <OddsPanel 
          v-if="currentRoom"
          :room="currentRoom"
          :selectedOdds="selectedOdds"
          @update:selectedOdds="selectedOdds = $event"
          mode="select"
        />
        
        <div class="modal-actions">
          <button class="btn-secondary" @click="router.push('/live')">
            Cancelar
          </button>
          <button class="btn-primary" @click="handleJoinRoom">
            🚀 Entrar na Sala
          </button>
        </div>
      </div>
    </div>
    
    <!-- Sala Principal -->
    <div v-else-if="currentRoom" class="room-container">
      <!-- Header da Sala -->
      <header class="room-header">
        <button class="btn-back" @click="handleLeaveRoom">
          ← Sair
        </button>
        
        <div class="match-info">
          <div class="team home">
            <img :src="currentRoom.home_team_logo" :alt="currentRoom.home_team" class="team-logo" />
            <span class="team-name">{{ currentRoom.home_team }}</span>
          </div>
          
          <div class="score-container">
            <div class="score" :class="{ live: isLive }">
              {{ matchScore }}
            </div>
            <div class="minute" v-if="isLive">
              {{ currentRoom.minute }}'
            </div>
            <div class="status" :class="currentRoom.status">
              {{ currentRoom.status === 'live' ? '🔴 AO VIVO' : currentRoom.status }}
            </div>
          </div>
          
          <div class="team away">
            <img :src="currentRoom.away_team_logo" :alt="currentRoom.away_team" class="team-logo" />
            <span class="team-name">{{ currentRoom.away_team }}</span>
          </div>
        </div>
        
        <div class="viewers-count">
          <span class="eye-icon">👁️</span>
          {{ viewersCount }} assistindo
        </div>
      </header>
      
      <!-- Conteúdo Principal -->
      <div class="room-content">
        <!-- Painel de Odds -->
        <aside class="odds-sidebar" v-if="userOdds.length > 0">
          <h3>🎯 Suas Odds</h3>
          <OddsPanel 
            :room="currentRoom"
            :userOdds="userOdds.filter(o => o.user_id === user?.id)"
            mode="view"
          />
        </aside>
        
        <!-- Chat -->
        <main class="chat-area">
          <LiveChat
            :messages="roomMessages"
            :currentUser="user"
            :userPlan="userProfile?.plan"
            @send="handleSendMessage"
            v-model:input="chatInput"
          />
          
          <!-- Reações Rápidas -->
          <div class="quick-reactions">
            <button 
              v-for="reaction in availableReactions"
              :key="reaction"
              class="reaction-btn"
              @click="handleReaction(reaction)"
            >
              {{ reaction }}
            </button>
          </div>
        </main>
        
        <!-- Lista de Usuários -->
        <aside class="users-sidebar" v-if="showUserList">
          <div class="sidebar-header">
            <h3>👥 Na Sala</h3>
            <span class="count">{{ viewersCount }}</span>
          </div>
          <UserList :users="sortedUsers" :currentUserId="user?.id" />
        </aside>
      </div>
      
      <!-- Overlay de Celebração -->
      <CelebrationOverlay 
        v-if="celebrationEvent"
        :event="celebrationEvent"
        :userPlan="userProfile?.plan"
      />
      
      <!-- Reações Flutuantes -->
      <div class="floating-reactions">
        <TransitionGroup name="reaction">
          <span 
            v-for="r in reactions" 
            :key="r.id"
            class="floating-reaction"
            :style="{ left: Math.random() * 80 + 10 + '%' }"
          >
            {{ r.reaction }}
          </span>
        </TransitionGroup>
      </div>
    </div>
    
    <!-- Erro -->
    <div v-else-if="error" class="error-container">
      <h2>❌ Erro</h2>
      <p>{{ error }}</p>
      <button class="btn-primary" @click="router.push('/live')">
        Voltar
      </button>
    </div>
  </div>
</template>

<style scoped>
.game-room-page {
  min-height: 100vh;
  min-height: 100dvh;
  min-height: -webkit-fill-available;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
  color: white;
  -webkit-overflow-scrolling: touch;
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

/* Loading */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 1rem;
}

.spinner-large {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(255,255,255,0.1);
  border-top-color: #ffd700;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Seletor de Odds Modal */
.odds-selector-modal {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
}

.modal-content {
  background: #1e1e3f;
  border-radius: 20px;
  padding: 2rem;
  max-width: 600px;
  width: 100%;
  border: 1px solid rgba(255,255,255,0.1);
}

.modal-content h2 {
  margin-bottom: 0.5rem;
}

.modal-content p {
  color: #888;
  margin-bottom: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

/* Room Container */
.room-container {
  display: flex;
  display: -webkit-box;
  display: -webkit-flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  height: -webkit-fill-available;
}

/* Header */
.room-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: rgba(0,0,0,0.3);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.btn-back {
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: rgba(255,255,255,0.2);
}

.match-info {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.team {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.team-logo {
  width: 50px;
  height: 50px;
  object-fit: contain;
  background: linear-gradient(145deg, #1e293b, #0f172a);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.team-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.score-container {
  text-align: center;
}

.score {
  font-size: 2.5rem;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
}

.score.live {
  color: #ffd700;
  text-shadow: 0 0 20px rgba(255,215,0,0.5);
}

.minute {
  font-size: 1.2rem;
  color: #ff4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  margin-top: 0.25rem;
}

.status.live {
  background: #ff4444;
  color: white;
}

.viewers-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #888;
}

/* Content */
.room-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebars */
.odds-sidebar,
.users-sidebar {
  width: 280px;
  background: rgba(0,0,0,0.2);
  border-right: 1px solid rgba(255,255,255,0.1);
  padding: 1rem;
  overflow-y: auto;
}

.users-sidebar {
  border-right: none;
  border-left: 1px solid rgba(255,255,255,0.1);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
}

.sidebar-header .count {
  background: rgba(255,255,255,0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
}

/* Chat Area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Quick Reactions */
.quick-reactions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.1);
}

.reaction-btn {
  font-size: 1.5rem;
  padding: 0.5rem;
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.reaction-btn:hover {
  background: rgba(255,255,255,0.2);
  transform: scale(1.2);
}

/* Floating Reactions */
.floating-reactions {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.floating-reaction {
  position: absolute;
  font-size: 2rem;
  animation: float-up 3s ease-out forwards;
  bottom: 100px;
}

@keyframes float-up {
  0% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateY(-300px) scale(1.5);
  }
}

.reaction-enter-active,
.reaction-leave-active {
  transition: all 0.3s ease;
}

.reaction-enter-from {
  opacity: 0;
  transform: scale(0);
}

.reaction-leave-to {
  opacity: 0;
}

/* Error */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 1rem;
}

/* Buttons */
.btn-primary {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255,215,0,0.4);
}

.btn-secondary {
  background: transparent;
  color: white;
  padding: 0.75rem 1.5rem;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(255,255,255,0.1);
}

/* Responsive */
@media (max-width: 1024px) {
  .odds-sidebar {
    display: none;
  }
}

@media (max-width: 768px) {
  .users-sidebar {
    display: none;
  }
  
  .room-header {
    flex-wrap: wrap;
    padding: 1rem;
  }
  
  .match-info {
    order: 1;
    width: 100%;
    justify-content: center;
    margin-top: 1rem;
  }
  
  .team-logo {
    width: 40px;
    height: 40px;
  }
  
  .score {
    font-size: 2rem;
  }
}
</style>
