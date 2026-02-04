<script setup>
import { ref } from 'vue'
import { supabase } from '../lib/supabase'

defineProps({
  visible: Boolean
})

const menuOpen = ref(false)
const user = ref(null)

supabase.auth.getSession().then(({ data: { session } }) => {
  user.value = session?.user ?? null
})

supabase.auth.onAuthStateChange((_event, session) => {
  user.value = session?.user ?? null
})

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const logout = async () => {
  await supabase.auth.signOut()
  menuOpen.value = false
}
</script>

<template>
  <nav class="navbar" :class="{ 'visible': visible }">
    <div class="nav-container">
      <div class="nav-brand">
        <img src="/icone.webp" alt="ODINENX" class="nav-icon" />
      </div>

      <div class="nav-links desktop">
        <a href="#modules" class="nav-link">Módulos</a>
        <a href="#pricing" class="nav-link">Preços</a>
        <router-link to="/live" class="nav-link live-link">
          <span class="live-dot"></span>
          Ao Vivo
        </router-link>
        <template v-if="user">
          <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
          <button @click="logout" class="nav-link btn-logout">Sair</button>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link">Login</router-link>
          <router-link to="/register" class="btn-register">Começar Grátis</router-link>
        </template>
      </div>

      <button class="menu-toggle" @click="toggleMenu" aria-label="Menu">
        <span :class="{ 'open': menuOpen }"></span>
        <span :class="{ 'open': menuOpen }"></span>
        <span :class="{ 'open': menuOpen }"></span>
      </button>
    </div>

    <div class="mobile-menu" :class="{ 'open': menuOpen }">
      <a href="#modules" class="nav-link" @click="menuOpen = false">Módulos</a>
      <a href="#pricing" class="nav-link" @click="menuOpen = false">Preços</a>
      <router-link to="/live" class="nav-link live-link" @click="menuOpen = false">
        <span class="live-dot"></span>
        Ao Vivo
      </router-link>
      <template v-if="user">
        <router-link to="/dashboard" class="nav-link" @click="menuOpen = false">Dashboard</router-link>
        <button @click="logout" class="nav-link btn-logout">Sair</button>
      </template>
      <template v-else>
        <router-link to="/login" class="nav-link" @click="menuOpen = false">Login</router-link>
        <router-link to="/register" class="btn-register" @click="menuOpen = false">Começar Grátis</router-link>
      </template>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 90px;
  left: 50%;
  transform: translateX(-50%) translateY(-20px);
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50px;
  padding: 12px 30px;
  z-index: 90;
  opacity: 0;
  transition: all 0.5s ease-out;
}

.navbar.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.nav-container {
  display: flex;
  align-items: center;
  gap: 30px;
}

.nav-brand {
  display: flex;
  align-items: center;
}

.nav-icon {
  height: 32px;
  width: auto;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 25px;
}

.nav-link {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
}

.nav-link:hover {
  color: #fff;
}

.btn-register {
  background: #fff;
  color: #000;
  padding: 10px 22px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn-register:hover {
  transform: scale(1.05);
  box-shadow: 0 5px 20px rgba(255, 255, 255, 0.2);
}

.btn-logout {
  color: #ff6b6b;
}

.btn-logout:hover {
  color: #ff4757;
}

.menu-toggle {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
}

.menu-toggle span {
  width: 22px;
  height: 2px;
  background: #fff;
  transition: all 0.3s ease;
}

.menu-toggle span.open:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.menu-toggle span.open:nth-child(2) {
  opacity: 0;
}

.menu-toggle span.open:nth-child(3) {
  transform: rotate(-45deg) translate(5px, -5px);
}

.mobile-menu {
  display: none;
  flex-direction: column;
  gap: 15px;
  padding-top: 20px;
  text-align: center;
}

.mobile-menu.open {
  display: flex;
}

/* Link Ao Vivo com animação */
.live-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #ff4444 !important;
  font-weight: 600;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #ff4444;
  border-radius: 50%;
  animation: pulse-live 1.5s infinite;
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7); }
  50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(255, 68, 68, 0); }
}

@media (max-width: 768px) {
  .navbar {
    top: 85px;
    left: 16px;
    right: 16px;
    transform: translateX(0) translateY(-20px);
    border-radius: 14px;
    padding: 12px 16px;
  }

  .navbar.visible {
    transform: translateX(0) translateY(0);
  }

  .nav-container {
    justify-content: space-between;
    width: 100%;
  }
  
  .nav-icon {
    height: 28px;
  }

  .desktop {
    display: none;
  }

  .menu-toggle {
    display: flex;
  }
  
  .mobile-menu {
    padding-top: 16px;
    gap: 12px;
  }
  
  .mobile-menu .nav-link {
    padding: 10px;
    font-size: 1rem;
  }
  
  .mobile-menu .btn-register {
    margin-top: 8px;
    padding: 12px 20px;
  }
}

@media (max-width: 480px) {
  .navbar {
    top: 75px;
    left: 12px;
    right: 12px;
    padding: 10px 14px;
  }
  
  .nav-icon {
    height: 24px;
  }
}
</style>
