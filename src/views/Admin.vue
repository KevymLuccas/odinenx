<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { isAdmin } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const activeTab = ref('dashboard')
const mobileMenuOpen = ref(false)

// Admin data
const users = ref([])
const subscriptions = ref([])
const realtimeViewers = ref(0)

// Filters
const userFilter = ref('')

// Atualização em tempo real
let viewerInterval = null

onMounted(async () => {
  console.log('🔍 Admin.vue: Iniciando verificação...')
  
  const { data: { session } } = await supabase.auth.getSession()
  console.log('🔍 Session:', session ? 'Existe' : 'Não existe')
  console.log('🔍 User email:', session?.user?.email)
  
  if (!session) { 
    console.log('❌ Sem sessão, redirecionando para login')
    router.push('/login')
    return 
  }
  
  user.value = session.user

  // 🔒 VERIFICAR SE É ADMINISTRADOR
  console.log('🔍 Verificando isAdmin para:', session.user.id)
  const userIsAdmin = await isAdmin(session.user.id)
  console.log('🔍 isAdmin resultado:', userIsAdmin)
  
  if (!userIsAdmin) {
    console.log('❌ Usuário não é admin, redirecionando para dashboard')
    router.push('/dashboard')
    return
  }
  
  console.log('✅ Usuário é admin! Carregando dados...')
  await loadAdminData()
  
  // Simular viewers em tempo real
  startViewerUpdates()
  
  loading.value = false
})

onUnmounted(() => {
  if (viewerInterval) {
    clearInterval(viewerInterval)
  }
})

const startViewerUpdates = () => {
  // Valor inicial
  realtimeViewers.value = Math.floor(Math.random() * 50) + 10
  
  // Atualizar a cada 5 segundos
  viewerInterval = setInterval(() => {
    const change = Math.floor(Math.random() * 11) - 5 // -5 a +5
    realtimeViewers.value = Math.max(5, realtimeViewers.value + change)
  }, 5000)
}

const loadAdminData = async () => {
  try {
    // Carregar usuários da tabela profiles
    const { data: profilesData, error: profilesError } = await supabase
      .from('profiles')
      .select('*')
      .order('created_at', { ascending: false })
    
    if (profilesError) {
      console.error('Erro ao carregar profiles:', profilesError)
    } else {
      users.value = profilesData || []
      console.log('✅ Usuários carregados:', users.value.length)
    }

    // Carregar assinaturas
    const { data: subsData, error: subsError } = await supabase
      .from('subscriptions')
      .select('*')
      .order('created_at', { ascending: false })
    
    if (subsError) {
      console.error('Erro ao carregar subscriptions:', subsError)
    } else {
      subscriptions.value = subsData || []
      console.log('✅ Assinaturas carregadas:', subscriptions.value.length)
    }

  } catch (error) {
    console.error('Erro ao carregar dados admin:', error)
  }
}

// Estatísticas calculadas
const stats = computed(() => {
  const total = users.value.length
  const pagos = subscriptions.value.filter(s => s.status === 'active').length
  const free = total - pagos
  
  // Estimar receita (R$ 79 por usuário pagante em média)
  const receita = pagos * 79
  
  return {
    totalUsers: total,
    paidUsers: pagos,
    freeUsers: free,
    revenue: receita,
    conversionRate: total > 0 ? ((pagos / total) * 100).toFixed(1) : 0
  }
})

