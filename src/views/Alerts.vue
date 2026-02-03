<template>
  <div class="app-layout">
    <!-- Sidebar Desktop -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <img src="/logo.webp" alt="ODINENX" class="sidebar-logo" />
      </div>
      <nav class="sidebar-nav">
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="10,8 16,12 10,16 10,8"/>
          </svg>
          BET
        </router-link>
        <router-link to="/trade" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="2" x2="12" y2="6"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
            <line x1="2" y1="12" x2="6" y2="12"/>
            <line x1="18" y1="12" x2="22" y2="12"/>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
          </svg>
          TRADE
        </router-link>
        <router-link to="/paper-trading" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          Paper Trading
        </router-link>
        <router-link to="/cartola" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <path d="M16 10a4 4 0 0 1-8 0"/>
          </svg>
          Cartola FC
        </router-link>

        <div class="nav-category">Acompanhamento</div>
        <router-link to="/alerts" class="nav-item active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          Alertas
        </router-link>
        <router-link to="/history" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12,6 12,12 16,14"/>
          </svg>
          Histórico
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="plan-badge-sidebar">{{ currentPlan.name }}</div>
        <button @click="logout" class="logout-btn">Sair</button>
      </div>
    </aside>

    <!-- Header Mobile -->
    <header class="header-mobile">
      <button @click="toggleMobileMenu" class="menu-toggle">
        <span></span><span></span><span></span>
      </button>
      <img src="/logo.webp" alt="ODINENX" class="logo-mobile" />
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="page-header">
        <h1>🔔 Alertas</h1>
        <p>Configure notificações para seus ativos favoritos</p>
      </div>

      <!-- Alert Creation Form -->
      <div class="alert-form-card">
        <h3>Criar Novo Alerta</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Nome do Alerta</label>
            <input 
              v-model="newAlert.name" 
              type="text" 
              placeholder="Ex: Bitcoin acima de R$ 350.000"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label>Tipo</label>
            <select v-model="newAlert.type" class="form-select">
              <option value="crypto">Criptomoeda</option>
              <option value="stock">Ação</option>
              <option value="forex">Forex</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Símbolo</label>
            <input 
              v-model="newAlert.symbol" 
              type="text" 
              placeholder="Ex: BTC, PETR4"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label>Condição</label>
            <select v-model="newAlert.condition" class="form-select">
              <option value="price_above">Preço acima de</option>
              <option value="price_below">Preço abaixo de</option>
              <option value="change_up">Alta de (%)</option>
              <option value="change_down">Queda de (%)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Valor</label>
            <input 
              v-model="newAlert.target_value" 
              type="number" 
              min="0" 
              step="0.01"
              placeholder="0.00"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <button 
              @click="createAlert" 
              class="btn-primary"
              :disabled="!canCreateAlert"
            >
              Criar Alerta
            </button>
          </div>
        </div>
      </div>

      <!-- Alerts List -->
      <div class="alerts-section">
        <h3>Seus Alertas</h3>
        
        <div v-if="alerts.length === 0" class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <p>Nenhum alerta configurado</p>
          <span>Crie seu primeiro alerta acima</span>
        </div>

        <div v-else class="alerts-list">
          <div v-for="alert in alerts" :key="alert.id" class="alert-item">
            <div class="alert-info">
              <h4>{{ alert.name }}</h4>
              <p>{{ alert.symbol }} - {{ getConditionText(alert.condition) }} {{ alert.target_value }}</p>
              <span class="alert-status" :class="alert.active ? 'active' : 'inactive'">
                {{ alert.active ? 'Ativo' : 'Inativo' }}
              </span>
            </div>
            <div class="alert-actions">
              <button @click="toggleAlert(alert)" class="btn-toggle">
                {{ alert.active ? 'Desativar' : 'Ativar' }}
              </button>
              <button @click="deleteAlert(alert.id)" class="btn-delete">
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Mobile Menu -->
    <div v-if="mobileMenuOpen" class="mobile-menu-overlay" @click="toggleMobileMenu">
      <nav class="mobile-menu">
        <div class="mobile-menu-header">
          <img src="/logo.webp" alt="ODINENX" class="mobile-logo" />
        </div>
        <div class="mobile-nav">
          <a @click="navigateTo('/dashboard')" class="mobile-nav-item">Dashboard</a>
          <a @click="navigateTo('/bet')" class="mobile-nav-item">BET</a>
          <a @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</a>
          <a @click="navigateTo('/paper-trading')" class="mobile-nav-item">Paper Trading</a>
          <a @click="navigateTo('/cartola')" class="mobile-nav-item">Cartola FC</a>
          <a @click="navigateTo('/alerts')" class="mobile-nav-item active">Alertas</a>
          <a @click="navigateTo('/history')" class="mobile-nav-item">Histórico</a>
        </div>
        <button @click="logout" class="mobile-logout">Sair</button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const alerts = ref([])
const mobileMenuOpen = ref(false)

const newAlert = ref({
  name: '',
  type: 'crypto',
  symbol: '',
  condition: 'price_above',
  target_value: ''
})

// Computed
const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

const canCreateAlert = computed(() => {
  return newAlert.value.name && 
         newAlert.value.symbol && 
         newAlert.value.target_value && 
         parseFloat(newAlert.value.target_value) > 0
})

