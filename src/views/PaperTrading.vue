<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans, hasAccess, isAdmin as checkIsAdmin } from '../lib/stripe'
import { 
  getPaperWallet, 
  getPaperPositions, 
  getPaperTrades, 
  getPaperStats,
  executeBuy,
  executeSell,
  updatePositionPrices
} from '../lib/paperTrading'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const userIsAdmin = ref(false)

// Estados do Paper Trading
const wallet = ref(null)
const positions = ref([])
const trades = ref([])
const stats = ref(null)
const marketData = ref({ crypto: [], acoes: [], forex: [] })
const loading = ref(true)
const refreshInterval = ref(null)

// Modais
const showBuyModal = ref(false)
const showSellModal = ref(false)
const selectedAsset = ref(null)
const tradeForm = ref({
  symbol: '',
  type: '',
  quantity: 0,
  price: 0,
  reason: ''
})

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { 
    router.push('/login')
    return 
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  userIsAdmin.value = await checkIsAdmin(session.user.id)
  
  // Verificar acesso ao Paper Trading (admin ignora)
  if (!userIsAdmin.value) {
    const hasPaperAccess = await hasAccess(subscription.value, 'paperTrading', session.user.id)
    if (!hasPaperAccess) {
      alert('❌ Acesso Negado!\n\nPaper Trading está disponível apenas para os planos Pro e Elite.')
      router.push('/pricing')
      return
    }
  }
  
  await loadPaperTradingData()
  await loadMarketData()
  
  // Auto-refresh a cada 30 segundos
  refreshInterval.value = setInterval(async () => {
    await updatePositionPrices(user.value.id)
    await loadPaperTradingData()
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

const loadPaperTradingData = async () => {
  try {
    const [walletData, positionsData, tradesData, statsData] = await Promise.all([
      getPaperWallet(user.value.id),
      getPaperPositions(user.value.id),
      getPaperTrades(user.value.id, 20),
      getPaperStats(user.value.id)
    ])
    
    wallet.value = walletData
    positions.value = positionsData
    trades.value = tradesData
    stats.value = statsData
    
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
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
    console.error('Erro ao carregar mercado:', error)
  }
}

const openBuyModal = (asset, type) => {
  selectedAsset.value = asset
  tradeForm.value = {
    symbol: asset.simbolo,
    type,
    quantity: 0,
    price: asset.preco,
    reason: ''
  }
  showBuyModal.value = true
}

const openSellModal = (position) => {
  selectedAsset.value = position
  tradeForm.value = {
    symbol: position.symbol,
    type: position.type,
    quantity: 0,
    price: position.current_price,
    reason: ''
  }
  showSellModal.value = true
}

const executeBuyOrder = async () => {
  try {
    loading.value = true
    
    await executeBuy(user.value.id, tradeForm.value)
    
    showBuyModal.value = false
    await loadPaperTradingData()
    
  } catch (error) {
    alert('Erro: ' + error.message)
  } finally {
    loading.value = false
  }
}

const executeSellOrder = async () => {
  try {
    loading.value = true
    
    await executeSell(user.value.id, tradeForm.value)
    
    showSellModal.value = false
    await loadPaperTradingData()
    
  } catch (error) {
    alert('Erro: ' + error.message)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { 
    style: 'currency', 
    currency: 'BRL' 
  }).format(value || 0)
}

const formatPercent = (value) => {
  const color = value >= 0 ? '#00ff88' : '#ff4444'
  const sign = value >= 0 ? '+' : ''
  return `<span style="color: ${color}">${sign}${(value || 0).toFixed(2)}%</span>`
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
        <router-link to="/paper-trading" class="nav-item active">
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
        <router-link to="/alerts" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 2 0 0 1-3.46 0"/>
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
            <h1>📈 Paper Trading</h1>
            <p>Simule operações sem risco real</p>
          </div>
          <div class="header-actions">
            <button @click="loadPaperTradingData" class="btn btn-outline">
              🔄 Atualizar
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading">
          <div class="loading-spinner"></div>
          <p>Carregando dados...</p>
        </div>

        <!-- Stats Cards -->
        <div v-if="!loading && stats" class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-info">
              <p class="stat-label">Saldo Disponível</p>
              <p class="stat-value">{{ formatCurrency(stats.balance) }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <p class="stat-label">Patrimônio Total</p>
              <p class="stat-value">{{ formatCurrency(stats.totalPortfolio) }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">📈</div>
            <div class="stat-info">
              <p class="stat-label">Retorno Total</p>
              <p class="stat-value" v-html="formatPercent(stats.totalReturn)"></p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-info">
              <p class="stat-label">Taxa de Acerto</p>
              <p class="stat-value" v-html="formatPercent(stats.winRate)"></p>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          <div class="tab-buttons">
            <button class="tab-btn active">Posições</button>
            <button class="tab-btn">Mercado</button>
            <button class="tab-btn">Histórico</button>
          </div>

          <!-- Posições Tab -->
          <div class="tab-content">
            <div v-if="positions.length === 0" class="empty-state">
              <p>📈 Nenhuma posição em aberto</p>
              <p>Compre alguns ativos na aba Mercado</p>
            </div>
            
            <div v-else class="positions-grid">
              <div v-for="position in positions" :key="position.id" class="position-card">
                <div class="position-header">
                  <span class="symbol">{{ position.symbol }}</span>
                  <span class="type-badge">{{ position.type }}</span>
                </div>
                
                <div class="position-info">
                  <p>Quantidade: {{ position.quantity }}</p>
                  <p>Preço Médio: {{ formatCurrency(position.avg_price) }}</p>
                  <p>Preço Atual: {{ formatCurrency(position.current_price) }}</p>
                  <p>Valor de Mercado: {{ formatCurrency(position.market_value) }}</p>
                  <p class="profit-loss" v-html="`P&L: ${formatCurrency(position.profit_loss)} (${formatPercent(position.profit_loss_pct)})`"></p>
                </div>
                
                <div class="position-actions">
                  <button @click="openSellModal(position)" class="btn btn-danger">Vender</button>
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
        <a @click="navigateTo('/paper-trading')" class="active">Paper Trading</a>
        <a @click="navigateTo('/cartola')">Cartola FC</a>
        <a @click="navigateTo('/alerts')">Alertas</a>
        <a @click="navigateTo('/history')">Histórico</a>
      </nav>
    </div>

    <!-- Modal de Compra -->
    <div v-if="showBuyModal" class="modal-overlay" @click="showBuyModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>💰 Comprar {{ tradeForm.symbol }}</h3>
          <button @click="showBuyModal = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Quantidade:</label>
            <input v-model="tradeForm.quantity" type="number" min="0" step="0.001" />
          </div>
          
          <div class="form-group">
            <label>Preço:</label>
            <input v-model="tradeForm.price" type="number" min="0" step="0.01" />
          </div>
          
          <div class="form-group">
            <label>Total:</label>
            <p class="total-value">{{ formatCurrency(tradeForm.quantity * tradeForm.price) }}</p>
          </div>
          
          <div class="form-group">
            <label>Motivo da operação:</label>
            <textarea v-model="tradeForm.reason" placeholder="Por que está comprando?"></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showBuyModal = false" class="btn btn-outline">Cancelar</button>
          <button @click="executeBuyOrder" class="btn btn-primary">Comprar</button>
        </div>
      </div>
    </div>

    <!-- Modal de Venda -->
    <div v-if="showSellModal" class="modal-overlay" @click="showSellModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>💸 Vender {{ tradeForm.symbol }}</h3>
          <button @click="showSellModal = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Quantidade Disponível:</label>
            <p>{{ selectedAsset?.quantity || 0 }}</p>
          </div>
          
          <div class="form-group">
            <label>Quantidade a Vender:</label>
            <input v-model="tradeForm.quantity" type="number" min="0" :max="selectedAsset?.quantity || 0" step="0.001" />
          </div>
          
          <div class="form-group">
            <label>Preço:</label>
            <input v-model="tradeForm.price" type="number" min="0" step="0.01" />
          </div>
          
          <div class="form-group">
            <label>Total:</label>
            <p class="total-value">{{ formatCurrency(tradeForm.quantity * tradeForm.price) }}</p>
          </div>
          
          <div class="form-group">
            <label>Motivo da operação:</label>
            <textarea v-model="tradeForm.reason" placeholder="Por que está vendendo?"></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showSellModal = false" class="btn btn-outline">Cancelar</button>
          <button @click="executeSellOrder" class="btn btn-danger">Vender</button>
        </div>
      </div>
    </div>

    <!-- Bottom Navigation Mobile -->
    <BottomNav :showAdmin="userIsAdmin" />
  </div>
</template>

<style scoped>
/* Base styles */
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a, #1a1a1a, #2d2d2d);
  color: white;
}

.nav-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 2rem;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.7);
  padding: 1rem 2rem;
  border-radius: 12px;
  margin: 0 1rem;
  transition: all 0.3s ease;
}

.nav-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.nav-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.15);
}

.nav-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(0, 217, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-label {
  color: #8892b0;
  font-size: 0.9rem;
  margin: 0 0 0.5rem 0;
}

.stat-value {
  color: white;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.tabs {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
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

.positions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.position-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
}

.position-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.symbol {
  font-size: 1.2rem;
  font-weight: 700;
  color: #00d9ff;
}

.type-badge {
  background: rgba(0, 217, 255, 0.1);
  color: #00d9ff;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  text-transform: uppercase;
}

.position-info p {
  margin: 0.5rem 0;
  color: #ccd6f6;
  font-size: 0.9rem;
}

.profit-loss {
  font-weight: 600;
  font-size: 1rem !important;
}

.position-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
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
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 1rem;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #00d9ff;
}

.total-value {
  color: #00d9ff;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid rgba(0, 217, 255, 0.1);
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .positions-grid {
    grid-template-columns: 1fr;
  }
  
  .mobile-menu-overlay {
    display: none;
  }
  
  .main-content {
    padding-bottom: 85px;
  }
}
</style>