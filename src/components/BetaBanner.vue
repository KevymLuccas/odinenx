<script setup>
import { ref } from 'vue'

const showDetails = ref(false)
const dismissed = ref(false)

const dismiss = () => {
  dismissed.value = true
  localStorage.setItem('beta_badge_dismissed', 'true')
}

// Checar se já foi dispensado
if (typeof window !== 'undefined') {
  dismissed.value = localStorage.getItem('beta_badge_dismissed') === 'true'
}
</script>

<template>
  <div v-if="!dismissed" class="beta-banner">
    <div class="beta-content">
      <span class="beta-badge">🚀 BETA</span>
      <span class="beta-text">
        Sistema em fase beta - Novos recursos todos os dias!
      </span>
      <button class="beta-info" @click="showDetails = true">Saiba mais</button>
    </div>
    <button class="beta-close" @click="dismiss">×</button>
  </div>
  
  <!-- Modal de detalhes -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showDetails" class="beta-modal-overlay" @click.self="showDetails = false">
        <div class="beta-modal">
          <button class="modal-close" @click="showDetails = false">×</button>
          
          <div class="modal-header">
            <span class="big-badge">🚀 BETA</span>
            <h2>ODINENX está em Beta!</h2>
          </div>
          
          <div class="modal-body">
            <p class="intro">
              Estamos trabalhando constantemente para trazer a melhor experiência de palpites esportivos do Brasil.
            </p>
            
            <div class="feature-list">
              <div class="feature-item">
                <span class="feature-icon">📊</span>
                <div>
                  <strong>Palpites com IA</strong>
                  <p>Análises baseadas em dados reais e algoritmos avançados</p>
                </div>
              </div>
              
              <div class="feature-item">
                <span class="feature-icon">⚡</span>
                <div>
                  <strong>Atualizações Diárias</strong>
                  <p>Novos recursos e melhorias a cada dia</p>
                </div>
              </div>
              
              <div class="feature-item">
                <span class="feature-icon">🎁</span>
                <div>
                  <strong>Early Adopters</strong>
                  <p>Usuários beta terão benefícios exclusivos</p>
                </div>
              </div>
              
              <div class="feature-item">
                <span class="feature-icon">💬</span>
                <div>
                  <strong>Seu Feedback Importa</strong>
                  <p>Ajude a moldar o futuro da plataforma</p>
                </div>
              </div>
            </div>
            

          </div>
          
          <div class="modal-footer">
            <button class="btn btn-primary" @click="showDetails = false">
              Entendi, vamos lá! 🔥
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.beta-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(90deg, #ff9800, #ff5722);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 9999;
  box-shadow: 0 4px 20px rgba(255, 152, 0, 0.3);
}

.beta-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.beta-badge {
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 50px;
  letter-spacing: 1px;
}

.beta-text {
  color: #fff;
  font-size: 0.85rem;
  font-weight: 500;
}

.beta-info {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: none;
  padding: 5px 12px;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.beta-info:hover {
  background: rgba(255, 255, 255, 0.3);
}

.beta-close {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  transition: color 0.3s ease;
}

.beta-close:hover {
  color: #fff;
}

/* Modal */
.beta-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  padding: 20px;
}

.beta-modal {
  background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
  border: 1px solid rgba(255, 152, 0, 0.3);
  border-radius: 20px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  -webkit-overflow-scrolling: touch;
}

.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 28px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.modal-header {
  text-align: center;
  padding: 30px 30px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.big-badge {
  display: inline-block;
  background: linear-gradient(90deg, #ff9800, #ff5722);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 800;
  padding: 6px 16px;
  border-radius: 50px;
  letter-spacing: 2px;
  margin-bottom: 15px;
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

.modal-body {
  padding: 25px 30px;
}

.intro {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 25px;
  text-align: center;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 25px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: rgba(255, 255, 255, 0.03);
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.feature-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.feature-item strong {
  display: block;
  color: #fff;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.feature-item p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  line-height: 1.4;
}

.modal-footer {
  padding: 20px 30px 30px;
  text-align: center;
}

.btn {
  display: inline-block;
  padding: 14px 32px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  border: none;
}

.btn-primary {
  background: linear-gradient(90deg, #ff9800, #ff5722);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 152, 0, 0.3);
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .beta-modal,
.modal-leave-to .beta-modal {
  transform: scale(0.95) translateY(20px);
}

@media (max-width: 768px) {
  .beta-banner {
    padding: 12px 50px 12px 15px;
  }
  
  .beta-text {
    font-size: 0.75rem;
  }
  
  .beta-info {
    display: none;
  }
}
</style>
