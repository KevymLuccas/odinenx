<script setup>
import { ref, onMounted, computed } from 'vue'
import { supabase } from '../lib/supabase'

const isOpen = ref(false)
const user = ref(null)
const userName = ref('')

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user
  if (user.value) {
    // Extrair nome do email ou usar nome do perfil
    const email = user.value.email || ''
    userName.value = user.value.user_metadata?.name || email.split('@')[0] || 'Usuário'
  }
})

const saudacao = computed(() => {
  const hora = new Date().getHours()
  if (hora >= 5 && hora < 12) return 'Bom dia'
  if (hora >= 12 && hora < 18) return 'Boa tarde'
  return 'Boa noite'
})

const toggleHelp = () => {
  isOpen.value = !isOpen.value
}

const closeHelp = () => {
  isOpen.value = false
}
</script>

<template>
  <div class="help-widget">
    <!-- Botão Flutuante Animado (Odin) -->
    <button @click="toggleHelp" class="help-btn pup-animate" :class="{ active: isOpen }">
      <img src="/icone.webp" alt="Odin" class="odin-icon" />
      <span class="pup-wave"></span>
      <span class="pup-wave delay"></span>
    </button>

    <!-- Painel de Ajuda -->
    <Transition name="slide">
      <div v-if="isOpen" class="help-panel">
        <div class="help-header">
          <div class="greeting-section">
            <img src="/icone.webp" alt="Odin" class="odin-avatar" />
            <div class="greeting-text">
              <h3>{{ saudacao }}, {{ userName || 'Visitante' }}!</h3>
              <p>Eu sou o Odin, como posso ajudar?</p>
            </div>
          </div>
          <button @click="closeHelp" class="close-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="help-content">
          <!-- Info do usuário logado -->
          <div v-if="user" class="user-info-card">
            <div class="user-avatar">{{ (userName || 'U').charAt(0).toUpperCase() }}</div>
            <div class="user-details">
              <span class="user-name">{{ userName }}</span>
              <span class="user-email">{{ user.email }}</span>
            </div>
            <span class="user-status">✅ Logado</span>
          </div>
          
          <div v-else class="guest-card">
            <p>👋 Você está navegando como visitante</p>
            <router-link to="/login" class="login-link" @click="closeHelp">Fazer Login</router-link>
          </div>

          <div class="quick-actions">
            <h4>⚡ Ações Rápidas</h4>
            <div class="actions-grid">
              <router-link to="/palpites" class="action-btn" @click="closeHelp">
                <span>⚽</span>
                <span>Palpites</span>
              </router-link>
              <router-link to="/pricing" class="action-btn" @click="closeHelp">
                <span>💎</span>
                <span>Planos</span>
              </router-link>
              <router-link v-if="user" to="/dashboard" class="action-btn" @click="closeHelp">
                <span>📊</span>
                <span>Dashboard</span>
              </router-link>
              <router-link v-else to="/register" class="action-btn" @click="closeHelp">
                <span>🚀</span>
                <span>Criar Conta</span>
              </router-link>
            </div>
          </div>

          <div class="help-section">
            <h4>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              O que oferecemos
            </h4>
            <ul>
              <li><strong>Palpites grátis</strong> para todos os jogos</li>
              <li>Análise completa com <strong>estatísticas H2H</strong></li>
              <li><strong>Módulo TRADE</strong> para cripto e ações</li>
              <li><strong>Módulo Cartola</strong> para Cartola FC</li>
            </ul>
          </div>

          <div class="help-section">
            <h4>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              Planos
            </h4>
            <ul>
              <li><strong>Free:</strong> Palpites básicos grátis</li>
              <li><strong>Basic:</strong> Análise completa + H2H</li>
              <li><strong>Pro:</strong> + TRADE + Cartola</li>
              <li><strong>Elite:</strong> Tudo ilimitado</li>
            </ul>
          </div>

          <div class="help-section">
            <h4>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              Precisa de mais ajuda?
            </h4>
            <p>Entre em contato com nosso suporte.</p>
          </div>
        </div>

        <div class="help-footer">
          <div class="fantom-link">
            <img src="https://i.imgur.com/vNwaSEm.png" alt="Fantom Tecnologias" />
            <span>Uma solução da <strong>Fantom Tecnologias</strong></span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.help-widget {
  position: fixed;
  bottom: 25px;
  right: 25px;
  z-index: 9999;
}

/* Botão Odin Animado */
.help-btn {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a1a1a, #0d0d0d);
  border: 2px solid rgba(255, 255, 255, 0.15);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 5px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: visible;
}