// Methods
const loadAlerts = async () => {
  if (!user.value) return
  
  try {
    const { data, error } = await supabase
      .from('alerts')
      .select('*')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })
    
    if (error) throw error
    alerts.value = data || []
  } catch (error) {
    console.error('Erro ao carregar alertas:', error)
    alerts.value = []
  }
}

const createAlert = async () => {
  if (!canCreateAlert.value) return
  
  try {
    const alertData = {
      user_id: user.value.id,
      name: newAlert.value.name,
      type: newAlert.value.type,
      symbol: newAlert.value.symbol.toUpperCase(),
      condition: newAlert.value.condition,
      target_value: parseFloat(newAlert.value.target_value),
      active: true,
      created_at: new Date().toISOString()
    }
    
    const { error } = await supabase
      .from('alerts')
      .insert(alertData)
    
    if (error) throw error
    
    // Reset form
    newAlert.value = {
      name: '',
      type: 'crypto',
      symbol: '',
      condition: 'price_above',
      target_value: ''
    }
    
    await loadAlerts()
  } catch (error) {
    console.error('Erro ao criar alerta:', error)
  }
}

const toggleAlert = async (alert) => {
  try {
    const { error } = await supabase
      .from('alerts')
      .update({ active: !alert.active })
      .eq('id', alert.id)
    
    if (error) throw error
    await loadAlerts()
  } catch (error) {
    console.error('Erro ao alterar status do alerta:', error)
  }
}

const deleteAlert = async (alertId) => {
  if (!confirm('Tem certeza que deseja excluir este alerta?')) return
  
  try {
    const { error } = await supabase
      .from('alerts')
      .delete()
      .eq('id', alertId)
    
    if (error) throw error
    await loadAlerts()
  } catch (error) {
    console.error('Erro ao excluir alerta:', error)
  }
}

const getConditionText = (condition) => {
  const conditions = {
    'price_above': 'acima de',
    'price_below': 'abaixo de',
    'change_up': 'alta de',
    'change_down': 'queda de'
  }
  return conditions[condition] || condition
}

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const navigateTo = (path) => {
  router.push(path)
  mobileMenuOpen.value = false
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/login')
}

// Lifecycle
onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  await loadAlerts()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
  color: white;
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
  overflow-y: auto;
}

.nav-category {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.35);
  padding: 15px 15px 8px;
  font-weight: 600;
}

.nav-category:first-child {
  padding-top: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  transition: all 0.3s;
  font-weight: 500;
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
  width: 20px;
  height: 20px;
  flex-shrink: 0;
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
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

/* Mobile Header */
.header-mobile {
  display: none;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.menu-toggle {
  background: none;
  border: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
  padding: 8px;
}

.menu-toggle span {
  width: 20px;
  height: 2px;
  background: #fff;
  border-radius: 1px;
  transition: all 0.3s;
}

.logo-mobile {
  height: 30px;
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 30px;
}

.page-header {
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.page-header p {
  color: rgba(255, 255, 255, 0.5);
}

/* Alert Form */
.alert-form-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.alert-form-card h3 {
  margin: 0 0 1.5rem 0;
  color: #fff;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  align-items: end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.form-input,
.form-select {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: rgba(0, 217, 255, 0.5);
}

.btn-primary {
  padding: 12px 24px;
  background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Alerts Section */
.alerts-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
}

.alerts-section h3 {
  margin: 0 0 1.5rem 0;
  color: #fff;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: rgba(255, 255, 255, 0.5);
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 1rem;
  opacity: 0.3;
}

.empty-state p {
  font-size: 1.1rem;
  margin: 0 0 0.5rem 0;
}

.empty-state span {
  font-size: 0.9rem;
  opacity: 0.7;
}

/* Alerts List */
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  transition: all 0.3s;
}

.alert-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.alert-info h4 {
  margin: 0 0 0.5rem 0;
  color: #fff;
  font-size: 1.1rem;
}

.alert-info p {
  margin: 0 0 0.5rem 0;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.alert-status {
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.alert-status.active {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.alert-status.inactive {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.alert-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-toggle,
.btn-delete {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.btn-toggle {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.btn-toggle:hover {
  background: rgba(59, 130, 246, 0.3);
}

.btn-delete {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.3);
}

/* Mobile Menu */
.mobile-menu-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 1000;
}

.mobile-menu {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #0a0a0a;
  border-top-left-radius: 25px;
  border-top-right-radius: 25px;
  padding: 25px;
  transform: translateY(100%);
  transition: transform 0.3s ease;
}

.mobile-menu.open {
  transform: translateY(0);
}

.mobile-menu-header {
  text-align: center;
  margin-bottom: 20px;
}

.mobile-logo {
  height: 35px;
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-nav-item {
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.mobile-logout {
  width: 100%;
  margin-top: 15px;
  padding: 15px;
  background: transparent;
  border: 1px solid #ef4444;
  border-radius: 12px;
  color: #ef4444;
  font-weight: 600;
  cursor: pointer;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  
  .header-mobile {
    display: flex;
  }
  
  .mobile-menu-overlay {
    display: block;
  }
  
  .main-content {
    margin-left: 0;
    margin-top: 70px;
    padding: 20px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .alert-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .alert-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>