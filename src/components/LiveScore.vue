<script setup>
/**
 * 📊 LiveScore.vue - Placar ao Vivo
 * ODINENX v2.0
 * 
 * Exibe placar com atualizações em tempo real
 */

import { ref, watch, computed } from 'vue'

const props = defineProps({
  homeTeam: { type: String, required: true },
  awayTeam: { type: String, required: true },
  homeLogo: { type: String, default: '' },
  awayLogo: { type: String, default: '' },
  homeScore: { type: Number, default: 0 },
  awayScore: { type: Number, default: 0 },
  minute: { type: Number, default: 0 },
  status: { type: String, default: 'scheduled' }, // scheduled, live, halftime, finished
  league: { type: String, default: '' },
  events: { type: Array, default: () => [] } // [{type: 'goal', team: 'home', minute: 23}]
})

const emit = defineEmits(['showReplays'])

// State
const isGoalAnimation = ref(false)
const lastScorer = ref('')

// Watch for score changes (goals)
watch([() => props.homeScore, () => props.awayScore], ([newHome, newAway], [oldHome, oldAway]) => {
  if (newHome > (oldHome || 0)) {
    triggerGoalAnimation(props.homeTeam)
  } else if (newAway > (oldAway || 0)) {
    triggerGoalAnimation(props.awayTeam)
  }
})

function triggerGoalAnimation(team) {
  lastScorer.value = team
  isGoalAnimation.value = true
  
  setTimeout(() => {
    isGoalAnimation.value = false
  }, 3000)
}

// Status display
const statusDisplay = computed(() => {
  switch (props.status) {
    case 'scheduled': return 'A iniciar'
    case 'live': return `${props.minute}'`
    case 'halftime': return 'Intervalo'
    case 'finished': return 'Encerrado'
    case 'postponed': return 'Adiado'
    case 'cancelled': return 'Cancelado'
    default: return props.status
  }
})

const isLive = computed(() => props.status === 'live')
</script>

<template>
  <div 
    class="live-score"
    :class="{ 
      live: isLive, 
      goal: isGoalAnimation,
      finished: status === 'finished'
    }"
  >
    <!-- Goal Animation Overlay -->
    <Transition name="goal">
      <div v-if="isGoalAnimation" class="goal-overlay">
        <span class="goal-text">⚽ GOOOOOL!</span>
        <span class="scorer-text">{{ lastScorer }}</span>
      </div>
    </Transition>
    
    <!-- League -->
    <div class="league-info" v-if="league">
      <span class="league-name">{{ league }}</span>
      <span class="live-indicator" v-if="isLive">
        <span class="dot"></span>
        AO VIVO
      </span>
    </div>
    
    <!-- Score Board -->
    <div class="score-board">
      <!-- Home Team -->
      <div class="team home">
        <img 
          v-if="homeLogo" 
          :src="homeLogo" 
          :alt="homeTeam" 
          class="team-logo"
        />
        <div v-else class="team-placeholder">{{ homeTeam.charAt(0) }}</div>
        <span class="team-name">{{ homeTeam }}</span>
      </div>
      
      <!-- Score -->
      <div class="score-center">
        <div class="score-display">
          <span 
            class="score home-score"
            :class="{ highlight: homeScore > awayScore }"
          >
            {{ homeScore }}
          </span>
          <span class="score-separator">-</span>
          <span 
            class="score away-score"
            :class="{ highlight: awayScore > homeScore }"
          >
            {{ awayScore }}
          </span>
        </div>
        
        <div 
          class="match-status"
          :class="{ live: isLive }"
        >
          {{ statusDisplay }}
        </div>
      </div>
      
      <!-- Away Team -->
      <div class="team away">
        <img 
          v-if="awayLogo" 
          :src="awayLogo" 
          :alt="awayTeam" 
          class="team-logo"
        />
        <div v-else class="team-placeholder">{{ awayTeam.charAt(0) }}</div>
        <span class="team-name">{{ awayTeam }}</span>
      </div>
    </div>
    
    <!-- Match Events -->
    <div class="events" v-if="events.length > 0">
      <div 
        v-for="(event, index) in events.slice(-5)" 
        :key="index"
        class="event"
        :class="event.type"
      >
        <span class="event-minute">{{ event.minute }}'</span>
        <span class="event-icon">
          <template v-if="event.type === 'goal'">⚽</template>
          <template v-else-if="event.type === 'yellow'">🟨</template>
          <template v-else-if="event.type === 'red'">🟥</template>
          <template v-else-if="event.type === 'substitution'">🔄</template>
          <template v-else-if="event.type === 'var'">📺</template>
          <template v-else>📋</template>
        </span>
        <span class="event-text">{{ event.text }}</span>
      </div>
    </div>
    
    <!-- Replay Button -->
    <button 
      v-if="homeScore + awayScore > 0"
      class="replay-btn"
      @click="$emit('showReplays')"
    >
      🎬 Ver Replays
    </button>
  </div>