.odin-icon {
  width: 50px;
  height: 50px;
  object-fit: contain;
  z-index: 2;
  animation: odinFloat 3s ease-in-out infinite;
  filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.3));
}

/* Ondas pulsantes */
.pup-wave {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  animation: pupPulse 2.5s ease-out infinite;
}

.pup-wave.delay {
  animation-delay: 0.8s;
}

@keyframes pupPulse {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

@keyframes odinFloat {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-4px) scale(1.05);
  }
}

.help-btn:hover {
  transform: scale(1.12);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(255, 255, 255, 0.15);
}

.help-btn:hover .odin-icon {
  animation: odinWiggle 0.6s ease-in-out;
  filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.5));
}

@keyframes odinWiggle {
  0%, 100% { transform: rotate(0deg) scale(1.1); }
  25% { transform: rotate(-10deg) scale(1.1); }
  75% { transform: rotate(10deg) scale(1.1); }
}

.help-btn.active {
  background: linear-gradient(135deg, #0d0d0d, #000);
  border-color: rgba(255, 255, 255, 0.25);
}

.help-btn.active .pup-wave {
  display: none;
}

.help-btn svg {
  width: 28px;
  height: 28px;
  stroke: #fff;
}

/* Painel */
.help-panel {
  position: absolute;
  bottom: 85px;
  right: 0;
  width: 370px;
  max-height: 560px;
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
}

/* Header com saudação */
.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a1a, #0d0d0d);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.greeting-section {
  display: flex;
  align-items: center;
  gap: 14px;
}

.odin-avatar {
  width: 50px;
  height: 50px;
  object-fit: contain;
  animation: odinFloat 3s ease-in-out infinite;
  filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.3));
}

.greeting-text h3 {
  font-size: 1.05rem;
  color: #fff;
  font-weight: 700;
  margin: 0;
}

.greeting-text p {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 4px 0 0;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.close-btn svg {
  width: 16px;
  height: 16px;
  stroke: #fff;
}

/* Conteúdo */
.help-content {
  padding: 20px;
  max-height: 380px;
  overflow-y: auto;
}

/* Card do usuário logado */
.user-info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 20px;
}

.user-avatar {
  width: 45px;
  height: 45px;
  background: linear-gradient(135deg, #333, #1a1a1a);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: #fff;
}

.user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 700;
  color: #fff;
  font-size: 0.95rem;
}

.user-email {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.user-status {
  font-size: 0.75rem;
  color: #4caf50;
}

/* Card de visitante */
.guest-card {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 20px;
}

.guest-card p {
  margin: 0 0 12px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.login-link {
  display: inline-block;
  background: #fff;
  color: #000;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.3s;
}

.login-link:hover {
  transform: scale(1.05);
  box-shadow: 0 5px 20px rgba(255, 255, 255, 0.2);
}

/* Ações Rápidas */
.quick-actions {
  margin-bottom: 20px;
}

.quick-actions h4 {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 15px 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  color: #fff;
  text-decoration: none;
  transition: all 0.3s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.action-btn span:first-child {
  font-size: 1.4rem;
}

.action-btn span:last-child {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

/* Seções de Ajuda */
.help-section {
  margin-bottom: 20px;
}

.help-section:last-child {
  margin-bottom: 0;
}

.help-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 10px;
  font-weight: 600;
}

.help-section h4 svg {
  width: 18px;
  height: 18px;
  stroke: rgba(255, 255, 255, 0.6);
}

.help-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.help-section li {
  padding: 6px 0;
  padding-left: 15px;
  position: relative;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.help-section li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: rgba(255, 255, 255, 0.3);
}

.help-section li strong {
  color: #fff;
}

.help-section p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 10px;
}

/* Footer */
.help-footer {
  padding: 15px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.3);
}

.fantom-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  transition: all 0.3s;
}

.fantom-link:hover {
  color: #fff;
}

.fantom-link img {
  height: 22px;
  width: auto;
  opacity: 0.6;
  transition: opacity 0.3s;
}

.fantom-link:hover img {
  opacity: 1;
}

.fantom-link strong {
  color: rgba(255, 255, 255, 0.8);
}

/* Animations */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* Scrollbar */
.help-content::-webkit-scrollbar {
  width: 6px;
}

.help-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}

.help-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

/* Mobile */
@media (max-width: 480px) {
  .help-widget {
    bottom: 15px;
    right: 15px;
  }
  
  .help-btn {
    width: 62px;
    height: 62px;
  }
  
  .odin-icon {
    width: 42px;
    height: 42px;
  }
  
  .help-panel {
    width: calc(100vw - 30px);
    right: -10px;
    max-height: 70vh;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