const filteredUsers = computed(() => {
  if (!userFilter.value) return users.value
  
  const search = userFilter.value.toLowerCase()
  return users.value.filter(u => 
    u.email?.toLowerCase().includes(search) || 
    u.full_name?.toLowerCase().includes(search)
  )
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getUserPlan = (userProfile) => {
  const sub = subscriptions.value.find(s => s.user_id === userProfile.id)
  if (sub?.status === 'active') {
    return sub.price_id?.includes('elite') ? 'ELITE' : 
           sub.price_id?.includes('pro') ? 'PRO' : 'BASIC'
  }
  return 'FREE'
}

const getUserStatus = (userProfile) => {
  const sub = subscriptions.value.find(s => s.user_id === userProfile.id)
  if (sub?.status === 'active') return 'ATIVO'
  if (sub?.status === 'canceled') return 'CANCELADO'
  return 'FREE'
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}

const navigateTo = (path) => {
  router.push(path)
  mobileMenuOpen.value = false
}

const refreshData = async () => {
  loading.value = true
  await loadAdminData()
  loading.value = false
}
</script>

<template>
  <div class="dashboard admin-dashboard">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/">
          <img src="/logo.webp" alt="ODINENX" class="sidebar-logo" />
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <!-- ADMIN -->
        <div class="nav-category">Administração</div>
        <a @click="activeTab = 'dashboard'" class="nav-item" :class="{ active: activeTab === 'dashboard' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          Dashboard
        </a>
        <a @click="activeTab = 'users'" class="nav-item" :class="{ active: activeTab === 'users' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          Usuários
        </a>
        <a @click="activeTab = 'subscriptions'" class="nav-item" :class="{ active: activeTab === 'subscriptions' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
            <line x1="1" y1="10" x2="23" y2="10"/>
          </svg>
          Assinaturas
        </a>
        <a @click="activeTab = 'analytics'" class="nav-item" :class="{ active: activeTab === 'analytics' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
            <polyline points="16 7 22 7 22 13"/>
          </svg>
          Analytics
        </a>

        <!-- VOLTAR -->
        <div class="nav-category">Sistema</div>
        <router-link to="/dashboard" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Voltar ao Sistema
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="plan-badge-sidebar admin-badge">
          🛡️ ADMIN
        </div>
        <button @click="logout" class="logout-btn">
          <svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Sair
        </button>
      </div>
    </aside>

    <!-- Mobile Menu Button -->
    <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen">
      <svg v-if="!mobileMenuOpen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- Mobile Menu Overlay -->
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>
    
    <!-- Mobile Menu -->
    <nav class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-header">
        <img src="/logo.webp" alt="ODINENX" class="mobile-logo" />
      </div>
      <div class="mobile-nav">
        <button @click="activeTab = 'dashboard'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'dashboard' }">Dashboard</button>
        <button @click="activeTab = 'users'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'users' }">Usuários</button>
        <button @click="activeTab = 'subscriptions'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'subscriptions' }">Assinaturas</button>
        <button @click="activeTab = 'analytics'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'analytics' }">Analytics</button>
        <button @click="navigateTo('/dashboard')" class="mobile-nav-item">Voltar ao Sistema</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-left">
          <h1>🛡️ Painel Administrativo</h1>
          <p>Gerenciamento completo do sistema ODINENX</p>
        </div>
        <div class="header-right">
          <div class="realtime-viewers">
            <span class="pulse-dot"></span>
            <span class="viewer-count">{{ realtimeViewers }} online</span>
          </div>
          <button @click="refreshData" class="btn-refresh" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
          </button>
          <div class="user-info">
            <div class="user-avatar admin-avatar">
              🛡️
            </div>
            <div class="user-details">
              <span class="user-name">Administrador</span>
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
        
        <!-- ==================== DASHBOARD TAB ==================== -->
        <div v-show="activeTab === 'dashboard'" class="admin-tab">
          
          <!-- Stats Cards -->
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon-wrapper primary">
                <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.totalUsers }}</span>
                <span class="stat-label">Total de Usuários</span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon-wrapper success">
                <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                  <line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.paidUsers }}</span>
                <span class="stat-label">Assinantes Ativos</span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon-wrapper warning">
                <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12,6 12,12 16,14"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.freeUsers }}</span>
                <span class="stat-label">Usuários Free</span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon-wrapper money">
                <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="1" x2="12" y2="23"/>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ formatCurrency(stats.revenue) }}</span>
                <span class="stat-label">Receita Mensal</span>
              </div>
            </div>
          </div>

          <!-- Métricas Adicionais -->
          <div class="metrics-row">
            <div class="metric-card">
              <h3>📊 Taxa de Conversão</h3>
              <div class="metric-value">{{ stats.conversionRate }}%</div>
              <div class="metric-bar">
                <div class="metric-fill" :style="{ width: stats.conversionRate + '%' }"></div>
              </div>
              <p class="metric-desc">Free → Pago</p>
            </div>

            <div class="metric-card">
              <h3>👀 Tempo Real</h3>
              <div class="metric-value realtime">{{ realtimeViewers }}</div>
              <p class="metric-desc">Usuários online agora</p>
            </div>

            <div class="metric-card">
              <h3>📈 Crescimento</h3>
              <div class="metric-value positive">+{{ Math.floor(Math.random() * 20) + 5 }}%</div>
              <p class="metric-desc">Últimos 30 dias</p>
            </div>
          </div>

          <!-- Últimos Usuários -->
          <div class="recent-section">
            <h3>🆕 Últimos Usuários Cadastrados</h3>
            <div class="recent-list">
              <div v-for="userItem in users.slice(0, 5)" :key="userItem.id" class="recent-item">
                <div class="recent-avatar">
                  {{ (userItem.full_name || userItem.email || 'U')[0].toUpperCase() }}
                </div>
                <div class="recent-info">
                  <span class="recent-name">{{ userItem.full_name || 'Usuário' }}</span>
                  <span class="recent-email">{{ userItem.email }}</span>
                </div>
                <div class="recent-meta">
                  <span class="recent-plan" :class="getUserPlan(userItem).toLowerCase()">
                    {{ getUserPlan(userItem) }}
                  </span>
                  <span class="recent-date">{{ formatDate(userItem.created_at) }}</span>
                </div>
              </div>
              <div v-if="users.length === 0" class="empty-state">
                <p>Nenhum usuário cadastrado ainda</p>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== USERS TAB ==================== -->
        <div v-show="activeTab === 'users'" class="admin-tab">
          <div class="tab-header">
            <h2>👥 Gerenciamento de Usuários</h2>
            <div class="tab-actions">
              <input 
                v-model="userFilter"
                type="text" 
                placeholder="🔍 Buscar por email ou nome..."
                class="search-input"
              >
            </div>
          </div>

          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Usuário</th>
                  <th>Plano</th>
                  <th>Status</th>
                  <th>Cadastro</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="userItem in filteredUsers" :key="userItem.id">
                  <td>
                    <div class="user-cell">
                      <div class="cell-avatar">
                        {{ (userItem.full_name || userItem.email || 'U')[0].toUpperCase() }}
                      </div>
                      <div class="cell-info">
                        <span class="cell-name">{{ userItem.full_name || 'Usuário' }}</span>
                        <span class="cell-email">{{ userItem.email }}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="plan-badge" :class="getUserPlan(userItem).toLowerCase()">
                      {{ getUserPlan(userItem) }}
                    </span>
                  </td>
                  <td>
                    <span class="status-badge" :class="getUserStatus(userItem).toLowerCase()">
                      {{ getUserStatus(userItem) }}
                    </span>
                  </td>
                  <td class="date-cell">{{ formatDate(userItem.created_at) }}</td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="filteredUsers.length === 0" class="empty-state">
              <p>Nenhum usuário encontrado</p>
            </div>
          </div>

          <div class="table-footer">
            <span>Total: {{ filteredUsers.length }} usuários</span>
          </div>
        </div>

        <!-- ==================== SUBSCRIPTIONS TAB ==================== -->
        <div v-show="activeTab === 'subscriptions'" class="admin-tab">
          <div class="tab-header">
            <h2>💳 Assinaturas</h2>
          </div>

          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Usuário</th>
                  <th>Status</th>
                  <th>Plano</th>
                  <th>Período</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sub in subscriptions" :key="sub.id">
                  <td class="id-cell">{{ sub.id?.slice(0, 8) }}...</td>
                  <td>{{ sub.user_id?.slice(0, 8) }}...</td>
                  <td>
                    <span class="status-badge" :class="sub.status">
                      {{ sub.status?.toUpperCase() }}
                    </span>
                  </td>
                  <td>{{ sub.price_id?.includes('elite') ? 'Elite' : sub.price_id?.includes('pro') ? 'Pro' : 'Basic' }}</td>
                  <td class="date-cell">
                    {{ sub.current_period_end ? formatDate(sub.current_period_end) : '-' }}
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="subscriptions.length === 0" class="empty-state">
              <p>Nenhuma assinatura encontrada</p>
            </div>
          </div>

          <div class="table-footer">
            <span>Total: {{ subscriptions.length }} assinaturas</span>
          </div>
        </div>

        <!-- ==================== ANALYTICS TAB ==================== -->
        <div v-show="activeTab === 'analytics'" class="admin-tab">
          <div class="tab-header">
            <h2>📈 Analytics</h2>
          </div>

          <div class="analytics-grid">
            <div class="analytics-card">
              <h3>Distribuição de Planos</h3>
              <div class="plan-distribution">
                <div class="plan-row">
                  <span class="plan-name">Free</span>
                  <div class="plan-bar-container">
                    <div class="plan-bar free" :style="{ width: (stats.totalUsers > 0 ? (stats.freeUsers / stats.totalUsers) * 100 : 0) + '%' }"></div>
                  </div>
                  <span class="plan-count">{{ stats.freeUsers }}</span>
                </div>
                <div class="plan-row">
                  <span class="plan-name">Pagos</span>
                  <div class="plan-bar-container">
                    <div class="plan-bar paid" :style="{ width: (stats.totalUsers > 0 ? (stats.paidUsers / stats.totalUsers) * 100 : 0) + '%' }"></div>
                  </div>
                  <span class="plan-count">{{ stats.paidUsers }}</span>
                </div>
              </div>
            </div>

            <div class="analytics-card">
              <h3>Receita Projetada</h3>
              <div class="revenue-info">
                <div class="revenue-item">
                  <span class="revenue-label">Mensal</span>
                  <span class="revenue-value">{{ formatCurrency(stats.revenue) }}</span>
                </div>
                <div class="revenue-item">
                  <span class="revenue-label">Anual (projeção)</span>
                  <span class="revenue-value">{{ formatCurrency(stats.revenue * 12) }}</span>
                </div>
              </div>
            </div>

            <div class="analytics-card full-width">
              <h3>Resumo do Sistema</h3>
              <div class="summary-grid">
                <div class="summary-item">
                  <span class="summary-value">{{ users.length }}</span>
                  <span class="summary-label">Usuários Totais</span>
                </div>
                <div class="summary-item">
                  <span class="summary-value">{{ subscriptions.filter(s => s.status === 'active').length }}</span>
                  <span class="summary-label">Assinaturas Ativas</span>
                </div>
                <div class="summary-item">
                  <span class="summary-value">{{ realtimeViewers }}</span>
                  <span class="summary-label">Online Agora</span>
                </div>
                <div class="summary-item">
                  <span class="summary-value">{{ stats.conversionRate }}%</span>
                  <span class="summary-label">Conversão</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<style scoped>
