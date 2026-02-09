<script setup>
/**
 * 🎭 FloatingReactions.vue - Reações Flutuantes
 * ODINENX v2.0
 * 
 * Exibe reações que flutuam na tela quando usuários reagem
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  reactions: {
    type: Array,
    default: () => []
    // Cada reação: { id, emoji, username, plan, timestamp }
  }
})

// State
const floatingReactions = ref([])
const containerRef = ref(null)

// Add reaction to floating display
function addFloatingReaction(reaction) {
  const id = `${reaction.id}_${Date.now()}`
  
  // Random position and animation
  const startX = Math.random() * 80 + 10 // 10% to 90%
  const drift = (Math.random() - 0.5) * 50 // -25px to +25px
  const duration = 2000 + Math.random() * 1000 // 2-3s
  const scale = 1 + Math.random() * 0.5 // 1x to 1.5x
  
  floatingReactions.value.push({
    ...reaction,
    floatId: id,
    startX,
    drift,
    duration,
    scale
  })
  
  // Remove after animation
  setTimeout(() => {
    floatingReactions.value = floatingReactions.value.filter(r => r.floatId !== id)
  }, duration)
}

// Watch for new reactions
watch(() => props.reactions, (newReactions) => {
  if (newReactions.length > 0) {
    const latestReaction = newReactions[newReactions.length - 1]
    addFloatingReaction(latestReaction)
  }
}, { deep: true })

// Get glow color based on plan
function getGlowColor(plan) {
  switch (plan) {
    case 'legend': return 'rgba(139, 92, 246, 0.9)'
    case 'ultra': return 'rgba(255, 215, 0, 0.8)'
    case 'pro': return 'rgba(192, 192, 192, 0.6)'
    case 'basic': return 'rgba(205, 127, 50, 0.5)'
    default: return 'transparent'
  }
}
</script>

<template>
  <div class="floating-reactions" ref="containerRef">
    <TransitionGroup name="float">
      <div
        v-for="reaction in floatingReactions"
        :key="reaction.floatId"
        class="floating-reaction"
        :class="reaction.plan"
        :style="{
          '--start-x': `${reaction.startX}%`,
          '--drift': `${reaction.drift}px`,
          '--duration': `${reaction.duration}ms`,
          '--scale': reaction.scale,
          '--glow-color': getGlowColor(reaction.plan)
        }"
      >
        <span class="emoji">{{ reaction.emoji }}</span>
        <span class="username" v-if="reaction.username">
          {{ reaction.username }}
        </span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.floating-reactions {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 100;
}

.floating-reaction {
  position: absolute;
  bottom: 20%;
  left: var(--start-x);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  animation: floatUp var(--duration) ease-out forwards;
}

@keyframes floatUp {
  0% {
    opacity: 1;
    transform: translateY(0) translateX(0) scale(var(--scale));
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translateY(-300px) translateX(var(--drift)) scale(calc(var(--scale) * 0.5));
  }
}

.emoji {
  font-size: 2.5rem;
  filter: drop-shadow(0 0 10px var(--glow-color));
  animation: pulse 0.3s ease-out;
}

@keyframes pulse {
  0% { transform: scale(0); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

.username {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(0, 0, 0, 0.5);
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  white-space: nowrap;
}

/* Plan-specific styles */
.floating-reaction.elite .emoji {
  animation: pulse 0.3s ease-out, eliteGlow 1s ease-in-out infinite;
}

@keyframes eliteGlow {
  0%, 100% { filter: drop-shadow(0 0 10px rgba(138, 43, 226, 0.8)); }
  50% { filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.8)); }
}

.floating-reaction.pro .emoji {
  filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.8));
}

.floating-reaction.basic .emoji {
  filter: drop-shadow(0 0 10px rgba(205, 127, 50, 0.6));
}

/* Transition */
.float-enter-active {
  transition: all 0.3s ease-out;
}

.float-leave-active {
  transition: all 0.3s ease-in;
}

.float-enter-from {
  opacity: 0;
  transform: scale(0);
}

.float-leave-to {
  opacity: 0;
}
</style>
