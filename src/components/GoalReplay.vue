<script setup>
/**
 * 🎬 GoalReplay.vue - Replay de Gols
 * ODINENX v2.0
 * 
 * Usa Scorebat API para exibir replays de gols
 * Os replays têm delay legal de ~1-2 minutos
 */

import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  fixtureId: { type: [Number, String], required: true },
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

// State
const loading = ref(true)
const error = ref('')
const videos = ref([])
const currentVideo = ref(null)
const isPlaying = ref(false)

// Buscar replays
async function fetchReplays() {
  loading.value = true
  error.value = ''
  
  try {
    // Em produção, usaria a Scorebat API
    // const response = await fetch(`https://www.scorebat.com/video-api/v3/feed/?token=YOUR_TOKEN`)
    // const data = await response.json()
    
    // Mock para demonstração
    videos.value = [
      {
        id: 1,
        title: `⚽ GOL! ${props.homeTeam} marca`,
        thumbnail: 'https://via.placeholder.com/320x180/1a1a2e/ffd700?text=GOL+1',
        embed: '<iframe src="about:blank" width="100%" height="100%"></iframe>',
        minute: '23\'',
        scorer: 'Jogador 1',
        team: props.homeTeam
      },
      {
        id: 2,
        title: `⚽ GOL! ${props.awayTeam} empata`,
        thumbnail: 'https://via.placeholder.com/320x180/1a1a2e/ff4444?text=GOL+2',
        embed: '<iframe src="about:blank" width="100%" height="100%"></iframe>',
        minute: '45\'',
        scorer: 'Jogador 2',
        team: props.awayTeam
      },
      {
        id: 3,
        title: `⚽ GOL! ${props.homeTeam} vira`,
        thumbnail: 'https://via.placeholder.com/320x180/1a1a2e/00c853?text=GOL+3',
        embed: '<iframe src="about:blank" width="100%" height="100%"></iframe>',
        minute: '67\'',
        scorer: 'Jogador 3',
        team: props.homeTeam
      }
    ]
    
    if (videos.value.length > 0) {
      currentVideo.value = videos.value[0]
    }
  } catch (err) {
    console.error('Erro ao buscar replays:', err)
    error.value = 'Não foi possível carregar os replays'
  } finally {
    loading.value = false
  }
}

// Play video
function playVideo(video) {
  currentVideo.value = video
  isPlaying.value = true
}

// Watch for visibility
watch(() => props.visible, (visible) => {
  if (visible) {
    fetchReplays()
  } else {
    isPlaying.value = false
  }
})

// Auto-fetch on mount if visible
onMounted(() => {
  if (props.visible) {
    fetchReplays()
  }
})
</script>

<template>
  <Transition name="slide-up">
    <div v-if="visible" class="replay-panel">
      <!-- Header -->
      <div class="replay-header">
        <div class="header-info">
          <span class="replay-icon">🎬</span>
          <h3>Replays dos Gols</h3>
          <span class="delay-badge">~1-2 min delay</span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Buscando replays...</p>
      </div>
      
      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <span>❌</span>
        <p>{{ error }}</p>
        <button @click="fetchReplays">Tentar novamente</button>
      </div>
      
      <!-- Empty -->
      <div v-else-if="videos.length === 0" class="empty-state">
        <span>⚽</span>
        <p>Nenhum replay disponível ainda</p>
        <small>Os replays aparecem ~1-2 min após os gols</small>
      </div>
      
      <!-- Content -->
      <div v-else class="replay-content">
        <!-- Video Player -->
        <div class="video-player">
          <div v-if="isPlaying && currentVideo" class="player-wrapper">
            <!-- Em produção, usaria o embed real -->
            <div class="mock-player">
              <span>▶️</span>
              <p>{{ currentVideo.title }}</p>
              <small>Reproduzindo...</small>
            </div>
          </div>
          <div v-else class="player-placeholder">
            <img 
              v-if="currentVideo"
              :src="currentVideo.thumbnail" 
              :alt="currentVideo.title"
              class="thumbnail-large"
            />
            <button class="play-btn" @click="isPlaying = true">
              ▶️ Reproduzir
            </button>
          </div>
        </div>
        
        <!-- Video List -->
        <div class="video-list">
          <h4>Todos os Gols</h4>
          <div 
            v-for="video in videos" 
            :key="video.id"
            class="video-item"
            :class="{ active: currentVideo?.id === video.id }"
            @click="playVideo(video)"
          >
            <img :src="video.thumbnail" :alt="video.title" class="thumbnail" />
            <div class="video-info">
              <span class="minute">{{ video.minute }}</span>
              <span class="scorer">{{ video.scorer }}</span>
              <span class="team">{{ video.team }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Legal Notice -->
      <div class="legal-notice">
        <p>
          ⚠️ Replays fornecidos por parceiros oficiais com delay legal.
          Transmissão ao vivo não disponível.
        </p>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.replay-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 24px 24px 0 0;
  border: 1px solid rgba(255,255,255,0.1);
  border-bottom: none;
  max-height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

/* Header */
.replay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.replay-icon {
  font-size: 1.5rem;
}

.header-info h3 {
  margin: 0;
  font-size: 1.1rem;
}

.delay-badge {
  background: rgba(255,140,0,0.2);
  color: #ff8c00;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
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

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem;
  color: #888;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #ffd700;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
.error-state {
  text-align: center;
  padding: 2rem;
  color: #ff4444;
}

.error-state span {
  font-size: 2rem;
}

.error-state button {
  background: rgba(255,68,68,0.2);
  border: 1px solid rgba(255,68,68,0.3);
  color: #ff4444;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1rem;
}

/* Empty */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #888;
}

.empty-state span {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-state small {
  color: #666;
}

/* Content */
.replay-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Video Player */
.video-player {
  flex: 2;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.player-wrapper {
  width: 100%;
  height: 100%;
  min-height: 250px;
}

.mock-player {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
  border-radius: 12px;
}

.mock-player span {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.mock-player p {
  color: white;
  font-weight: 600;
}

.mock-player small {
  color: #888;
}

.player-placeholder {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 250px;
}

.thumbnail-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.play-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0,0,0,0.7);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 50px;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s;
}

.play-btn:hover {
  background: rgba(255,215,0,0.9);
  color: #000;
  transform: translate(-50%, -50%) scale(1.1);
}

/* Video List */
.video-list {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  border-left: 1px solid rgba(255,255,255,0.1);
}

.video-list h4 {
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
  color: #888;
}

.video-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 0.5rem;
}

.video-item:hover {
  background: rgba(255,255,255,0.05);
}

.video-item.active {
  background: rgba(255,215,0,0.1);
  border: 1px solid rgba(255,215,0,0.3);
}

.thumbnail {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 6px;
}

.video-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.25rem;
}

.minute {
  background: rgba(255,68,68,0.2);
  color: #ff4444;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.75rem;
  width: fit-content;
}

.scorer {
  font-weight: 600;
  font-size: 0.85rem;
}

.team {
  color: #888;
  font-size: 0.75rem;
}

/* Legal Notice */
.legal-notice {
  padding: 0.75rem 1rem;
  background: rgba(255,140,0,0.1);
  border-top: 1px solid rgba(255,140,0,0.2);
}

.legal-notice p {
  margin: 0;
  color: #ff8c00;
  font-size: 0.75rem;
  text-align: center;
}

/* Animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .replay-content {
    flex-direction: column;
  }
  
  .video-list {
    border-left: none;
    border-top: 1px solid rgba(255,255,255,0.1);
    max-height: 200px;
  }
}
</style>
