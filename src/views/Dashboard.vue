<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, createCustomerPortal, cancelSubscription, plans } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const showCancelModal = ref(false)
const canceling = ref(false)

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  loading.value = false
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

const isPaidPlan = computed(() => {
  return currentPlan.value.id !== 'free'
})

const isCanceledButActive = computed(() => {
  return subscription.value?.cancel_at_period_end === true
})

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}

const openBillingPortal = async () => {
  try {
    await createCustomerPortal()
  } catch (error) {
    console.error('Erro ao abrir portal:', error)
  }
}

const handleCancelSubscription = async () => {
  canceling.value = true
  try {
    await cancelSubscription()
    subscription.value = await getSubscriptionStatus(user.value.id)
    showCancelModal.value = false
  } catch (error) {
    console.error('Erro ao cancelar:', error)
    alert('Erro ao cancelar assinatura. Tente novamente.')
  } finally {
    canceling.value = false
  }
}
</script>

<template>
  <div class="dashboard">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/">
          <img src="/logo.webp" alt="ODINENX" class="sidebar-logo" />
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <a href="#" class="nav-item active">
          <span class="nav-icon">📊</span>
          Dashboard
        </a>
        <a href="#" class="nav-item">
          <span class="nav-icon">⚽</span>
          Módulo BET
        </a>
        <a href="#" class="nav-item">
          <span class="nav-icon">📈</span>
          Módulo TRADE
        </a>
        <a href="#" class="nav-item">
          <span class="nav-icon">🔔</span>
          Alertas
        </a>
        <a href="#" class="nav-item">
          <span class="nav-icon">📜</span>
          Histórico
        </a>
        <a href="#" class="nav-item">
          <span class="nav-icon">⚙️</span>
          Configurações
        </a>
      </nav>

      <div class="sidebar-footer">
        <div class="plan-badge-sidebar">
          {{ currentPlan.name }}
        </div>
        <button @click="logout" class="logout-btn">
          Sair
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-left">
          <h1>Dashboard</h1>
          <p>Bem-vindo de volta, {{ user?.user_metadata?.name || 'Usuário' }}!</p>
        </div>
        <div class="header-right">
          <div class="user-info">
            <div class="user-avatar">
              {{ (user?.user_metadata?.name || user?.email || 'U')[0].toUpperCase() }}
            </div>
            <div class="user-details">
              <span class="user-name">{{ user?.user_metadata?.name || 'Usuário' }}</span>
              <span class="user-email">{{ user?.email }}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Loading -->
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
      </div>

      <!-- Content -->
      <div v-else class="dashboard-content">
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <span class="stat-value">0</span>
              <span class="stat-label">Análises hoje</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-info">
              <span class="stat-value">0%</span>
              <span class="stat-label">Taxa de acerto</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-info">
              <span class="stat-value">0</span>
              <span class="stat-label">Oportunidades</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <div class="stat-info">
              <span class="stat-value">{{ currentPlan.limits?.analysisPerDay === -1 ? '∞' : currentPlan.limits?.analysisPerDay }}</span>
              <span class="stat-label">Análises restantes</span>
            </div>
          </div>
        </div>

        <!-- Plan Card -->
        <div class="plan-section">
          <div class="plan-card-dashboard">
            <div class="plan-info-dash">
              <div class="plan-badge-large" :class="{ 'canceled': isCanceledButActive }">
                {{ currentPlan.name }}
                <span v-if="isCanceledButActive" class="canceled-tag">Cancelado</span>
              </div>
              <h3>Seu Plano Atual</h3>
              <p v-if="currentPlan.id === 'free'">
                Faça upgrade para desbloquear mais recursos
              </p>
              <p v-else-if="isCanceledButActive" class="cancel-notice">
                ⚠️ Assinatura cancelada. Acesso até: {{ subscription?.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString('pt-BR') : 'N/A' }}
              </p>
              <p v-else>
                Próxima cobrança: {{ subscription?.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString('pt-BR') : 'N/A' }}
              </p>
            </div>
            <div class="plan-actions-dash">
              <router-link v-if="currentPlan.id === 'free'" to="/pricing" class="btn-upgrade">
                Fazer Upgrade
              </router-link>
              <template v-else>
                <button @click="openBillingPortal" class="btn-manage">
                  Gerenciar Assinatura
                </button>
                <button v-if="!isCanceledButActive" @click="showCancelModal = true" class="btn-cancel">
                  Cancelar Assinatura
                </button>
                <router-link v-else to="/pricing" class="btn-reactivate">
                  Reativar Assinatura
                </router-link>
              </template>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
          <h2>Ações Rápidas</h2>
          <div class="actions-grid">
            <div class="action-card">
              <span class="action-icon">⚽</span>
              <h4>Nova Análise BET</h4>
              <p>Analise partidas de futebol</p>
              <button class="action-btn">Iniciar</button>
            </div>
            <div class="action-card">
              <span class="action-icon">📈</span>
              <h4>Nova Análise TRADE</h4>
              <p>Analise ativos financeiros</p>
              <button class="action-btn">Iniciar</button>
            </div>
            <div class="action-card">
              <span class="action-icon">📅</span>
              <h4>Calendário</h4>
              <p>Eventos e jogos do dia</p>
              <button class="action-btn">Ver</button>
            </div>
            <div class="action-card">
              <span class="action-icon">📊</span>
              <h4>Relatórios</h4>
              <p>Seu desempenho detalhado</p>
              <button class="action-btn">Ver</button>
            </div>
          </div>
        </div>

        <!-- Recent Analyses -->
        <div class="recent-section">
          <h2>Análises Recentes</h2>
          <div class="empty-state">
            <span class="empty-icon">📭</span>
            <h4>Nenhuma análise ainda</h4>
            <p>Comece fazendo sua primeira análise!</p>
          </div>
        </div>
      </div>
    </main>

    <!-- Cancel Modal -->
    <div v-if="showCancelModal" class="modal-overlay" @click.self="showCancelModal = false">
      <div class="modal">
        <div class="modal-icon">⚠️</div>
        <h3>Cancelar Assinatura?</h3>
        <p>Tem certeza que deseja cancelar sua assinatura do plano <strong>{{ currentPlan.name }}</strong>?</p>
        <ul class="cancel-info">
          <li>Você continuará tendo acesso até o fim do período pago</li>
          <li>Perderá acesso aos recursos premium após essa data</li>
          <li>Pode reativar a qualquer momento</li>
        </ul>
        <div class="modal-actions">
          <button @click="showCancelModal = false" class="btn-keep" :disabled="canceling">
            Manter Assinatura
          </button>
          <button @click="handleCancelSubscription" class="btn-confirm-cancel" :disabled="canceling">
            {{ canceling ? 'Cancelando...' : 'Confirmar Cancelamento' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #000;
  color: #fff;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: rgba(255, 255, 255, 0.02);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
}

.sidebar-header {
  padding: 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  height: 35px;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 15px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  transition: all 0.3s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-icon {
  font-size: 1.2rem;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.plan-badge-sidebar {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  text-align: center;
}

.logout-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.6);
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 30px;
}

/* Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.header-left h1 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 5px;
}

.header-left p {
  color: rgba(255, 255, 255, 0.5);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 45px;
  height: 45px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
}

.user-email {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 100px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  font-size: 2rem;
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 12px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
}

.stat-label {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

/* Plan Section */
.plan-section {
  margin-bottom: 40px;
}

.plan-card-dashboard {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 35px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.plan-badge-large {
  display: inline-block;
  background: #fff;
  color: #000;
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 1px;
  margin-bottom: 15px;
}

.plan-info-dash h3 {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.plan-info-dash p {
  color: rgba(255, 255, 255, 0.5);
}

.btn-upgrade,
.btn-manage {
  padding: 15px 30px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upgrade {
  background: #fff;
  color: #000;
  text-decoration: none;
}

.btn-upgrade:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

.btn-manage {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-manage:hover {
  border-color: #fff;
}

/* Quick Actions */
.quick-actions {
  margin-bottom: 40px;
}

.quick-actions h2 {
  font-size: 1.3rem;
  margin-bottom: 20px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.action-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  text-align: center;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.2);
}

.action-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 15px;
}

.action-card h4 {
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.action-card p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  margin-bottom: 20px;
}

.action-btn {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Recent Section */
.recent-section h2 {
  font-size: 1.3rem;
  margin-bottom: 20px;
}

.empty-state {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 60px;
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 15px;
}

.empty-state h4 {
  font-size: 1.2rem;
  margin-bottom: 8px;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.5);
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid,
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 968px) {
  .sidebar {
    display: none;
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .plan-card-dashboard {
    flex-direction: column;
    text-align: center;
    gap: 25px;
  }
  
  .plan-actions-dash {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .stats-grid,
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .main-content {
    padding: 20px;
  }
}

/* Cancel Button */
.btn-cancel {
  padding: 12px 25px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background: transparent;
  color: #ff6b6b;
  border: 1px solid #ff6b6b;
}

.btn-cancel:hover {
  background: rgba(255, 107, 107, 0.1);
}

/* Reactivate Button */
.btn-reactivate {
  padding: 12px 25px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background: #4CAF50;
  color: #fff;
  text-decoration: none;
  border: none;
}

.btn-reactivate:hover {
  background: #45a049;
}

/* Plan Actions */
.plan-actions-dash {
  display: flex;
  gap: 15px;
  align-items: center;
}

/* Canceled Badge */
.plan-badge-large.canceled {
  background: linear-gradient(135deg, #ff6b6b, #ee5253);
}

.canceled-tag {
  font-size: 0.7rem;
  margin-left: 10px;
  opacity: 0.8;
}

.cancel-notice {
  color: #ff6b6b !important;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  max-width: 450px;
  width: 100%;
  text-align: center;
}

.modal-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.modal h3 {
  font-size: 1.5rem;
  margin-bottom: 15px;
}

.modal p {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 25px;
}

.cancel-info {
  text-align: left;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 25px;
  list-style: none;
}

.cancel-info li {
  padding: 8px 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.cancel-info li::before {
  content: "•";
  color: #ff6b6b;
  margin-right: 10px;
}

.modal-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.btn-keep {
  padding: 15px 30px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
  color: #000;
  border: none;
}

.btn-keep:hover {
  transform: translateY(-2px);
}

.btn-keep:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm-cancel {
  padding: 15px 30px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: transparent;
  color: #ff6b6b;
  border: 1px solid #ff6b6b;
}

.btn-confirm-cancel:hover {
  background: rgba(255, 107, 107, 0.1);
}

.btn-confirm-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 500px) {
  .modal-actions {
    flex-direction: column;
  }
  
  .modal {
    padding: 30px 20px;
  }
}
</style>
