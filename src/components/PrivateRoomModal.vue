<script setup>
/**
 * 🔒 PrivateRoomModal.vue - Criar/Entrar em Sala Privada
 * ODINENX v2.0
 */

import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameRoom } from '../lib/useGameRoom'
import { getMaxPrivateRooms } from '../lib/stripe'

const props = defineProps({
  userId: { type: String, required: true },
  userPlan: { type: String, default: 'free' },
  username: { type: String, default: '' },
  game: { type: Object, default: null }, // Jogo selecionado
  currentPrivateRooms: { type: Number, default: 0 }
})

const emit = defineEmits(['close', 'created', 'joined'])

const router = useRouter()
const { createPrivateRoom, joinPrivateRoom, isLoading, error } = useGameRoom()

// State
const activeTab = ref('join') // 'join' ou 'create'
const joinCode = ref('')
const roomName = ref('')
const maxUsers = ref(10)
const notification = ref({ type: '', message: '' })

// Computed
const maxPrivateRooms = computed(() => getMaxPrivateRooms(props.userPlan))

const canCreateRoom = computed(() => {
  if (maxPrivateRooms.value === 0) return false
  if (maxPrivateRooms.value === -1) return true // Ilimitado
  return props.currentPrivateRooms < maxPrivateRooms.value
})

const remainingRooms = computed(() => {
  if (maxPrivateRooms.value === -1) return '∞'
  return maxPrivateRooms.value - props.currentPrivateRooms
})

// Gerar nome sugerido
const suggestedName = computed(() => {
  if (!props.game) return `Sala de ${props.username}`
  return `${props.game.home_team} x ${props.game.away_team}`
})

// Handlers
async function handleJoin() {
  if (!joinCode.value.trim()) {
    showNotification('error', 'Digite o código da sala')
    return
  }
  
  const success = await joinPrivateRoom(joinCode.value.toUpperCase(), props.userId, {
    username: props.username,
    plan: props.userPlan
  })
  
  if (success) {
    emit('joined', { code: joinCode.value })
    // Navegar para sala (seria necessário buscar o roomId)
    // router.push(`/live/${roomId}`)
  } else {
    showNotification('error', 'Código inválido ou sala não encontrada')
  }
}

async function handleCreate() {
  if (!canCreateRoom.value) {
    showNotification('error', 'Você atingiu o limite de salas privadas')
    return
  }
  
  if (!props.game) {
    showNotification('error', 'Selecione um jogo primeiro')
    return
  }
  
  const room = await createPrivateRoom(props.userId, props.userPlan, {
    fixture_id: props.game.fixture_id,
    home_team: props.game.home_team,
    away_team: props.game.away_team,
    home_logo: props.game.home_team_logo,
    away_logo: props.game.away_team_logo,
    league: props.game.league,
    name: roomName.value || suggestedName.value,
    max_users: maxUsers.value
  })
  
  if (room) {
    // Copiar código
    await navigator.clipboard.writeText(room.private_code)
    
    emit('created', { 
      room, 
      code: room.private_code 
    })
    
    showNotification('success', `Sala criada! Código: ${room.private_code}`)
    
    // Navegar para sala após 1.5s
    setTimeout(() => {
      router.push(`/live/${room.id}`)
    }, 1500)
  }
}

function showNotification(type, message) {
  notification.value = { type, message }
  setTimeout(() => notification.value = { type: '', message: '' }, 3000)
}