</template>

<style scoped>
.live-score {
  background: linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(22, 33, 62, 0.9) 100%);
  border-radius: 20px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.live-score.live {
  border-color: rgba(255, 68, 68, 0.3);
  box-shadow: 0 0 30px rgba(255, 68, 68, 0.1);
}

.live-score.live::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #ff4444, #ff8844, #ff4444);
  background-size: 200% 100%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 0%; }
}

.live-score.goal {
  animation: goalShake 0.5s ease-out;
}

@keyframes goalShake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-5px); }
  40% { transform: translateX(5px); }
  60% { transform: translateX(-3px); }
  80% { transform: translateX(3px); }
}

.live-score.finished {
  opacity: 0.8;
}

/* Goal Overlay */
.goal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 200, 83, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.goal-text {
  font-size: 2.5rem;
  font-weight: 900;
  color: white;
  text-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
  animation: goalPop 0.5s ease-out;
}

.scorer-text {
  font-size: 1.2rem;
  color: white;
  margin-top: 0.5rem;
  font-weight: 600;
}

@keyframes goalPop {
  0% { transform: scale(0); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.goal-enter-active {
  animation: goalFadeIn 0.3s ease-out;
}

.goal-leave-active {
  animation: goalFadeOut 0.5s ease-in;
}

@keyframes goalFadeIn {
  from { opacity: 0; transform: scale(0.5); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes goalFadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* League Info */
.league-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.league-name {
  color: #888;
  font-size: 0.85rem;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #ff4444;
  font-size: 0.75rem;
  font-weight: 600;
}

.live-indicator .dot {
  width: 8px;
  height: 8px;
  background: #ff4444;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Score Board */
.score-board {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.team {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.team-logo {
  width: 60px;
  height: 60px;
  object-fit: contain;
  background: linear-gradient(145deg, #1e293b, #0f172a);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.team-placeholder {
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: #888;
}

.team-name {
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Score Center */
.score-center {
  text-align: center;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score {
  font-size: 3rem;
  font-weight: 900;
  font-family: 'Orbitron', sans-serif;
  min-width: 50px;
  text-align: center;
}

.score.highlight {
  color: #00c853;
}

.score-separator {
  font-size: 2rem;
  color: #666;
}

.match-status {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #888;
}

.match-status.live {
  color: #ff4444;
  font-weight: 600;
}

/* Events */
.events {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.event {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: #aaa;
}

.event-minute {
  color: #666;
  min-width: 35px;
}

.event-icon {
  font-size: 1rem;
}

.event-text {
  flex: 1;
}

.event.goal {
  color: #00c853;
  font-weight: 600;
}

/* Replay Button */
.replay-btn {
  width: 100%;
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(255, 140, 0, 0.1);
  border: 1px solid rgba(255, 140, 0, 0.3);
  color: #ff8c00;
  border-radius: 10px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.replay-btn:hover {
  background: rgba(255, 140, 0, 0.2);
}

/* Responsive */
@media (max-width: 480px) {
  .live-score {
    padding: 1rem;
  }
  
  .team-logo,
  .team-placeholder {
    width: 45px;
    height: 45px;
  }
  
  .team-name {
    font-size: 0.8rem;
    max-width: 70px;
  }
  
  .score {
    font-size: 2rem;
  }
}
</style>
