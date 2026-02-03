<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans, hasAccess } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const loading = ref(true)

// Estados dos alertas
const alerts = ref([])
const alertHistory = ref([])
const activeTab = ref('config')
const refreshInterval = ref(null)

// Modal de novo alerta
const showNewAlertModal = ref(false)
const newAlert = ref({
  name: '',
  type: 'crypto',
  symbol: '',
  condition: 'price_above',
  target_value: 0
})

// Dados de mercado para seleção
const marketData = ref({ crypto: [], acoes: [], forex: [] })

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { 
    router.push('/login')
    return 
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  // Verificar acesso aos Alertas (Pro/Elite)
  const hasAlertsAccess = await hasAccess(subscription.value, 'alerts', session.user.id)
  if (!hasAlertsAccess) {
    alert('❌ Acesso Negado!\n\nSistema de Alertas está disponível apenas para os planos Pro e Elite.')
    router.push('/pricing')
    return
  }
  
  await loadAlerts()
  await loadMarketData()
  
  // Auto-refresh a cada 30 segundos
  refreshInterval.value = setInterval(() => {
    loadAlerts()
  }, 30000)
  
  loading.value = false
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

const loadAlerts = async () => {
  try {
    // Carregar configurações de alertas
    const { data: alertsData, error: alertsError } = await supabase
      .from('alerts')
      .select('*')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })
    
    if (alertsError) throw alertsError
    alerts.value = alertsData || []
    
    // Carregar histórico
    const { data: historyData, error: historyError } = await supabase
      .from('alerts_history')
      .select('*')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })
      .limit(50)
    
    if (historyError) throw historyError
    alertHistory.value = historyData || []
    
  } catch (error) {
    console.error('Erro ao carregar alertas:', error)
  }
}

const loadMarketData = async () => {
  try {
    const [cryptoRes, acoesRes, forexRes] = await Promise.all([
      fetch('/api/market?type=crypto'),
      fetch('/api/market?type=acoes'),
      fetch('/api/market?type=forex')
    ])
    
    const [crypto, acoes, forex] = await Promise.all([
      cryptoRes.json(),
      acoesRes.json(),
      forexRes.json()
    ])
    
    marketData.value = {
      crypto: crypto.data || [],
      acoes: acoes.data || [],
      forex: forex.data || []
    }
    
  } catch (error) {
    console.error('Erro ao carregar dados de mercado:', error)
  }
}

const createAlert = async () => {
  try {
    loading.value = true
    
    const { error } = await supabase
      .from('alerts_config')
      .insert([{
        user_id: user.value.id,
        name: newAlert.value.name,
        type: newAlert.value.type,
        symbol: newAlert.value.symbol,
        condition: newAlert.value.condition,
        target_value: newAlert.value.target_value
      }])
    
    if (error) throw error
    
    showNewAlertModal.value = false
    newAlert.value = {
      name: '',
      type: 'crypto',
      symbol: '',
      condition: 'price_above',
      target_value: 0
    }
    
    await loadAlerts()
    
  } catch (error) {
    alert('Erro ao criar alerta: ' + error.message)
  } finally {
    loading.value = false
  }
}

