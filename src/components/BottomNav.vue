<script setup>
/**
 * 📱 BottomNav.vue - Navegação Mobile Inferior
 * ODINENX v2.0 - Design inspirado em apps nativos
 */

import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  showAdmin: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const router = useRouter()

// Itens de navegação
const navItems = computed(() => {
  const items = [
    { 
      id: 'dashboard', 
      path: '/dashboard', 
      label: 'Início', 
      icon: 'home',
      activeColor: '#7c3aed'
    },
    { 
      id: 'live', 
      path: '/live', 
      label: 'Ao Vivo', 
      icon: 'live',
      activeColor: '#ef4444',
      hasIndicator: true
    },
    { 
      id: 'bet', 
      path: '/bet', 
      label: 'BET', 
      icon: 'bet',
      activeColor: '#22c55e'
    },
    { 
      id: 'cartola', 
      path: '/cartola', 
      label: 'Cartola', 
      icon: 'cartola',
      activeColor: '#f97316'
    },
    { 
      id: 'more', 
      path: null, 
      label: 'Mais', 
      icon: 'more',
      activeColor: '#8b5cf6',
      isMenu: true
    }
  ]
  return items
})

// Menu "Mais" expandido
const moreMenuOpen = defineModel('moreMenuOpen', { default: false })

const moreItems = [
  { id: 'trade', path: '/trade', label: 'Trade', icon: '📈' },
  { id: 'alerts', path: '/alerts', label: 'Alertas', icon: '🔔' },
  { id: 'history', path: '/history', label: 'Histórico', icon: '📊' },
  { id: 'settings', path: '/settings', label: 'Configurações', icon: '⚙️' },
]

const isActive = (path) => {
  if (!path) return false
  return route.path === path || route.path.startsWith(path + '/')
}

const isMoreActive = computed(() => {
  return moreItems.some(item => route.path === item.path)
})

const navigate = (item) => {
  if (item.isMenu) {
    moreMenuOpen.value = !moreMenuOpen.value
  } else if (item.path) {
    moreMenuOpen.value = false
    router.push(item.path)
  }
}

const navigateMore = (path) => {
  moreMenuOpen.value = false
  router.push(path)
}

const closeMenu = () => {
  moreMenuOpen.value = false
}
</script>

<template>
  <!-- Overlay para fechar menu -->
  <Teleport to="body">
    <div v-if="moreMenuOpen" class="bottom-nav-overlay" @click="closeMenu"></div>
  </Teleport>

  <!-- Menu Mais expandido -->
  <Transition name="slide-up">
    <div v-if="moreMenuOpen" class="more-menu">
      <div class="more-menu-header">
        <span>Mais opções</span>
        <button @click="closeMenu" class="close-btn">✕</button>
      </div>
      <div class="more-menu-grid">
        <button 
          v-for="item in moreItems" 
          :key="item.id"
          @click="navigateMore(item.path)"
          class="more-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="more-icon">{{ item.icon }}</span>
          <span class="more-label">{{ item.label }}</span>
        </button>
        <button 
          v-if="showAdmin"
          @click="navigateMore('/admin')"
          class="more-item admin"
          :class="{ active: isActive('/admin') }"
        >
          <span class="more-icon">🛡️</span>
          <span class="more-label">Admin</span>
        </button>
      </div>
    </div>
  </Transition>

  <!-- Bottom Navigation Bar -->
  <nav class="bottom-nav">
    <button 
      v-for="item in navItems" 
      :key="item.id"
      @click="navigate(item)"
      class="nav-btn"
      :class="{ 
        active: item.isMenu ? (moreMenuOpen || isMoreActive) : isActive(item.path),
        'has-indicator': item.hasIndicator
      }"
      :style="{ '--active-color': item.activeColor }"
    >
      <!-- Ícones SVG -->
      <div class="nav-icon-wrapper">
        <!-- Live indicator -->
        <span v-if="item.hasIndicator" class="live-pulse"></span>
        
        <!-- Home -->
        <svg v-if="item.icon === 'home'" class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        
        <!-- Live -->
        <svg v-else-if="item.icon === 'live'" class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polygon points="10 8 16 12 10 16 10 8" fill="currentColor"/>
        </svg>
        
        <!-- BET -->
        <svg v-else-if="item.icon === 'bet'" class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        
        <!-- Cartola -->
        <svg v-else-if="item.icon === 'cartola'" class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
        </svg>
        
        <!-- More -->
        <svg v-else-if="item.icon === 'more'" class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="1" fill="currentColor"/>
          <circle cx="12" cy="5" r="1" fill="currentColor"/>
          <circle cx="12" cy="19" r="1" fill="currentColor"/>
        </svg>
      </div>
      
      <span class="nav-label">{{ item.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
/* Bottom Navigation Bar */
.bottom-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(65px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: rgba(10, 10, 10, 0.95);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 1000;
  -webkit-box-pack: space-around;
  justify-content: space-around;
  align-items: center;
}

@media (max-width: 968px) {
  .bottom-nav {
    display: -webkit-box;
    display: -webkit-flex;
    display: flex;
  }
}

.nav-btn {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  -webkit-transition: all 0.2s ease;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
  position: relative;
  min-width: 60px;
}

.nav-btn.active {
  color: var(--active-color, #7c3aed);
}

.nav-btn.active .nav-icon-wrapper {
  background: rgba(124, 58, 237, 0.15);
  background: color-mix(in srgb, var(--active-color, #7c3aed) 15%, transparent);
}

.nav-icon-wrapper {
  position: relative;
  width: 40px;
  height: 32px;
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
  border-radius: 16px;
  -webkit-transition: all 0.2s ease;
  transition: all 0.2s ease;
}

.nav-icon {
  width: 22px;
  height: 22px;
}

.nav-label {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Live Pulse Animation */
.live-pulse {
  position: absolute;
  top: 2px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  -webkit-animation: pulse-live 1.5s infinite;
  animation: pulse-live 1.5s infinite;
}

@-webkit-keyframes pulse-live {
  0%, 100% { opacity: 1; -webkit-transform: scale(1); transform: scale(1); }
  50% { opacity: 0.5; -webkit-transform: scale(1.3); transform: scale(1.3); }
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

/* More Menu */
.bottom-nav-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
  z-index: 998;
}

.more-menu {
  position: fixed;
  bottom: calc(65px + env(safe-area-inset-bottom));
  left: 0;
  right: 0;
  background: #0f0f0f;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  padding: 20px;
  z-index: 999;
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.more-menu-header {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-pack: justify;
  -webkit-justify-content: space-between;
  justify-content: space-between;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.more-menu-header span {
  font-weight: 700;
  font-size: 1.1rem;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
}

.more-menu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.more-item {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  -webkit-transition: all 0.2s ease;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.more-item:hover,
.more-item:active {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.more-item.active {
  background: rgba(124, 58, 237, 0.15);
  border-color: rgba(124, 58, 237, 0.3);
  color: #a855f7;
}

.more-item.admin {
  background: rgba(234, 179, 8, 0.1);
  border-color: rgba(234, 179, 8, 0.2);
}

.more-icon {
  font-size: 1.5rem;
}

.more-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
}

/* Animations */
.slide-up-enter-active,
.slide-up-leave-active {
  -webkit-transition: all 0.3s ease;
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  -webkit-transform: translateY(100%);
  transform: translateY(100%);
  opacity: 0;
}

/* Responsivo */
@media (max-width: 400px) {
  .more-menu-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .nav-btn {
    padding: 8px 12px;
    min-width: 50px;
  }
  
  .nav-label {
    font-size: 0.6rem;
  }
}
</style>