function copyCode(code) {
  navigator.clipboard.writeText(code)
  showNotification('success', 'Código copiado!')
}
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <!-- Header -->
      <div class="modal-header">
        <h2>🔒 Sala Privada</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      
      <!-- Tabs -->
      <div class="tabs">
        <button 
          class="tab" 
          :class="{ active: activeTab === 'join' }"
          @click="activeTab = 'join'"
        >
          🔑 Entrar
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'create' }"
          @click="activeTab = 'create'"
          :disabled="maxPrivateRooms === 0"
        >
          ➕ Criar
        </button>
      </div>
      
      <!-- Join Tab -->
      <div v-if="activeTab === 'join'" class="tab-content">
        <p class="description">
          Digite o código de 6 dígitos da sala para entrar
        </p>
        
        <div class="code-input-wrapper">
          <input
            type="text"
            v-model="joinCode"
            placeholder="ABC123"
            maxlength="6"
            class="code-input"
            @keyup.enter="handleJoin"
          />
        </div>
        
        <button 
          class="btn-primary"
          :disabled="isLoading || joinCode.length < 6"
          @click="handleJoin"
        >
          <span v-if="isLoading" class="spinner"></span>
          <span v-else>Entrar na Sala</span>
        </button>
      </div>
      
      <!-- Create Tab -->
      <div v-else class="tab-content">
        <!-- No permission -->
        <div v-if="maxPrivateRooms === 0" class="no-permission">
          <div class="lock-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h3>Recurso Premium</h3>
          <p>Salas privadas estão disponíveis a partir do plano Pro</p>
          <router-link to="/pricing" class="upgrade-btn">
            <span>Ver Planos</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </router-link>
        </div>
        
        <!-- Has permission -->
        <template v-else>
          <p class="description">
            Crie uma sala privada e convide seus amigos
          </p>
          
          <!-- Remaining rooms -->
          <div class="remaining-info">
            <span>Salas disponíveis:</span>
            <span class="remaining-count">{{ remainingRooms }}</span>
          </div>
          
          <!-- Game Selected -->
          <div v-if="game" class="game-selected">
            <img :src="game.home_team_logo" :alt="game.home_team" class="team-logo" />
            <span>{{ game.home_team }} x {{ game.away_team }}</span>
            <img :src="game.away_team_logo" :alt="game.away_team" class="team-logo" />
          </div>
          
          <div v-else class="no-game">
            ⚠️ Selecione um jogo para criar a sala
          </div>
          
          <!-- Room Name -->
          <div class="form-group">
            <label>Nome da Sala (opcional)</label>
            <input
              type="text"
              v-model="roomName"
              :placeholder="suggestedName"
              class="text-input"
            />
          </div>
          
          <!-- Max Users -->
          <div class="form-group">
            <label>Máximo de Participantes</label>
            <div class="range-wrapper">
              <input
                type="range"
                v-model.number="maxUsers"
                min="2"
                max="50"
                class="range-input"
              />
              <span class="range-value">{{ maxUsers }}</span>
            </div>
          </div>
          
          <button 
            class="btn-primary"
            :disabled="isLoading || !canCreateRoom || !game"
            @click="handleCreate"
          >
            <span v-if="isLoading" class="spinner"></span>
            <span v-else>🔒 Criar Sala Privada</span>
          </button>
          
          <p class="hint">
            💡 Um código será gerado automaticamente para compartilhar
          </p>
        </template>
      </div>
      
      <!-- Error -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      
      <!-- Notification -->
      <Transition name="slide">
        <div 
          v-if="notification.message" 
          class="notification"
          :class="notification.type"
        >
          {{ notification.message }}
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 24px;
  width: 100%;
  max-width: 450px;
  border: 1px solid rgba(255,255,255,0.1);
  position: relative;
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.3rem;
}

.close-btn {
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255,68,68,0.3);
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.tab {
  flex: 1;
  background: transparent;
  border: none;
  color: #888;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.tab:hover:not(:disabled) {
  color: white;
  background: rgba(255,255,255,0.05);
}

.tab.active {
  color: #ffd700;
  background: rgba(255,215,0,0.1);
  border-bottom: 2px solid #ffd700;
}

.tab:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Tab Content */
.tab-content {
  padding: 2rem;
}

.description {
  color: #888;
  text-align: center;
  margin: 0 0 1.5rem 0;
}