const toggleAlert = async (alertId, isActive) => {
  try {
    const { error } = await supabase
      .from('alerts_config')
      .update({ is_active: !isActive })
      .eq('id', alertId)
    
    if (error) throw error
    await loadAlerts()
    
  } catch (error) {
    console.error('Erro ao alternar alerta:', error)
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

const markAsRead = async (historyId) => {
  try {
    const { error } = await supabase
      .from('alerts_history')
      .update({ is_read: true })
      .eq('id', historyId)
    
    if (error) throw error
    await loadAlerts()
    
  } catch (error) {
    console.error('Erro ao marcar como lido:', error)
  }
}

const formatDateTime = (dateStr) => {
  return new Date(dateStr).toLocaleString('pt-BR')
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { 
    style: 'currency', 
    currency: 'BRL' 
  }).format(value || 0)
}

const getConditionText = (condition) => {
  const conditions = {
    price_above: 'Preço acima de',
    price_below: 'Preço abaixo de',
    price_change_up: 'Alta de',
    price_change_down: 'Queda de'
  }
  return conditions[condition] || condition
}

const getSymbolsForType = (type) => {
  const typeMap = {
    crypto: 'crypto',
    stock: 'acoes',
    forex: 'forex'
  }
  return marketData.value[typeMap[type]] || []
}

const logout = async () => { await supabase.auth.signOut(); router.push('/') }
const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value }
const navigateTo = (path) => { router.push(path); mobileMenuOpen.value = false }
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
        <router-link to="/dashboard" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
          Dashboard
        </router-link>
        
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
            <line x1="9" y1="9" x2="9.01" y2="9"/>
            <line x1="15" y1="9" x2="15.01" y2="9"/>
          </svg>
          BET
        </router-link>
        <router-link to="/trade" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22,6 13.5,14.5 8.5,9.5 2,16"/>
            <polyline points="16,6 22,6 22,12"/>
          </svg>
          TRADE
        </router-link>
        <router-link to="/paper-trading" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          Paper Trading
        </router-link>
        <router-link to="/cartola" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="3"/>
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
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header Mobile -->
      <header class="header-mobile">
        <button @click="toggleMobileMenu" class="menu-toggle">
          <span></span>
          <span></span>
          <span></span>
        </button>
        <img src="/logo.webp" alt="ODINENX" class="logo-mobile" />
        <div class="user-menu">
          <span class="plan-badge">{{ currentPlan.name }}</span>
          <button @click="logout" class="logout-btn">Sair</button>
        </div>
      </header>

      <div class="content">
        <!-- Header -->
        <div class="page-header">
          <div>
            <h1>🔔 Alertas</h1>
            <p>Notificações em tempo real</p>
          </div>
          <div class="header-actions">
            <button @click="showNewAlertModal = true" class="btn btn-primary">
              + Novo Alerta
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading">
          <div class="loading-spinner"></div>
          <p>Carregando alertas...</p>
        </div>

        <!-- Tabs -->
        <div v-if="!loading" class="tabs">
          <div class="tab-buttons">
            <button 
              :class="['tab-btn', { active: activeTab === 'config' }]"
              @click="activeTab = 'config'"
            >
              Configurações
            </button>
            <button 
              :class="['tab-btn', { active: activeTab === 'history' }]"
              @click="activeTab = 'history'"
            >
              Histórico
            </button>
          </div>

          <!-- Tab Configurações -->
          <div v-if="activeTab === 'config'" class="tab-content">
            <div v-if="alerts.length === 0" class="empty-state">
              <p>🔕 Nenhum alerta configurado</p>
              <p>Crie seu primeiro alerta para receber notificações</p>
            </div>
            
            <div v-else class="alerts-grid">
              <div v-for="alert in alerts" :key="alert.id" class="alert-card">
                <div class="alert-header">
                  <div class="alert-info">
                    <h3>{{ alert.name }}</h3>
                    <p class="alert-condition">
                      {{ alert.symbol }} - {{ getConditionText(alert.condition) }} 
                      {{ formatCurrency(alert.target_value) }}
                    </p>
                  </div>
                  <div class="alert-status">
                    <button 
                      @click="toggleAlert(alert.id, alert.is_active)"
                      :class="['status-toggle', { active: alert.is_active }]"
                    >
                      {{ alert.is_active ? 'Ativo' : 'Inativo' }}
                    </button>
                  </div>
                </div>
                
                <div class="alert-details">
                  <p><strong>Tipo:</strong> {{ alert.type.toUpperCase() }}</p>
                  <p><strong>Valor Atual:</strong> {{ formatCurrency(alert.current_value) }}</p>
                  <p><strong>Disparado:</strong> {{ alert.triggered_count }}x</p>
                  <p><strong>Criado:</strong> {{ formatDateTime(alert.created_at) }}</p>
                </div>
                
                <div class="alert-actions">
                  <button @click="deleteAlert(alert.id)" class="btn btn-danger btn-sm">
                    Excluir
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab Histórico -->
          <div v-if="activeTab === 'history'" class="tab-content">
            <div v-if="alertHistory.length === 0" class="empty-state">
              <p>📭 Nenhum alerta disparado ainda</p>
              <p>Quando seus alertas forem acionados, aparecerão aqui</p>
            </div>
            
            <div v-else class="history-list">
              <div 
                v-for="item in alertHistory" 
                :key="item.id" 
                :class="['history-item', { unread: !item.is_read }]"
                @click="markAsRead(item.id)"
              >
                <div class="history-icon">
                  {{ item.is_read ? '📬' : '📭' }}
                </div>
                <div class="history-content">
                  <p class="history-message">{{ item.message }}</p>
                  <p class="history-meta">
                    {{ formatDateTime(item.created_at) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Mobile Menu -->
    <div v-if="mobileMenuOpen" class="mobile-menu-overlay" @click="toggleMobileMenu">
      <nav class="mobile-menu">
        <a @click="navigateTo('/dashboard')">Dashboard</a>
        <a @click="navigateTo('/bet')">BET</a>
        <a @click="navigateTo('/trade')">TRADE</a>
        <a @click="navigateTo('/paper-trading')">Paper Trading</a>
        <a @click="navigateTo('/cartola')">Cartola FC</a>
        <a @click="navigateTo('/alerts')" class="active">Alertas</a>
        <a @click="navigateTo('/history')">Histórico</a>
      </nav>
    </div>

    <!-- Modal de Novo Alerta -->
    <div v-if="showNewAlertModal" class="modal-overlay" @click="showNewAlertModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>🔔 Criar Alerta</h3>
          <button @click="showNewAlertModal = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Nome do Alerta:</label>
            <input v-model="newAlert.name" type="text" placeholder="Ex: Bitcoin acima de R$ 350.000" />
          </div>
          
          <div class="form-group">
            <label>Tipo:</label>
            <select v-model="newAlert.type">
              <option value="crypto">Criptomoeda</option>
              <option value="stock">Ação</option>
              <option value="forex">Forex</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Ativo:</label>
            <select v-model="newAlert.symbol">
              <option value="">Selecione um ativo...</option>
              <option 
                v-for="asset in getSymbolsForType(newAlert.type)" 
                :key="asset.simbolo" 
                :value="asset.simbolo"
              >
                {{ asset.simbolo }} - {{ asset.nome }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Condição:</label>
            <select v-model="newAlert.condition">
              <option value="price_above">Preço acima de</option>
              <option value="price_below">Preço abaixo de</option>
              <option value="price_change_up">Alta de (%)</option>
              <option value="price_change_down">Queda de (%)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Valor:</label>
            <input v-model="newAlert.target_value" type="number" min="0" step="0.01" />
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showNewAlertModal = false" class="btn btn-outline">Cancelar</button>
          <button @click="createAlert" class="btn btn-primary" :disabled="!newAlert.name || !newAlert.symbol">
            Criar Alerta
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 2rem;
}

.tab-buttons {
  display: flex;
  border-bottom: 1px solid rgba(0, 217, 255, 0.1);
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  background: none;
  border: none;
  color: #8892b0;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn.active,
.tab-btn:hover {
  color: #00d9ff;
  background: rgba(0, 217, 255, 0.1);
}

.tab-content {
  padding: 2rem;
}

/* Base nav-icon styles */
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.alerts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.alert-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.alert-info h3 {
  color: white;
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
}

.alert-condition {
  color: #8892b0;
  margin: 0;
  font-size: 0.9rem;
}

.status-toggle {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(0, 217, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
  color: #8892b0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.3s ease;
}

.status-toggle.active {
  background: rgba(0, 217, 255, 0.1);
  border-color: #00d9ff;
  color: #00d9ff;
}

.alert-details p {
  margin: 0.5rem 0;
  color: #ccd6f6;
  font-size: 0.9rem;
}

.alert-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-item.unread {
  border-color: #00d9ff;
  background: rgba(0, 217, 255, 0.05);
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.history-icon {
  font-size: 1.5rem;
  width: 40px;
  text-align: center;
}

.history-content {
  flex: 1;
}

.history-message {
  color: white;
  margin: 0 0 0.5rem 0;
  font-weight: 500;
}

.history-meta {
  color: #8892b0;
  margin: 0;
  font-size: 0.8rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #8892b0;
}

.empty-state p:first-child {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
}

/* Modal Styles */
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
}

.modal {
  background: #1a1a2e;
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(0, 217, 255, 0.1);
}

.modal-header h3 {
  color: white;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #8892b0;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  color: #ccd6f6;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #00d9ff;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid rgba(0, 217, 255, 0.1);
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .alerts-grid {
    grid-template-columns: 1fr;
  }
  
  .modal {
    width: 95%;
  }
  
  /* Fix mobile navigation icons */
  .nav-icon {
    width: 20px;
    height: 20px;
  }
  
  /* Fix mobile menu layout */
  .mobile-menu {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0a0a0a;
    border-top-left-radius: 25px;
    border-top-right-radius: 25px;
    padding: 25px;
    z-index: 999;
    transform: translateY(100%);
    transition: transform 0.3s ease;
  }
  
  .mobile-menu.open {
    transform: translateY(0);
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
}
</style>