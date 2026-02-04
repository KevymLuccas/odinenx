<script setup>
/**
 * 😄 ReactionBar.vue - Barra de Reações Rápidas
 * ODINENX v2.0
 * 
 * Permite usuários enviar reações rápidas durante jogos
 */

import { ref, computed } from 'vue'

const props = defineProps({
  userPlan: { type: String, default: 'free' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['react'])

// Reações disponíveis por categoria
const reactionCategories = {
  emotions: [
    { emoji: '🔥', name: 'Fogo' },
    { emoji: '😱', name: 'Chocado' },
    { emoji: '😂', name: 'Rindo' },
    { emoji: '😭', name: 'Chorando' },
    { emoji: '🤯', name: 'Mente explodindo' },
    { emoji: '😤', name: 'Bravo' }
  ],
  sports: [
    { emoji: '⚽', name: 'Gol' },
    { emoji: '🥅', name: 'Goleiro' },
    { emoji: '🏃', name: 'Correndo' },
    { emoji: '🦶', name: 'Chute' },
    { emoji: '🎯', name: 'Na trave' },
    { emoji: '🟨', name: 'Amarelo' },
    { emoji: '🟥', name: 'Vermelho' }
  ],
  celebration: [
    { emoji: '🎉', name: 'Festa' },
    { emoji: '🏆', name: 'Troféu' },
    { emoji: '👏', name: 'Palmas' },
    { emoji: '💪', name: 'Força' },
    { emoji: '🙌', name: 'Celebrar' },
    { emoji: '🫡', name: 'Respeito' }
  ],
  money: [
    { emoji: '💰', name: 'Dinheiro' },
    { emoji: '💸', name: 'Voando' },
    { emoji: '🤑', name: 'Rico' },
    { emoji: '📈', name: 'Subindo' },
    { emoji: '📉', name: 'Caindo' },
    { emoji: '💎', name: 'Diamante' }
  ]
}

// State
const showPicker = ref(false)
const activeCategory = ref('emotions')
const recentReactions = ref(['🔥', '😱', '⚽', '💰', '🎉', '😂'])

// Quick reactions (always visible)
const quickReactions = computed(() => recentReactions.value.slice(0, 6))

// Send reaction
function sendReaction(emoji) {
  if (props.disabled) return
  
  emit('react', emoji)
  
  // Update recent reactions
  if (!recentReactions.value.includes(emoji)) {
    recentReactions.value = [emoji, ...recentReactions.value.slice(0, 5)]
  }
  
  // Close picker
  showPicker.value = false
}

// Toggle picker
function togglePicker() {
  showPicker.value = !showPicker.value
}
</script>

<template>
  <div class="reaction-bar-wrapper">
    <!-- Quick Reactions -->
    <div class="quick-reactions">
      <button
        v-for="emoji in quickReactions"
        :key="emoji"
        class="reaction-btn"
        :class="{ disabled: disabled }"
        :disabled="disabled"
        @click="sendReaction(emoji)"
      >
        {{ emoji }}
      </button>
      
      <button 
        class="more-btn"
        :class="{ active: showPicker }"
        @click="togglePicker"
      >
        <span v-if="showPicker">✕</span>
        <span v-else>+</span>
      </button>
    </div>
    
    <!-- Full Picker -->
    <Transition name="slide">
      <div v-if="showPicker" class="reaction-picker">
        <!-- Categories -->
        <div class="picker-categories">
          <button
            v-for="(reactions, category) in reactionCategories"
            :key="category"
            class="category-btn"
            :class="{ active: activeCategory === category }"
            @click="activeCategory = category"
          >
            {{ reactions[0].emoji }}
          </button>
        </div>
        
        <!-- Reactions Grid -->
        <div class="picker-grid">
          <button
            v-for="reaction in reactionCategories[activeCategory]"
            :key="reaction.emoji"
            class="picker-reaction"
            :title="reaction.name"
            @click="sendReaction(reaction.emoji)"
          >
            {{ reaction.emoji }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.reaction-bar-wrapper {
  position: relative;
}

/* Quick Reactions */
.quick-reactions {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 50px;
  backdrop-filter: blur(10px);
}

.reaction-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reaction-btn:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.2);
}

.reaction-btn:active:not(.disabled) {
  transform: scale(0.9);
}

.reaction-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.more-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 215, 0, 0.2);
  border-radius: 50%;
  color: #ffd700;
  font-size: 1.25rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.more-btn:hover {
  background: rgba(255, 215, 0, 0.3);
  transform: scale(1.1);
}

.more-btn.active {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
}

/* Reaction Picker */
.reaction-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  margin-bottom: 0.5rem;
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  backdrop-filter: blur(20px);
}

/* Categories */
.picker-categories {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.category-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  background: transparent;
  font-size: 1.25rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
  opacity: 0.5;
}

.category-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  opacity: 0.8;
}

.category-btn.active {
  background: rgba(255, 215, 0, 0.1);
  opacity: 1;
}

/* Grid */
.picker-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.25rem;
  padding: 0.75rem;
}

.picker-reaction {
  width: 100%;
  aspect-ratio: 1;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.picker-reaction:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.2);
}

/* Animation */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
