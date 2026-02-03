<template>
  <div class="trial-expired-page">
    <div class="container">
      <div class="expired-card">
        <div class="expired-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="m15 9-6 6"/>
            <path d="m9 9 6 6"/>
          </svg>
        </div>
        
        <h1>🔒 Trial Expirado</h1>
        <p class="expired-message">
          Seu período gratuito de <strong>3 dias</strong> chegou ao fim!
        </p>
        
        <div class="trial-stats">
          <div class="stat-item">
            <span class="stat-label">Período do Trial:</span>
            <span class="stat-value">{{ formatDate(trialStart) }} - {{ formatDate(trialEnd) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Dias utilizados:</span>
            <span class="stat-value">{{ daysUsed }}/3 dias</span>
          </div>
        </div>
        
        <div class="benefits">
          <h3>🎯 O que você pode fazer agora:</h3>
          <ul>
            <li>✅ <strong>Continuar usando BET</strong> - Análises básicas de apostas</li>
            <li>🚀 <strong>Assinar um plano</strong> - Acesso completo + novas funcionalidades</li>
            <li>📊 <strong>Paper Trading</strong> - Simulação com R$ 10.000 virtuais</li>
            <li>🔔 <strong>Sistema de Alertas</strong> - Notificações automáticas</li>
          </ul>
        </div>
        
        <div class="action-buttons">
          <router-link to="/pricing" class="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Ver Planos - A partir de R$ 79
          </router-link>
          
          <router-link to="/bet" class="btn-secondary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22,6 13.5,14.5 8.5,9.5 2,16"/>
              <polyline points="16,6 22,6 22,12"/>
            </svg>
            Continuar no BET (Grátis)
          </router-link>
        </div>
        
        <div class="contact-support">
          <p>💬 <strong>Dúvidas?</strong> Entre em contato conosco!</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getTrialStatus, isAdmin } from '../lib/stripe'

const router = useRouter()
const trialData = ref(null)
const userIsAdmin = ref(false)

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  // Verificar se é admin
  userIsAdmin.value = await isAdmin(session.user.id)
  
  // Se for admin, redirecionar direto para dashboard
  if (userIsAdmin.value) {
    router.push('/dashboard')
    return
  }
  
  // Buscar dados do trial
  trialData.value = await getTrialStatus(session.user.id)
})

const trialStart = computed(() => {
  if (!trialData.value?.startDate) return null
  return new Date(trialData.value.startDate)
})

const trialEnd = computed(() => {
  if (!trialStart.value) return null
  const end = new Date(trialStart.value)
  end.setDate(end.getDate() + 3)
  return end
})

const daysUsed = computed(() => {
  return trialData.value?.daysUsed || 3
})

const formatDate = (date) => {
  if (!date) return 'N/A'
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}
</script>

<style scoped>
.trial-expired-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2d2d2d 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.container {
  max-width: 600px;
  width: 100%;
}

.expired-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 20px;
  padding: 3rem;
  text-align: center;
  backdrop-filter: blur(20px);
}

.expired-icon {
  background: rgba(255, 107, 107, 0.2);
  border-radius: 50%;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2rem;
}

.expired-icon svg {
  width: 40px;
  height: 40px;
  color: #ff6b6b;
}

h1 {
  color: #ff6b6b;
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
}

.expired-message {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.2rem;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.trial-stats {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: left;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.stat-value {
  color: white;
  font-weight: 600;
}

.benefits {
  text-align: left;
  margin-bottom: 2rem;
}

.benefits h3 {
  color: #00d9ff;
  font-size: 1.3rem;
  margin-bottom: 1rem;
  text-align: center;
}

.benefits ul {
  list-style: none;
  padding: 0;
}

.benefits li {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
  position: relative;
  line-height: 1.5;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn-primary, .btn-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #ff6b6b, #cc4444);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
}

.btn-secondary {
  background: rgba(0, 217, 255, 0.1);
  color: #00d9ff;
  border: 1px solid rgba(0, 217, 255, 0.3);
}

.btn-secondary:hover {
  background: rgba(0, 217, 255, 0.2);
  transform: translateY(-2px);
}

.btn-primary svg, .btn-secondary svg {
  width: 20px;
  height: 20px;
}

.contact-support {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 1.5rem;
}

@media (max-width: 768px) {
  .trial-expired-page {
    padding: 1rem;
  }
  
  .expired-card {
    padding: 2rem;
  }
  
  h1 {
    font-size: 2rem;
  }
  
  .stat-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>