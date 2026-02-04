<script setup>
/**
 * 🎉 CelebrationOverlay.vue - Efeitos de celebração por plano
 * ODINENX v2.0
 */

import { ref, computed, watch, onMounted } from 'vue'
import { plans, getCelebrationEffect } from '../lib/stripe'

const props = defineProps({
  event: {
    type: Object,
    default: null
  },
  userPlan: {
    type: String,
    default: 'free'
  }
})

const emit = defineEmits(['complete'])

const isVisible = ref(false)
const confettiParticles = ref([])
const showMessage = ref(false)

// Configurações de celebração por plano
const celebrationConfig = {
  free: {
    name: 'Confete Simples',
    particleCount: 30,
    duration: 2000,
    colors: ['#ffd700', '#ff8c00'],
    sound: null,
    showPopup: false,
    highlightDuration: 0
  },
  basic: {
    name: 'Confete Colorido',
    particleCount: 60,
    duration: 3000,
    colors: ['#ffd700', '#ff8c00', '#ff4444', '#44ff44', '#4444ff', '#ff44ff'],
    sound: 'celebration_basic.mp3',
    showPopup: false,
    highlightDuration: 2000
  },
  pro: {
    name: 'Animação Premium',
    particleCount: 100,
    duration: 4000,
    colors: ['#ffd700', '#ff8c00', '#ff4444', '#44ff44', '#4444ff', '#ff44ff', '#00ffff'],
    sound: 'celebration_pro.mp3',
    showPopup: true,
    highlightDuration: 3000,
    extraEffects: ['stars', 'fireworks']
  },
  elite: {
    name: 'Full Customizado',
    particleCount: 150,
    duration: 5000,
    colors: ['#ffd700', '#ff8c00', '#ff4444', '#44ff44', '#4444ff', '#ff44ff', '#00ffff', '#ffffff'],
    sound: 'celebration_elite.mp3',
    showPopup: true,
    highlightDuration: 5000,
    extraEffects: ['stars', 'fireworks', 'spotlight'],
    customizable: true
  }
}

const config = computed(() => {
  return celebrationConfig[props.userPlan] || celebrationConfig.free
})

// Gerar partículas de confete
function generateConfetti() {
  const particles = []
  const count = config.value.particleCount
  
  for (let i = 0; i < count; i++) {
    particles.push({
      id: i,
      x: Math.random() * 100,
      delay: Math.random() * 1000,
      duration: 2000 + Math.random() * 2000,
      color: config.value.colors[Math.floor(Math.random() * config.value.colors.length)],
      size: 8 + Math.random() * 12,
      rotation: Math.random() * 360,
      type: Math.random() > 0.5 ? 'square' : 'circle'
    })
  }
  
  return particles
}

// Iniciar celebração
function startCelebration() {
  isVisible.value = true
  confettiParticles.value = generateConfetti()
  
  // Mostrar mensagem após pequeno delay
  setTimeout(() => {
    showMessage.value = true
  }, 300)
  
  // Tocar som (se disponível e permitido)
  if (config.value.sound) {
    playSound(config.value.sound)
  }
  
  // Finalizar após duração
  setTimeout(() => {
    isVisible.value = false
    showMessage.value = false
    confettiParticles.value = []
    emit('complete')
  }, config.value.duration)
}

// Tocar som
function playSound(soundFile) {
  try {
    const audio = new Audio(`/sounds/${soundFile}`)
    audio.volume = 0.5
    audio.play().catch(() => {
      // Autoplay bloqueado pelo navegador
      console.log('Som bloqueado pelo navegador')
    })
  } catch (e) {
    console.log('Erro ao tocar som:', e)
  }
}

// Watch para evento de celebração
watch(() => props.event, (newEvent) => {
  if (newEvent) {
    startCelebration()
  }
}, { immediate: true })

// Mensagem baseada no tipo de evento
const celebrationMessage = computed(() => {
  if (!props.event) return ''
  
  if (props.event.type === 'goal') {
    return '⚽ GOOOOOL!'
  }
  
  if (props.event.type === 'odd_won') {
    return '🎉 VOCÊ ACERTOU!'
  }
  
  return '🎊 PARABÉNS!'
})

const subMessage = computed(() => {
  if (!props.event) return ''
  
  if (props.event.type === 'odd_won') {
    return `${props.event.data.odd_type} @ ${props.event.data.odd_value}`
  }
  
  return ''
})
</script>