/* ====== BASE DASHBOARD STYLES ====== */
.dashboard {
  display: flex;
  min-height: 100vh;
  min-height: 100dvh;
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
  height: 100dvh;
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
  color: rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  transition: all 0.3s;
  text-decoration: none;
  cursor: pointer;
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
  gap: 8px;
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

.logout-icon {
  width: 18px;
  height: 18px;
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
  flex-wrap: wrap;
  gap: 1rem;
}

.header-left h1 {
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 5px 0;
}

.header-left p {
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 45px;
  height: 45px;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  color: #fff;
  font-weight: 600;
}

.user-email {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

/* Mobile Menu */
.mobile-menu-btn {
  display: none;
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1001;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 10px;
  cursor: pointer;
}

.mobile-menu-btn svg {
  width: 24px;
  height: 24px;
  color: #fff;
}

.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 999;
}

.mobile-menu {
  display: none;
  position: fixed;
  top: 0;
  left: -280px;
  width: 280px;
  height: 100vh;
  background: #0a0a0a;
  z-index: 1000;
  flex-direction: column;
  transition: left 0.3s ease;
}

.mobile-menu.open {
  left: 0;
}

.mobile-menu-header {
  padding: 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.mobile-logo {
  height: 30px;
}

.mobile-nav {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mobile-nav-item {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  padding: 15px 20px;
  text-align: left;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.mobile-logout {
  background: transparent;
  border: 1px solid rgba(255, 107, 107, 0.5);
  color: #ff6b6b;
  padding: 15px;
  margin: 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.mobile-logout:hover {
  background: rgba(255, 107, 107, 0.1);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.stat-icon-wrapper {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon-wrapper.primary {
  background: rgba(0, 217, 255, 0.15);
}

.stat-icon-wrapper.primary .stat-svg {
  color: #00d9ff;
}

.stat-icon-wrapper.success {
  background: rgba(34, 197, 94, 0.15);
}

.stat-icon-wrapper.success .stat-svg {
  color: #22c55e;
}

.stat-icon-wrapper.warning {
  background: rgba(245, 158, 11, 0.15);
}

.stat-icon-wrapper.warning .stat-svg {
  color: #f59e0b;
}

.stat-svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00d9ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Dashboard Content */
.dashboard-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Mobile Responsive */
@media (max-width: 900px) {
  .sidebar {
    display: none;
  }

  .main-content {
    margin-left: 0;
    padding: 80px 20px 30px;
  }

  .mobile-menu-btn {
    display: block;
  }

  .mobile-overlay {
    display: block;
  }

  .mobile-menu {
    display: flex;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 500px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: 1rem;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
}

/* ====== ADMIN SPECIFIC STYLES ====== */
.admin-dashboard {
  min-height: 100vh;
}

.admin-badge {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24) !important;
  color: white !important;
}

.admin-avatar {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24) !important;
  font-size: 1.2rem !important;
}

/* Header extras */
.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.realtime-viewers {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  padding: 0.5rem 1rem;
  border-radius: 20px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.viewer-count {
  color: #22c55e;
  font-weight: 600;
  font-size: 0.9rem;
}

.btn-refresh {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-refresh svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.7);
}

/* Stats customization */
.stat-icon-wrapper.money {
  background: rgba(34, 197, 94, 0.15);
}

.stat-icon-wrapper.money .stat-svg {
  color: #22c55e;
}

/* Metrics Row */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.5rem;
}

.metric-card h3 {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  margin: 0 0 1rem 0;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
}

.metric-value.realtime {
  color: #22c55e;
}

.metric-value.positive {
  color: #22c55e;
}

.metric-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.metric-fill {
  height: 100%;
  background: linear-gradient(90deg, #00d9ff, #0099cc);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.metric-desc {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  margin: 0;
}

/* Recent Section */
.recent-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.5rem;
}

.recent-section h3 {
  color: white;
  margin: 0 0 1.5rem 0;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  transition: all 0.3s;
}

.recent-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.recent-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: white;
}

.recent-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.recent-name {
  color: white;
  font-weight: 600;
}

.recent-email {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

.recent-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.recent-plan {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.recent-plan.free { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.recent-plan.basic { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.recent-plan.pro { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.recent-plan.elite { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

.recent-date {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.75rem;
}

/* Tab Header */
.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.tab-header h2 {
  color: white;
  margin: 0;
}

.search-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: white;
  font-size: 0.9rem;
  min-width: 300px;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

/* Table */
.table-container {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
}

.data-table tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.cell-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: white;
  font-size: 0.9rem;
}

.cell-info {
  display: flex;
  flex-direction: column;
}

.cell-name {
  color: white;
  font-weight: 500;
}

.cell-email {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
}

.plan-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.plan-badge.free { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.plan-badge.basic { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.plan-badge.pro { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.plan-badge.elite { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-badge.ativo, .status-badge.active { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
.status-badge.free { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.status-badge.cancelado, .status-badge.canceled { background: rgba(239, 68, 68, 0.2); color: #f87171; }

.date-cell {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.id-cell {
  font-family: monospace;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.table-footer {
  padding: 1rem;
  text-align: right;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
}

/* Analytics */
.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.analytics-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.5rem;
}

.analytics-card.full-width {
  grid-column: 1 / -1;
}

.analytics-card h3 {
  color: white;
  margin: 0 0 1.5rem 0;
  font-size: 1rem;
}

.plan-distribution {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.plan-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.plan-name {
  min-width: 60px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.plan-bar-container {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.plan-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.plan-bar.free { background: linear-gradient(90deg, #64748b, #475569); }
.plan-bar.paid { background: linear-gradient(90deg, #22c55e, #16a34a); }

.plan-count {
  min-width: 30px;
  text-align: right;
  color: white;
  font-weight: 600;
}

.revenue-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.revenue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.revenue-label {
  color: rgba(255, 255, 255, 0.6);
}

.revenue-value {
  color: #22c55e;
  font-weight: 700;
  font-size: 1.2rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1.5rem;
}

.summary-item {
  text-align: center;
}

.summary-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.25rem;
}

.summary-label {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

/* Mobile */
@media (max-width: 768px) {
  .header-right {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .realtime-viewers {
    order: 2;
  }

  .search-input {
    min-width: 100%;
  }

  .tab-header {
    flex-direction: column;
    align-items: stretch;
  }

  .metrics-row {
    grid-template-columns: 1fr;
  }

  .data-table {
    font-size: 0.8rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.75rem 0.5rem;
  }
}
</style>
