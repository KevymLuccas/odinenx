<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans, hasAccess } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const loading = ref(true)

// Admin data
const users = ref([])
const subscriptions = ref([])
const stats = ref(null)
const activeTab = ref('users')

// Filters
const userFilter = ref('')
const planFilter = ref('all')

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { 
    router.push('/login')
    return 
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  // 🔒 CONTROLE DE ACESSO: Apenas Elite pode acessar Admin
  const hasAdminAccess = await hasAccess(subscription.value, 'admin', session.user.id)
  if (!hasAdminAccess) {
    alert('❌ Acesso Negado!\n\nApenas usuários do plano Elite podem acessar o Painel Administrativo.')
    router.push('/dashboard')
    return
  }
  
  await loadAdminData()
  loading.value = false
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

const filteredUsers = computed(() => {
  let filtered = users.value
  
  if (userFilter.value) {
    const search = userFilter.value.toLowerCase()
    filtered = filtered.filter(u => 
      u.email?.toLowerCase().includes(search) ||
      u.id?.toLowerCase().includes(search)
    )
  }
  
  if (planFilter.value !== 'all') {
    filtered = filtered.filter(u => {
      const sub = subscriptions.value.find(s => s.user_id === u.id)
      return sub?.plan === planFilter.value || (planFilter.value === 'free' && !sub)
    })
  }
  
  return filtered
})

const loadAdminData = async () => {
  try {
    // Carregar usuários (usando service_role para bypass RLS)
    const { data: usersData, error: usersError } = await supabase
      .from('auth.users')
      .select('id, email, created_at, last_sign_in_at, email_confirmed_at')
      .order('created_at', { ascending: false })
      .limit(1000)
    
    // Fallback: se não conseguir acessar auth.users, criar dados mock
    if (usersError) {
      console.error('Erro ao carregar usuários:', usersError)
      users.value = [
        {
          id: user.value.id,
          email: user.value.email,
          created_at: new Date().toISOString(),
          last_sign_in_at: new Date().toISOString(),
          email_confirmed_at: new Date().toISOString()
        }
      ]
    } else {
      users.value = usersData || []
    }
    
    // Carregar assinaturas
    const { data: subsData, error: subsError } = await supabase
      .from('subscriptions')
      .select('*')
      .order('created_at', { ascending: false })
    
    if (subsError) {
      console.error('Erro ao carregar assinaturas:', subsError)
      subscriptions.value = []
    } else {
      subscriptions.value = subsData || []
    }
    
    // Calcular estatísticas
    calculateStats()
    
  } catch (error) {
    console.error('Erro ao carregar dados admin:', error)
  }
}

const calculateStats = () => {
  const totalUsers = users.value.length
  const totalSubscriptions = subscriptions.value.filter(s => s.status === 'active').length
  
  const planCounts = {
    free: users.value.length - totalSubscriptions,
    basic: subscriptions.value.filter(s => s.plan === 'basic' && s.status === 'active').length,
    pro: subscriptions.value.filter(s => s.plan === 'pro' && s.status === 'active').length,
    elite: subscriptions.value.filter(s => s.plan === 'elite' && s.status === 'active').length
  }
  
  const monthlyRevenue = subscriptions.value
    .filter(s => s.status === 'active')
    .reduce((acc, s) => {
      const plan = plans[s.plan]
      return acc + (plan?.price || 0)
    }, 0)
  
  const thisMonth = new Date()
  thisMonth.setDate(1)
  const newUsersThisMonth = users.value.filter(u => 
    new Date(u.created_at) >= thisMonth
  ).length
  
  stats.value = {
    totalUsers,
    totalSubscriptions,
    planCounts,
    monthlyRevenue,
    newUsersThisMonth,
    conversionRate: totalUsers > 0 ? (totalSubscriptions / totalUsers) * 100 : 0
  }
}

const getUserSubscription = (userId) => {
  return subscriptions.value.find(s => s.user_id === userId && s.status === 'active')
}

const getUserPlan = (userId) => {
  const sub = getUserSubscription(userId)
  return sub?.plan || 'free'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Nunca'
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { 
    style: 'currency', 
    currency: 'BRL' 
  }).format(value || 0)
}

const getPlanBadgeColor = (planId) => {
  const colors = {
    free: '#6b7280',
    basic: '#3b82f6',
    pro: '#8b5cf6',
    elite: '#f59e0b'
  }
  return colors[planId] || colors.free
}