<template>
  <Transition name="celebration">
    <div 
      v-if="isVisible" 
      class="celebration-overlay"
      :class="userPlan"
    >
      <!-- Confetti -->
      <div class="confetti-container">
        <div
          v-for="particle in confettiParticles"
          :key="particle.id"
          class="confetti-particle"
          :class="particle.type"
          :style="{
            left: particle.x + '%',
            animationDelay: particle.delay + 'ms',
            animationDuration: particle.duration + 'ms',
            backgroundColor: particle.color,
            width: particle.size + 'px',
            height: particle.size + 'px',
            transform: `rotate(${particle.rotation}deg)`
          }"
        ></div>
      </div>
      
      <!-- Extra Effects (Pro/Elite) -->
      <template v-if="config.extraEffects?.includes('stars')">
        <div class="stars-container">
          <div 
            v-for="i in 20" 
            :key="'star-' + i"
            class="star"
            :style="{
              left: Math.random() * 100 + '%',
              top: Math.random() * 100 + '%',
              animationDelay: Math.random() * 2 + 's'
            }"
          >⭐</div>
        </div>
      </template>
      
      <template v-if="config.extraEffects?.includes('fireworks')">
        <div class="fireworks-container">
          <div 
            v-for="i in 5" 
            :key="'fw-' + i"
            class="firework"
            :style="{
              left: 10 + i * 20 + '%',
              animationDelay: i * 0.3 + 's'
            }"
          ></div>
        </div>
      </template>
      
      <!-- Spotlight (Elite) -->
      <div v-if="config.extraEffects?.includes('spotlight')" class="spotlight"></div>
      
      <!-- Message Popup -->
      <Transition name="popup">
        <div v-if="showMessage" class="message-popup" :class="userPlan">
          <div class="message-main">{{ celebrationMessage }}</div>
          <div class="message-sub" v-if="subMessage">{{ subMessage }}</div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
.celebration-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 9999;
  overflow: hidden;
}

/* Confetti Container */
.confetti-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  overflow: hidden;
}

/* Confetti Particle */
.confetti-particle {
  position: absolute;
  top: -20px;
  animation: confetti-fall linear forwards;
  opacity: 0.9;
}

.confetti-particle.square {
  border-radius: 2px;
}

.confetti-particle.circle {
  border-radius: 50%;
}

@keyframes confetti-fall {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(100vh) rotate(720deg);
    opacity: 0;
  }
}

/* Stars */
.stars-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.star {
  position: absolute;
  font-size: 1.5rem;
  animation: star-twinkle 1s ease-in-out infinite;
}

@keyframes star-twinkle {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.3);
  }
}

/* Fireworks */
.fireworks-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.firework {
  position: absolute;
  top: 30%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ffd700;
  animation: firework-explode 1.5s ease-out forwards;
}

@keyframes firework-explode {
  0% {
    transform: scale(1);
    box-shadow: 
      0 0 0 0 rgba(255,215,0,1),
      0 0 0 0 rgba(255,140,0,1),
      0 0 0 0 rgba(255,68,68,1);
  }
  50% {
    transform: scale(1.5);
    box-shadow: 
      50px -50px 0 2px rgba(255,215,0,0.8),
      -50px -50px 0 2px rgba(255,140,0,0.8),
      0 -70px 0 2px rgba(255,68,68,0.8),
      70px 0 0 2px rgba(68,255,68,0.8),
      -70px 0 0 2px rgba(68,68,255,0.8),
      50px 50px 0 2px rgba(255,68,255,0.8),
      -50px 50px 0 2px rgba(0,255,255,0.8);
  }
  100% {
    transform: scale(0);
    box-shadow: 
      100px -100px 0 0 rgba(255,215,0,0),
      -100px -100px 0 0 rgba(255,140,0,0),
      0 -140px 0 0 rgba(255,68,68,0),
      140px 0 0 0 rgba(68,255,68,0),
      -140px 0 0 0 rgba(68,68,255,0),
      100px 100px 0 0 rgba(255,68,255,0),
      -100px 100px 0 0 rgba(0,255,255,0);
  }
}

/* Spotlight (Elite) */
.spotlight {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 100%;
  background: radial-gradient(
    ellipse at top,
    rgba(255,215,0,0.3) 0%,
    transparent 70%
  );
  animation: spotlight-move 2s ease-in-out infinite alternate;
}

@keyframes spotlight-move {
  0% {
    transform: translateX(-50%) skewX(-10deg);
  }
  100% {
    transform: translateX(-50%) skewX(10deg);
  }
}

/* Message Popup */
.message-popup {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  padding: 2rem 4rem;
  border-radius: 20px;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255,215,0,0.5);
}

.message-popup.elite {
  background: linear-gradient(135deg, rgba(255,215,0,0.2) 0%, rgba(255,140,0,0.2) 100%);
  border-color: #ffd700;
  box-shadow: 0 0 50px rgba(255,215,0,0.5);
}

.message-popup.pro {
  border-color: #c0c0c0;
  box-shadow: 0 0 30px rgba(192,192,192,0.3);
}

.message-main {
  font-size: 3rem;
  font-weight: 700;
  color: #ffd700;
  text-shadow: 0 0 20px rgba(255,215,0,0.5);
  animation: message-bounce 0.5s ease;
}

.message-sub {
  font-size: 1.2rem;
  color: #ccc;
  margin-top: 0.5rem;
}

@keyframes message-bounce {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Transitions */
.celebration-enter-active,
.celebration-leave-active {
  transition: opacity 0.3s ease;
}

.celebration-enter-from,
.celebration-leave-to {
  opacity: 0;
}

.popup-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.popup-leave-active {
  transition: all 0.2s ease;
}

.popup-enter-from {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.5);
}

.popup-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(1.2);
}
</style>
