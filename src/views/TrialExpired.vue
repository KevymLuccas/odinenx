<template>
  <div class="trial-page">
    <!-- Background Effects -->
    <div class="bg-effects">
      <div class="glow glow-1"></div>
      <div class="glow glow-2"></div>
      <div class="grid-overlay"></div>
    </div>

    <div class="container">
      <!-- Card Principal -->
      <div class="upgrade-card">
        <!-- Header com animação -->
        <div class="card-header">
          <div class="icon-wrapper">
            <div class="icon-bg"></div>
            <svg class="lock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h1>Seu Trial Terminou</h1>
          <p class="subtitle">
            Você aproveitou <span class="highlight">{{ daysUsed }} dias</span> de acesso completo
          </p>
        </div>

        <!-- Stats do Trial -->
        <div class="trial-summary">
          <div class="summary-item">
            <span class="label">Iniciou em</span>
            <span class="value">{{ formatDate(trialStart) }}</span>
          </div>
          <div class="divider"></div>
          <div class="summary-item">
            <span class="label">Expirou em</span>
            <span class="value">{{ formatDate(trialEnd) }}</span>
          </div>
        </div>

        <!-- Planos -->
        <div class="plans-section">
          <h2>Escolha seu plano</h2>
          <p class="plans-subtitle">Desbloqueie todo o potencial do ODINENX</p>
          
          <div class="plans-grid">
            <!-- Basic -->
            <div class="plan-card">
              <div class="plan-header">
                <span class="plan-name">Basic</span>
                <span class="plan-price">R$ <strong>19</strong>,90/mês</span>
              </div>
              <ul class="plan-features">
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Análises BET ilimitadas</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Paper Trading</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> GIFs no chat</li>
              </ul>
              <button @click="selectPlan('basic')" class="btn-plan">
                Assinar Basic
              </button>
            </div>

            <!-- Pro (Destaque) -->
            <div class="plan-card featured">
              <div class="featured-badge">⭐ Mais Popular</div>
              <div class="plan-header">
                <span class="plan-name">Pro</span>
                <span class="plan-price">R$ <strong>49</strong>,90/mês</span>
              </div>
              <ul class="plan-features">
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Tudo do Basic</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> 5 Salas Privadas</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Alertas Ilimitados</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Stickers + Badge VIP</li>
              </ul>
              <button @click="selectPlan('pro')" class="btn-plan btn-featured">
                Assinar Pro
              </button>
            </div>

            <!-- Elite -->
            <div class="plan-card elite">
              <div class="elite-badge">👑 Elite</div>
              <div class="plan-header">
                <span class="plan-name">Elite</span>
                <span class="plan-price">R$ <strong>99</strong>,90/mês</span>
              </div>
              <ul class="plan-features">
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Tudo do Pro</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Salas Ilimitadas</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> API de Odds em Tempo Real</li>
                <li><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Suporte Prioritário</li>
              </ul>
              <button @click="selectPlan('elite')" class="btn-plan btn-elite">
                Assinar Elite
              </button>
            </div>
          </div>
        </div>

        <!-- Link Free -->
        <div class="free-option">
          <router-link to="/dashboard" class="link-free">
            Continuar gratuitamente (recursos limitados) →
          </router-link>
        </div>
      </div>

      <!-- Garantia -->
      <div class="guarantee">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <polyline points="9 12 11 14 15 10"/>
        </svg>
        <span>Garantia de 7 dias ou seu dinheiro de volta</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getTrialStatus, isAdmin, redirectToCheckout } from '../lib/stripe'

const router = useRouter()
const trialData = ref(null)
const loading = ref(false)

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  // Se for admin, redirecionar
  if (await isAdmin(session.user.id)) {
    router.push('/dashboard')
    return
  }
  
  trialData.value = await getTrialStatus(session.user.id)
})

const trialStart = computed(() => {
  if (!trialData.value?.startDate) return new Date()
  return new Date(trialData.value.startDate)
})

const trialEnd = computed(() => {
  const end = new Date(trialStart.value)
  end.setDate(end.getDate() + 3)
  return end
})

const daysUsed = computed(() => trialData.value?.daysUsed || 3)