/* Code Input */
.code-input-wrapper {
  margin-bottom: 1.5rem;
}

.code-input {
  width: 100%;
  padding: 1.25rem;
  border: 2px solid rgba(255,255,255,0.2);
  border-radius: 12px;
  background: rgba(255,255,255,0.05);
  color: white;
  font-size: 2rem;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.75rem;
  outline: none;
  font-family: 'Orbitron', monospace;
}

.code-input:focus {
  border-color: #ffd700;
}

.code-input::placeholder {
  color: #444;
  letter-spacing: 0.5rem;
}

/* Form Group */
.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  color: #888;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.text-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  background: rgba(255,255,255,0.05);
  color: white;
  font-size: 1rem;
  outline: none;
}

.text-input:focus {
  border-color: #ffd700;
}

/* Range */
.range-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.range-input {
  flex: 1;
  -webkit-appearance: none;
  height: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
  outline: none;
}

.range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: #ffd700;
  border-radius: 50%;
  cursor: pointer;
}

.range-value {
  min-width: 40px;
  text-align: center;
  font-weight: 600;
  color: #ffd700;
}

/* Game Selected */
.game-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: rgba(255,255,255,0.05);
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.team-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  background: linear-gradient(145deg, #1e293b, #0f172a);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.no-game {
  text-align: center;
  color: #ff8c00;
  padding: 1rem;
  background: rgba(255,140,0,0.1);
  border-radius: 10px;
  margin-bottom: 1.5rem;
}

/* Remaining */
.remaining-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(255,215,0,0.1);
  border-radius: 10px;
  margin-bottom: 1.5rem;
}

.remaining-count {
  font-weight: 700;
  color: #ffd700;
  font-size: 1.2rem;
}

/* No Permission - Premium Style */
.no-permission {
  text-align: center;
  padding: 2.5rem 1.5rem;
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 16px;
  margin-bottom: 1rem;
}

.no-permission .lock-icon-wrapper {
  width: 56px;
  height: 56px;
  margin: 0 auto 1rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-permission .lock-icon-wrapper svg {
  width: 24px;
  height: 24px;
  color: #8b5cf6;
}

.no-permission h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.5rem;
}

.no-permission p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.upgrade-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.upgrade-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

.upgrade-btn svg {
  width: 16px;
  height: 16px;
}

.upgrade-link {
  display: inline-block;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
}

/* Buttons */
.btn-primary {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 5px 20px rgba(255,215,0,0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0,0,0,0.3);
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Hint */
.hint {
  text-align: center;
  color: #666;
  font-size: 0.85rem;
  margin: 1rem 0 0 0;
}

/* Error */
.error-message {
  padding: 1rem 2rem;
  background: rgba(255,68,68,0.1);
  color: #ff4444;
  text-align: center;
}

/* Notification */
.notification {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 5px 20px rgba(0,0,0,0.3);
}

.notification.success {
  background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
  color: #000;
}

.notification.error {
  background: linear-gradient(135deg, #ff4444 0%, #ff6b6b 100%);
  color: white;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* Responsive */
@media (max-width: 480px) {
  .modal-content {
    max-width: 100%;
    margin: 0.5rem;
    border-radius: 16px;
  }
  
  .modal-header {
    padding: 1rem;
  }
  
  .tab-content {
    padding: 1rem;
  }
  
  .no-permission {
    padding: 2rem 1rem;
  }
  
  .no-permission .lock-icon-wrapper {
    width: 48px;
    height: 48px;
  }
  
  .no-permission .lock-icon-wrapper svg {
    width: 20px;
    height: 20px;
  }
  
  .no-permission h3 {
    font-size: 1rem;
  }
  
  .no-permission p {
    font-size: 0.85rem;
  }
  
  .upgrade-btn {
    padding: 0.6rem 1.2rem;
    font-size: 0.85rem;
  }
}
</style>
