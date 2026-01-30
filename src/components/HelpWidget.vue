<script setup>
import { ref } from 'vue'

const isOpen = ref(false)

const toggleHelp = () => {
  isOpen.value = !isOpen.value
}

const closeHelp = () => {
  isOpen.value = false
}
</script>

<template>
  <div class="help-widget">
    <!-- Botão Flutuante -->
    <button @click="toggleHelp" class="help-btn" :class="{ active: isOpen }">
      <svg v-if="!isOpen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- Painel de Ajuda -->
    <Transition name="slide">
      <div v-if="isOpen" class="help-panel">
        <div class="help-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Central de Ajuda
          </h3>
          <button @click="closeHelp" class="close-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="help-content">
          <div class="help-section">
            <h4>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              Início Rápido
            </h4>
            <ul>
              <li>Escolha seu <strong>plano</strong> para acessar os módulos</li>
              <li>Use <strong>Módulo BET</strong> para apostas esportivas</li>
              <li>Use <strong>Módulo TRADE</strong> para mercado financeiro</li>
              <li>Use <strong>Módulo Cartola</strong> para Cartola FC</li>
            </ul>
          </div>

          <div class="help-section">
            <h4>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              Módulo Cartola
            </h4>
            <ul>
              <li><strong>Mercado:</strong> Veja todos os atletas disponíveis</li>
              <li><strong>Escalação IA:</strong> Monte seu time automaticamente</li>
              <li><strong>Confrontos:</strong> Análise dos jogos da rodada</li>
              <li>Clique num atleta para adicionar ao time</li>
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
              <li><strong>Basic:</strong> Módulos BET + TRADE</li>
              <li><strong>Pro:</strong> + Cartola + Alertas</li>
              <li><strong>Elite:</strong> Acesso total + API</li>
            </ul>
          </div>

          <div class="help-section">
            <h4>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              Precisa de mais ajuda?
            </h4>
            <p>Entre em contato com nosso suporte via WhatsApp ou e-mail.</p>
            <a href="mailto:suporte@fantomstore.com.br" class="support-link">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              suporte@fantomstore.com.br
            </a>
          </div>
        </div>

        <div class="help-footer">
          <a href="https://fantomstore.com.br" target="_blank" rel="noopener" class="fantom-link">
            <img src="https://i.imgur.com/vNwaSEm.png" alt="Fantom Store" />
            <span>Uma solução da <strong>Fantom Store</strong></span>
          </a>
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

.help-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 5px 25px rgba(155, 89, 182, 0.4);
  transition: all 0.3s ease;
}

.help-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 35px rgba(155, 89, 182, 0.5);
}

.help-btn.active {
  background: linear-gradient(135deg, #8e44ad, #7b2cbf);
}

.help-btn svg {
  width: 28px;
  height: 28px;
  stroke: #fff;
}

.help-panel {
  position: absolute;
  bottom: 75px;
  right: 0;
  width: 340px;
  max-height: 500px;
  background: #1a1a1a;
  border: 1px solid rgba(155, 89, 182, 0.3);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5);
}

.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
}

.help-header h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1rem;
  color: #fff;
  font-weight: 700;
}

.help-header h3 svg {
  width: 22px;
  height: 22px;
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

.help-content {
  padding: 20px;
  max-height: 320px;
  overflow-y: auto;
}

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
  color: #bb86fc;
  margin-bottom: 10px;
  font-weight: 600;
}

.help-section h4 svg {
  width: 18px;
  height: 18px;
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
  color: rgba(255, 255, 255, 0.7);
}

.help-section li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #9b59b6;
}

.help-section li strong {
  color: #fff;
}

.help-section p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 10px;
}

.support-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #bb86fc;
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.3s;
}

.support-link:hover {
  color: #fff;
}

.support-link svg {
  width: 16px;
  height: 16px;
}

.help-footer {
  padding: 15px 20px;
  border-top: 1px solid rgba(155, 89, 182, 0.2);
  background: rgba(155, 89, 182, 0.05);
}

.fantom-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  transition: all 0.3s;
}

.fantom-link:hover {
  color: #fff;
}

.fantom-link img {
  height: 22px;
  width: auto;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.fantom-link:hover img {
  opacity: 1;
}

.fantom-link strong {
  color: #fff;
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
  background: rgba(255, 255, 255, 0.05);
}

.help-content::-webkit-scrollbar-thumb {
  background: rgba(155, 89, 182, 0.5);
  border-radius: 3px;
}

/* Mobile */
@media (max-width: 480px) {
  .help-widget {
    bottom: 15px;
    right: 15px;
  }
  
  .help-btn {
    width: 55px;
    height: 55px;
  }
  
  .help-panel {
    width: calc(100vw - 30px);
    right: -10px;
    max-height: 70vh;
  }
}
</style>
