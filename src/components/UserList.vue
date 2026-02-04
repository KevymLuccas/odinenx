<script setup>
/**
 * 👥 UserList.vue - Lista de Usuários na Sala
 * ODINENX v2.0
 */

import { computed } from 'vue'
import { plans, getPlanBadge, getPlanOrder } from '../lib/stripe'

const props = defineProps({
  users: {
    type: Array,
    default: () => []
  },
  currentUserId: {
    type: String,
    default: null
  }
})

// Usuários já vêm ordenados do composable, mas garantimos aqui também
const sortedUsers = computed(() => {
  return [...props.users].sort((a, b) => getPlanOrder(a.plan) - getPlanOrder(b.plan))
})

// Configurações visuais por plano
const planConfig = {
  elite: {
    badge: '👑',
    tag: 'ELITE',
    bgClass: 'elite-bg',
    glowClass: 'elite-glow',
    textClass: 'elite-text'
  },
  pro: {
    badge: '⭐',
    tag: 'PRO',
    bgClass: 'pro-bg',
    glowClass: 'pro-glow',
    textClass: 'pro-text'
  },
  basic: {
    badge: '🥉',
    tag: 'BASIC',
    bgClass: 'basic-bg',
    glowClass: '',
    textClass: 'basic-text'
  },
  free: {
    badge: '',
    tag: 'FREE',
    bgClass: '',
    glowClass: '',
    textClass: ''
  }
}

function getConfig(plan) {
  return planConfig[plan] || planConfig.free
}

function isCurrentUser(userId) {
  return userId === props.currentUserId
}
</script>

<template>
  <div class="user-list">
    <TransitionGroup name="user">
      <div 
        v-for="user in sortedUsers" 
        :key="user.user_id"
        class="user-item"
        :class="[
          getConfig(user.plan).bgClass,
          getConfig(user.plan).glowClass,
          { 'is-current': isCurrentUser(user.user_id) }
        ]"
      >
        <!-- Avatar -->
        <div class="user-avatar">
          <img 
            v-if="user.avatar_url" 
            :src="user.avatar_url" 
            :alt="user.username"
          />
          <span v-else class="avatar-placeholder">
            {{ user.username?.charAt(0)?.toUpperCase() || '?' }}
          </span>
          
          <!-- Online indicator -->
          <span class="online-dot" v-if="user.is_online"></span>
        </div>
        
        <!-- Info -->
        <div class="user-info">
          <div class="user-name-row">
            <span 
              class="badge" 
              v-if="getConfig(user.plan).badge"
            >
              {{ getConfig(user.plan).badge }}
            </span>
            <span 
              class="plan-tag"
              :class="user.plan"
            >
              [{{ getConfig(user.plan).tag }}]
            </span>
            <span 
              class="username"
              :class="getConfig(user.plan).textClass"
            >
              {{ user.username }}
            </span>
            <span class="you-badge" v-if="isCurrentUser(user.user_id)">
              (você)
            </span>
          </div>
          
          <!-- Odds selecionadas (resumo) -->
          <div class="user-odds-preview" v-if="user.selected_odds?.length > 0">
            <span class="odds-count">
              🎯 {{ user.selected_odds.length }} odds
            </span>
          </div>
        </div>
      </div>
    </TransitionGroup>
    
    <!-- Empty state -->
    <div v-if="sortedUsers.length === 0" class="empty-state">
      <p>Nenhum usuário na sala</p>
    </div>
  </div>
</template>

<style scoped>
.user-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* User Item */
.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.03);
  transition: all 0.3s ease;
}

.user-item:hover {
  background: rgba(255,255,255,0.08);
}

.user-item.is-current {
  border: 1px solid rgba(255,215,0,0.3);
}

/* Plan Backgrounds */
.user-item.elite-bg {
  background: linear-gradient(135deg, rgba(255,215,0,0.15) 0%, rgba(255,140,0,0.1) 100%);
}

.user-item.pro-bg {
  background: linear-gradient(135deg, rgba(192,192,192,0.1) 0%, rgba(169,169,169,0.05) 100%);
}

.user-item.basic-bg {
  background: rgba(205,127,50,0.08);
}

/* Glow Effects */
.user-item.elite-glow {
  box-shadow: 0 0 15px rgba(255,215,0,0.2);
  animation: elite-pulse 2s infinite;
}

.user-item.pro-glow {
  box-shadow: 0 0 10px rgba(192,192,192,0.15);
}

@keyframes elite-pulse {
  0%, 100% {
    box-shadow: 0 0 15px rgba(255,215,0,0.2);
  }
  50% {
    box-shadow: 0 0 25px rgba(255,215,0,0.4);
  }
}

/* Avatar */
.user-avatar {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-weight: 600;
  font-size: 0.9rem;
}

.online-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #28a745;
  border: 2px solid #1a1a2e;
}

/* User Info */
.user-info {
  flex: 1;
  min-width: 0;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.badge {
  font-size: 0.9rem;
}

.plan-tag {
  font-size: 0.65rem;
  font-weight: 700;
  opacity: 0.7;
}

.plan-tag.elite {
  color: #ffd700;
}

.plan-tag.pro {
  color: #c0c0c0;
}

.plan-tag.basic {
  color: #cd7f32;
}

.plan-tag.free {
  color: #888;
}

.username {
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Text colors by plan */
.elite-text {
  color: #ffd700;
  text-shadow: 0 0 10px rgba(255,215,0,0.5);
}

.pro-text {
  color: #e0e0e0;
}

.basic-text {
  color: #cd7f32;
}

.you-badge {
  font-size: 0.7rem;
  color: #888;
  font-style: italic;
}

/* Odds Preview */
.user-odds-preview {
  margin-top: 0.25rem;
}

.odds-count {
  font-size: 0.7rem;
  color: #888;
}

/* Empty State */
.empty-state {
  text-align: center;
  color: #666;
  padding: 2rem;
}

/* Transitions */
.user-enter-active,
.user-leave-active {
  transition: all 0.3s ease;
}

.user-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.user-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.user-move {
  transition: transform 0.3s ease;
}
</style>