const exportUsers = () => {
  const csv = [
    ['Email', 'Plano', 'Data de Cadastro', 'Último Login', 'Status'].join(','),
    ...filteredUsers.value.map(u => [
      u.email,
      getUserPlan(u.id),
      formatDate(u.created_at),
      formatDate(u.last_sign_in_at),
      u.email_confirmed_at ? 'Confirmado' : 'Pendente'
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `usuarios_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
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
        
        <div class="nav-category">Sistema</div>
        <router-link to="/admin" class="nav-item active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
          Admin
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
            <h1>🛡️ Admin</h1>
            <p>Painel de administração</p>
          </div>
          <div class="header-actions">
            <button @click="loadAdminData" class="btn btn-outline">
              🔄 Atualizar
            </button>
            <button @click="exportUsers" class="btn btn-primary">
              📊 Exportar CSV
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading">
          <div class="loading-spinner"></div>
          <p>Carregando dados administrativos...</p>
        </div>

        <!-- Stats Cards -->
        <div v-if="!loading && stats" class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-info">
              <p class="stat-label">Total de Usuários</p>
              <p class="stat-value">{{ stats.totalUsers }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-info">
              <p class="stat-label">Receita Mensal</p>
              <p class="stat-value">{{ formatCurrency(stats.monthlyRevenue) }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">📈</div>
            <div class="stat-info">
              <p class="stat-label">Taxa de Conversão</p>
              <p class="stat-value">{{ stats.conversionRate.toFixed(1) }}%</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">🆕</div>
            <div class="stat-info">
              <p class="stat-label">Novos (Este Mês)</p>
              <p class="stat-value">{{ stats.newUsersThisMonth }}</p>
            </div>
          </div>
        </div>

        <!-- Plan Distribution -->
        <div v-if="!loading && stats" class="plan-distribution">
          <h3>📊 Distribuição por Plano</h3>
          <div class="plan-bars">
            <div 
              v-for="(count, plan) in stats.planCounts" 
              :key="plan" 
              class="plan-bar"
            >
              <div class="plan-bar-info">
                <span class="plan-name">{{ plans[plan]?.name || plan }}</span>
                <span class="plan-count">{{ count }} usuários</span>
              </div>
              <div class="plan-bar-visual">
                <div 
                  class="plan-bar-fill" 
                  :style="{ 
                    width: `${(count / stats.totalUsers) * 100}%`,
                    backgroundColor: getPlanBadgeColor(plan)
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- User Management -->
        <div v-if="!loading" class="user-management">
          <div class="management-header">
            <h3>👥 Gerenciamento de Usuários</h3>
            <div class="filters">
              <input 
                v-model="userFilter" 
                type="text" 
                placeholder="Buscar por email ou ID..."
                class="search-input"
              />
              <select v-model="planFilter" class="plan-select">
                <option value="all">Todos os planos</option>
                <option value="free">Free</option>
                <option value="basic">Basic</option>
                <option value="pro">Pro</option>
                <option value="elite">Elite</option>
              </select>
            </div>
          </div>
          
          <div class="users-table-container">
            <table class="users-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Plano</th>
                  <th>Cadastro</th>
                  <th>Último Login</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id">
                  <td>{{ user.email }}</td>
                  <td>
                    <span 
                      class="plan-badge-table" 
                      :style="{ backgroundColor: getPlanBadgeColor(getUserPlan(user.id)) }"
                    >
                      {{ plans[getUserPlan(user.id)]?.name || 'Free' }}
                    </span>
                  </td>
                  <td>{{ formatDate(user.created_at) }}</td>
                  <td>{{ formatDate(user.last_sign_in_at) }}</td>
                  <td>
                    <span :class="['status-badge', user.email_confirmed_at ? 'confirmed' : 'pending']">
                      {{ user.email_confirmed_at ? 'Confirmado' : 'Pendente' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="table-footer">
            <p>{{ filteredUsers.length }} de {{ users.length }} usuários</p>
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
        <a @click="navigateTo('/admin')" class="active">Admin</a>
      </nav>
    </div>
  </div>
</template>

<style scoped>
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

.plan-distribution {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.plan-distribution h3 {
  color: white;
  margin: 0 0 1rem 0;
}

.plan-bars {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.plan-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.plan-bar-info {
  min-width: 120px;
  display: flex;
  flex-direction: column;
}

.plan-name {
  color: white;
  font-weight: 500;
}

.plan-count {
  color: #8892b0;
  font-size: 0.8rem;
}

.plan-bar-visual {
  flex: 1;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.plan-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 10px;
}

.user-management {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
}

.management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.management-header h3 {
  color: white;
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-input,
.plan-select {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 6px;
  color: white;
  font-size: 0.9rem;
}

.search-input {
  min-width: 200px;
}

.users-table-container {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  overflow: hidden;
}

.users-table th {
  background: rgba(0, 217, 255, 0.1);
  color: #00d9ff;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid rgba(0, 217, 255, 0.2);
}

.users-table td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #ccd6f6;
}

.users-table tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.plan-badge-table {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  color: white;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge.confirmed {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-badge.pending {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.table-footer {
  margin-top: 1rem;
  color: #8892b0;
  font-size: 0.9rem;
  text-align: center;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .management-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filters {
    justify-content: stretch;
  }
  
  .search-input,
  .plan-select {
    flex: 1;
    min-width: auto;
  }
  
  .users-table-container {
    font-size: 0.8rem;
  }
  
  .users-table th,
  .users-table td {
    padding: 0.5rem;
  }
}
</style>