const formatDate = (date) => {
  if (!date) return '--'
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

const selectPlan = async (planId) => {
  loading.value = true
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return router.push('/login')
    
    await redirectToCheckout(planId)
  } catch (err) {
    console.error('Erro ao criar checkout:', err)
    alert('Erro ao processar. Tente novamente.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.trial-page {
  min-height: 100vh;
  background: #0a0a0f;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

/* Background Effects */
.bg-effects {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.4;
}

.glow-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  top: -200px;
  right: -100px;
}

.glow-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #06b6d4, #0ea5e9);
  bottom: -150px;
  left: -100px;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 50px 50px;
}

.container {
  max-width: 900px;
  width: 100%;
  position: relative;
  z-index: 1;
}

/* Card Principal */
.upgrade-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 24px;
  padding: 3rem;
  backdrop-filter: blur(20px);
}

/* Header */
.card-header {
  text-align: center;
  margin-bottom: 2rem;
}

.icon-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
}

.icon-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border-radius: 50%;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.lock-icon {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 36px;
  height: 36px;
  color: white;
  z-index: 1;
}

.card-header h1 {
  font-size: 2rem;
  font-weight: 800;
  color: white;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: rgba(255,255,255,0.6);
  font-size: 1.1rem;
}

.highlight {
  color: #f59e0b;
  font-weight: 600;
}

/* Trial Summary */
.trial-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 1.5rem;
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  margin-bottom: 2.5rem;
}

.summary-item {
  text-align: center;
}

.summary-item .label {
  display: block;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.5);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-item .value {
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.divider {
  width: 1px;
  height: 40px;
  background: rgba(255,255,255,0.1);
}

/* Plans Section */
.plans-section h2 {
  text-align: center;
  font-size: 1.5rem;
  color: white;
  margin-bottom: 0.5rem;
}

.plans-subtitle {
  text-align: center;
  color: rgba(255,255,255,0.5);
  margin-bottom: 2rem;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

/* Plan Card */
.plan-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 1.5rem;
  position: relative;
  transition: all 0.3s;
}

.plan-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255,255,255,0.2);
}

.plan-card.featured {
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1));
  border-color: rgba(99, 102, 241, 0.4);
  transform: scale(1.02);
}

.plan-card.elite {
  background: linear-gradient(145deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));
  border-color: rgba(245, 158, 11, 0.3);
}

.featured-badge, .elite-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.25rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.featured-badge {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.elite-badge {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.plan-header {
  text-align: center;
  margin-bottom: 1.5rem;
  padding-top: 0.5rem;
}

.plan-name {
  display: block;
  font-size: 1rem;
  color: rgba(255,255,255,0.7);
  margin-bottom: 0.5rem;
}

.plan-price {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.5);
}

.plan-price strong {
  font-size: 2rem;
  color: white;
  font-weight: 700;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin-bottom: 1.5rem;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255,255,255,0.8);
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}

.plan-features svg {
  width: 16px;
  height: 16px;
  stroke: #22c55e;
  stroke-width: 3;
  fill: none;
}

.btn-plan {
  width: 100%;
  padding: 0.875rem;
  border-radius: 10px;
  border: none;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(255,255,255,0.1);
  color: white;
}

.btn-plan:hover {
  background: rgba(255,255,255,0.2);
}

.btn-featured {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.btn-featured:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
}

.btn-elite {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.btn-elite:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 30px rgba(245, 158, 11, 0.4);
}

/* Free Option */
.free-option {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255,255,255,0.08);
}

.link-free {
  color: rgba(255,255,255,0.5);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s;
}

.link-free:hover {
  color: rgba(255,255,255,0.8);
}

/* Guarantee */
.guarantee {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 2rem;
  color: rgba(255,255,255,0.5);
  font-size: 0.85rem;
}

.guarantee svg {
  width: 20px;
  height: 20px;
  stroke: #22c55e;
}

/* Responsivo */
@media (max-width: 768px) {
  .trial-page {
    padding: 1rem;
  }
  
  .upgrade-card {
    padding: 1.5rem;
  }
  
  .plans-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .plan-card.featured {
    transform: none;
    order: -1;
  }
  
  .trial-summary {
    flex-direction: column;
    gap: 1rem;
  }
  
  .divider {
    width: 60px;
    height: 1px;
  }
}
</style>
