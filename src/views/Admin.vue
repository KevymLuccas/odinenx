<script setup>
import { ref, computed, onMounted } from 'vue'
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

// Filters
const userFilter = ref('')

// Edit modal
const showEditModal = ref(false)
const editingUser = ref(null)
const editForm = ref({
  full_name: '',
  plan: 'free'
})
const saving = ref(false)

onMounted(async () => {
  console.log('🔍 Admin.vue: Iniciando verificação...')
  
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) { 
    router.push('/login')
    return 
  }
  
  user.value = session.user

  const userIsAdmin = await isAdmin(session.user.id)
  
  if (!userIsAdmin) {
    router.push('/dashboard')
    return
  }
  
  await loadAdminData()
  loading.value = false
})

const loadAdminData = async () => {
  try {
    // Carregar usuários
    const { data: profilesData, error: profilesError } = await supabase
      .from('profiles')
      .select('*')
      .order('created_at', { ascending: false })
    
    if (!profilesError) {
      users.value = profilesData || []
    }

    // Carregar assinaturas
    const { data: subsData, error: subsError } = await supabase
      .from('subscriptions')
      .select('*')
      .order('created_at', { ascending: false })
    
    if (!subsError) {
      subscriptions.value = subsData || []
    }

  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  }
}

// Estatísticas calculadas (100% real do Supabase)
const stats = computed(() => {
  const total = users.value.length
  const pagos = subscriptions.value.filter(s => s.status === 'active').length
  const free = total - pagos
  // Receita real = R$ 0,00 até ter pagamentos via Stripe
  const receita = 0
  
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
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
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

// EDITAR USUÁRIO
const openEditModal = (userItem) => {
  editingUser.value = userItem
  editForm.value = {
    full_name: userItem.full_name || '',
    plan: getUserPlan(userItem).toLowerCase()
  }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingUser.value = null
}

const saveUserChanges = async () => {
  if (!editingUser.value) return
  saving.value = true

  try {
    // Atualizar nome no profiles
    const { error: profileError } = await supabase
      .from('profiles')
      .update({ full_name: editForm.value.full_name })
      .eq('id', editingUser.value.id)

    if (profileError) {
      alert('Erro ao salvar nome: ' + profileError.message)
      saving.value = false
      return
    }

    // Se mudou o plano, atualizar/criar assinatura
    const currentPlan = getUserPlan(editingUser.value).toLowerCase()
    if (editForm.value.plan !== currentPlan) {
      const existingSub = subscriptions.value.find(s => s.user_id === editingUser.value.id)
      
      if (editForm.value.plan === 'free') {
        // Remover assinatura se existir
        if (existingSub) {
          await supabase.from('subscriptions').delete().eq('id', existingSub.id)
        }
      } else {
        // Criar ou atualizar assinatura
        const subData = {
          user_id: editingUser.value.id,
          status: 'active',
          price_id: `price_${editForm.value.plan}`,
          current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
        }

        if (existingSub) {
          await supabase.from('subscriptions').update(subData).eq('id', existingSub.id)
        } else {
          await supabase.from('subscriptions').insert(subData)
        }
      }
    }

    await loadAdminData()
    closeEditModal()
    alert('Usuário atualizado com sucesso!')

  } catch (error) {
    alert('Erro: ' + error.message)
  }

  saving.value = false
}

// DELETAR USUÁRIO
const deleteUser = async (userItem) => {
  if (!confirm(`Tem certeza que deseja remover ${userItem.email}? Esta ação não pode ser desfeita.`)) {
    return
  }

  try {
    // Remover assinaturas
    await supabase.from('subscriptions').delete().eq('user_id', userItem.id)
    
    // Remover profile
    const { error } = await supabase.from('profiles').delete().eq('id', userItem.id)
    
    if (error) {
      alert('Erro ao remover: ' + error.message)
      return
    }

    await loadAdminData()
    alert('Usuário removido!')

  } catch (error) {
    alert('Erro: ' + error.message)
  }
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
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
        <router-link to="/"><img src="/logo.webp" alt="ODINENX" class="sidebar-logo" /></router-link>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-category">Administração</div>
        <a @click="activeTab = 'dashboard'" class="nav-item" :class="{ active: activeTab === 'dashboard' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          Dashboard
        </a>
        <a @click="activeTab = 'users'" class="nav-item" :class="{ active: activeTab === 'users' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          Usuários
        </a>
        <a @click="activeTab = 'subscriptions'" class="nav-item" :class="{ active: activeTab === 'subscriptions' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
          </svg>
          Assinaturas
        </a>
        <a @click="activeTab = 'analytics'" class="nav-item" :class="{ active: activeTab === 'analytics' }">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>
          </svg>
          Analytics
        </a>

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
          <svg class="admin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          ADMIN
        </div>
        <button @click="logout" class="logout-btn">
          <svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
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

    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>
    
    <nav class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-header"><img src="/logo.webp" alt="ODINENX" class="mobile-logo" /></div>
      <div class="mobile-nav">
        <button @click="activeTab = 'dashboard'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'dashboard' }">Dashboard</button>
        <button @click="activeTab = 'users'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'users' }">Usuários</button>
        <button @click="activeTab = 'subscriptions'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'subscriptions' }">Assinaturas</button>
        <button @click="activeTab = 'analytics'; mobileMenuOpen = false" class="mobile-nav-item" :class="{ active: activeTab === 'analytics' }">Analytics</button>
        <button @click="router.push('/dashboard'); mobileMenuOpen = false" class="mobile-nav-item">Voltar ao Sistema</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <header class="dashboard-header">
        <div class="header-left">
          <h1>
            <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Painel Administrativo
          </h1>
          <p>Gerenciamento do sistema ODINENX</p>
        </div>
        <div class="header-right">
          <button @click="refreshData" class="btn-refresh" :disabled="loading" title="Atualizar dados">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
          </button>
          <div class="user-info">
            <div class="user-avatar admin-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div class="user-details">
              <span class="user-name">Administrador</span>
              <span class="user-email">{{ user?.email }}</span>
            </div>
          </div>
        </div>
      </header>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>

      <div v-else class="dashboard-content">
        
        <!-- DASHBOARD TAB -->
        <div v-show="activeTab === 'dashboard'" class="admin-tab">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon-wrapper primary">
                <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
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
                  <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
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
                  <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
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
                  <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ formatCurrency(stats.revenue) }}</span>
                <span class="stat-label">Receita Mensal</span>
              </div>
            </div>
          </div>

          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-header">
                <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
                <span>Taxa de Conversão</span>
              </div>
              <div class="metric-value">{{ stats.conversionRate }}%</div>
              <div class="metric-bar"><div class="metric-fill" :style="{ width: stats.conversionRate + '%' }"></div></div>
              <p class="metric-desc">Free → Pago</p>
            </div>

            <div class="metric-card">
              <div class="metric-header">
                <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                </svg>
                <span>Usuários</span>
              </div>
              <div class="metric-value">{{ stats.totalUsers }}</div>
              <p class="metric-desc">Total cadastrados</p>
            </div>

            <div class="metric-card">
              <div class="metric-header">
                <svg class="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
                </svg>
                <span>Receita Anual</span>
              </div>
              <div class="metric-value positive">{{ formatCurrency(stats.revenue * 12) }}</div>
              <p class="metric-desc">Projeção anual</p>
            </div>
          </div>

          <div class="recent-section">
            <div class="section-header">
              <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              <h3>Últimos Usuários Cadastrados</h3>
            </div>
            <div class="recent-list">
              <div v-for="userItem in users.slice(0, 5)" :key="userItem.id" class="recent-item">
                <div class="recent-avatar">{{ (userItem.full_name || userItem.email || 'U')[0].toUpperCase() }}</div>
                <div class="recent-info">
                  <span class="recent-name">{{ userItem.full_name || 'Usuário' }}</span>
                  <span class="recent-email">{{ userItem.email }}</span>
                </div>
                <div class="recent-meta">
                  <span class="recent-plan" :class="getUserPlan(userItem).toLowerCase()">{{ getUserPlan(userItem) }}</span>
                  <span class="recent-date">{{ formatDate(userItem.created_at) }}</span>
                </div>
              </div>
              <div v-if="users.length === 0" class="empty-state"><p>Nenhum usuário cadastrado</p></div>
            </div>
          </div>
        </div>

        <!-- USERS TAB -->
        <div v-show="activeTab === 'users'" class="admin-tab">
          <div class="tab-header">
            <div class="tab-title">
              <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <h2>Gerenciamento de Usuários</h2>
            </div>
            <div class="tab-actions">
              <div class="search-wrapper">
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
                </svg>
                <input v-model="userFilter" type="text" placeholder="Buscar por email ou nome..." class="search-input">
              </div>
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
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="userItem in filteredUsers" :key="userItem.id">
                  <td>
                    <div class="user-cell">
                      <div class="cell-avatar">{{ (userItem.full_name || userItem.email || 'U')[0].toUpperCase() }}</div>
                      <div class="cell-info">
                        <span class="cell-name">{{ userItem.full_name || 'Usuário' }}</span>
                        <span class="cell-email">{{ userItem.email }}</span>
                      </div>
                    </div>
                  </td>
                  <td><span class="plan-badge" :class="getUserPlan(userItem).toLowerCase()">{{ getUserPlan(userItem) }}</span></td>
                  <td><span class="status-badge" :class="getUserStatus(userItem).toLowerCase()">{{ getUserStatus(userItem) }}</span></td>
                  <td class="date-cell">{{ formatDate(userItem.created_at) }}</td>
                  <td class="actions-cell">
                    <button @click="openEditModal(userItem)" class="btn-action edit" title="Editar">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </button>
                    <button @click="deleteUser(userItem)" class="btn-action delete" title="Remover">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="filteredUsers.length === 0" class="empty-state"><p>Nenhum usuário encontrado</p></div>
          </div>
          <div class="table-footer"><span>Total: {{ filteredUsers.length }} usuários</span></div>
        </div>

        <!-- SUBSCRIPTIONS TAB -->
        <div v-show="activeTab === 'subscriptions'" class="admin-tab">
          <div class="tab-header">
            <div class="tab-title">
              <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>
              </svg>
              <h2>Assinaturas</h2>
            </div>
          </div>

          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr><th>ID</th><th>Usuário</th><th>Status</th><th>Plano</th><th>Validade</th></tr>
              </thead>
              <tbody>
                <tr v-for="sub in subscriptions" :key="sub.id">
                  <td class="id-cell">{{ sub.id?.slice(0, 8) }}...</td>
                  <td>{{ sub.user_id?.slice(0, 8) }}...</td>
                  <td><span class="status-badge" :class="sub.status">{{ sub.status?.toUpperCase() }}</span></td>
                  <td>{{ sub.price_id?.includes('elite') ? 'Elite' : sub.price_id?.includes('pro') ? 'Pro' : 'Basic' }}</td>
                  <td class="date-cell">{{ sub.current_period_end ? formatDate(sub.current_period_end) : '-' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="subscriptions.length === 0" class="empty-state"><p>Nenhuma assinatura encontrada</p></div>
          </div>
          <div class="table-footer"><span>Total: {{ subscriptions.length }} assinaturas</span></div>
        </div>

        <!-- ANALYTICS TAB -->
        <div v-show="activeTab === 'analytics'" class="admin-tab">
          <div class="tab-header">
            <div class="tab-title">
              <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>
              </svg>
              <h2>Analytics</h2>
            </div>
          </div>

          <div class="analytics-grid">
            <div class="analytics-card">
              <h3>Distribuição de Planos</h3>
              <div class="plan-distribution">
                <div class="plan-row">
                  <span class="plan-name">Free</span>
                  <div class="plan-bar-container"><div class="plan-bar free" :style="{ width: (stats.totalUsers > 0 ? (stats.freeUsers / stats.totalUsers) * 100 : 0) + '%' }"></div></div>
                  <span class="plan-count">{{ stats.freeUsers }}</span>
                </div>
                <div class="plan-row">
                  <span class="plan-name">Pagos</span>
                  <div class="plan-bar-container"><div class="plan-bar paid" :style="{ width: (stats.totalUsers > 0 ? (stats.paidUsers / stats.totalUsers) * 100 : 0) + '%' }"></div></div>
                  <span class="plan-count">{{ stats.paidUsers }}</span>
                </div>
              </div>
            </div>

            <div class="analytics-card">
              <h3>Receita</h3>
              <div class="revenue-info">
                <div class="revenue-item"><span class="revenue-label">Mensal</span><span class="revenue-value">{{ formatCurrency(stats.revenue) }}</span></div>
                <div class="revenue-item"><span class="revenue-label">Anual</span><span class="revenue-value">{{ formatCurrency(stats.revenue * 12) }}</span></div>
              </div>
            </div>

            <div class="analytics-card full-width">
              <h3>Resumo</h3>
              <div class="summary-grid">
                <div class="summary-item"><span class="summary-value">{{ users.length }}</span><span class="summary-label">Usuários</span></div>
                <div class="summary-item"><span class="summary-value">{{ subscriptions.filter(s => s.status === 'active').length }}</span><span class="summary-label">Ativos</span></div>
                <div class="summary-item"><span class="summary-value">{{ stats.conversionRate }}%</span><span class="summary-label">Conversão</span></div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal">
        <div class="modal-header">
          <svg class="modal-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          <h3>Editar Usuário</h3>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Email</label>
            <input type="text" :value="editingUser?.email" disabled class="form-input disabled">
          </div>
          <div class="form-group">
            <label>Nome Completo</label>
            <input type="text" v-model="editForm.full_name" class="form-input" placeholder="Nome do usuário">
          </div>
          <div class="form-group">
            <label>Plano</label>
            <select v-model="editForm.plan" class="form-select">
              <option value="free">FREE</option>
              <option value="basic">BASIC</option>
              <option value="pro">PRO</option>
              <option value="elite">ELITE</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-cancel">Cancelar</button>
          <button @click="saveUserChanges" class="btn-save" :disabled="saving">{{ saving ? 'Salvando...' : 'Salvar' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* BASE */
.dashboard { display: flex; min-height: 100vh; background: #000; color: #fff; }

/* SIDEBAR */
.sidebar { width: 260px; background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; position: fixed; height: 100vh; left: 0; top: 0; }
.sidebar-header { padding: 25px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.sidebar-logo { height: 35px; }
.sidebar-nav { flex: 1; padding: 20px 15px; display: flex; flex-direction: column; gap: 5px; overflow-y: auto; }
.nav-category { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.35); padding: 15px 15px 8px; font-weight: 600; }
.nav-category:first-child { padding-top: 0; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 15px; color: rgba(255,255,255,0.6); border-radius: 10px; transition: all 0.3s; text-decoration: none; cursor: pointer; }
.nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
.nav-item.active { background: rgba(255,255,255,0.1); color: #fff; }
.nav-icon { width: 20px; height: 20px; flex-shrink: 0; }
.sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; gap: 15px; }
.plan-badge-sidebar { background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; text-align: center; display: flex; align-items: center; justify-content: center; gap: 8px; }
.admin-badge { background: linear-gradient(135deg, #ff6b6b, #ee5a24) !important; color: white !important; }
.admin-icon { width: 16px; height: 16px; }
.logout-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: transparent; border: 1px solid rgba(255,255,255,0.2); color: rgba(255,255,255,0.6); padding: 10px; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
.logout-btn:hover { border-color: #ff6b6b; color: #ff6b6b; }
.logout-icon { width: 18px; height: 18px; }

/* MAIN CONTENT */
.main-content { flex: 1; margin-left: 260px; padding: 30px; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; flex-wrap: wrap; gap: 1rem; }
.header-left h1 { font-size: 1.8rem; font-weight: 800; margin: 0 0 5px 0; display: flex; align-items: center; gap: 10px; }
.title-icon { width: 28px; height: 28px; color: #ff6b6b; }
.header-left p { color: rgba(255,255,255,0.5); margin: 0; }
.header-right { display: flex; align-items: center; gap: 1rem; }
.btn-refresh { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; cursor: pointer; transition: all 0.3s; }
.btn-refresh:hover { background: rgba(255,255,255,0.1); }
.btn-refresh svg { width: 20px; height: 20px; color: rgba(255,255,255,0.7); }
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { width: 45px; height: 45px; background: linear-gradient(135deg, #00d9ff, #0099cc); border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.admin-avatar { background: linear-gradient(135deg, #ff6b6b, #ee5a24) !important; }
.admin-avatar svg { width: 22px; height: 22px; color: white; }
.user-details { display: flex; flex-direction: column; }
.user-name { color: #fff; font-weight: 600; }
.user-email { color: rgba(255,255,255,0.5); font-size: 0.85rem; }

/* MOBILE */
.mobile-menu-btn { display: none; position: fixed; top: 20px; left: 20px; z-index: 1001; background: rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 10px; cursor: pointer; }
.mobile-menu-btn svg { width: 24px; height: 24px; color: #fff; }
.mobile-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 999; }
.mobile-menu { display: none; position: fixed; top: 0; left: -280px; width: 280px; height: 100vh; background: #0a0a0a; z-index: 1000; flex-direction: column; transition: left 0.3s ease; }
.mobile-menu.open { left: 0; }
.mobile-menu-header { padding: 25px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.mobile-logo { height: 30px; }
.mobile-nav { flex: 1; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
.mobile-nav-item { background: transparent; border: none; color: rgba(255,255,255,0.7); padding: 15px 20px; text-align: left; border-radius: 10px; cursor: pointer; transition: all 0.3s; font-size: 1rem; }
.mobile-nav-item:hover, .mobile-nav-item.active { background: rgba(255,255,255,0.1); color: #fff; }
.mobile-logout { background: transparent; border: 1px solid rgba(255,107,107,0.5); color: #ff6b6b; padding: 15px; margin: 20px; border-radius: 10px; cursor: pointer; }

/* STATS */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.stat-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1.5rem; display: flex; align-items: center; gap: 1rem; transition: all 0.3s; }
.stat-card:hover { border-color: rgba(255,255,255,0.15); transform: translateY(-2px); }
.stat-icon-wrapper { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-icon-wrapper.primary { background: rgba(0,217,255,0.15); }
.stat-icon-wrapper.primary .stat-svg { color: #00d9ff; }
.stat-icon-wrapper.success { background: rgba(34,197,94,0.15); }
.stat-icon-wrapper.success .stat-svg { color: #22c55e; }
.stat-icon-wrapper.warning { background: rgba(245,158,11,0.15); }
.stat-icon-wrapper.warning .stat-svg { color: #f59e0b; }
.stat-icon-wrapper.money { background: rgba(34,197,94,0.15); }
.stat-icon-wrapper.money .stat-svg { color: #22c55e; }
.stat-svg { width: 24px; height: 24px; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: #fff; }
.stat-label { color: rgba(255,255,255,0.5); font-size: 0.85rem; }

/* METRICS */
.metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.metric-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.5rem; }
.metric-header { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 1rem; }
.metric-icon { width: 18px; height: 18px; }
.metric-value { font-size: 2.5rem; font-weight: 700; color: white; margin-bottom: 0.5rem; }
.metric-value.positive { color: #22c55e; }
.metric-bar { height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; margin-bottom: 0.5rem; }
.metric-fill { height: 100%; background: linear-gradient(90deg, #00d9ff, #0099cc); border-radius: 3px; transition: width 0.5s ease; }
.metric-desc { color: rgba(255,255,255,0.5); font-size: 0.85rem; margin: 0; }

/* RECENT */
.recent-section { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.5rem; }
.section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1.5rem; }
.section-icon { width: 20px; height: 20px; color: #00d9ff; }
.section-header h3 { color: white; margin: 0; font-size: 1rem; }
.recent-list { display: flex; flex-direction: column; gap: 1rem; }
.recent-item { display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(255,255,255,0.02); border-radius: 8px; transition: all 0.3s; }
.recent-item:hover { background: rgba(255,255,255,0.05); }
.recent-avatar { width: 40px; height: 40px; background: linear-gradient(135deg, #00d9ff, #0099cc); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; }
.recent-info { flex: 1; display: flex; flex-direction: column; }
.recent-name { color: white; font-weight: 600; }
.recent-email { color: rgba(255,255,255,0.5); font-size: 0.85rem; }
.recent-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 0.25rem; }
.recent-plan { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.recent-plan.free { background: rgba(100,116,139,0.2); color: #94a3b8; }
.recent-plan.basic { background: rgba(59,130,246,0.2); color: #60a5fa; }
.recent-plan.pro { background: rgba(16,185,129,0.2); color: #34d399; }
.recent-plan.elite { background: rgba(245,158,11,0.2); color: #fbbf24; }
.recent-date { color: rgba(255,255,255,0.4); font-size: 0.75rem; }

/* TAB HEADER */
.tab-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
.tab-title { display: flex; align-items: center; gap: 10px; }
.tab-icon { width: 24px; height: 24px; color: #00d9ff; }
.tab-title h2 { color: white; margin: 0; font-size: 1.3rem; }
.search-wrapper { position: relative; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); width: 18px; height: 18px; color: rgba(255,255,255,0.4); }
.search-input { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 0.75rem 1rem 0.75rem 40px; color: white; font-size: 0.9rem; min-width: 280px; }
.search-input::placeholder { color: rgba(255,255,255,0.4); }

/* TABLE */
.table-container { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: rgba(255,255,255,0.05); padding: 1rem; text-align: left; font-weight: 600; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.1); }
.data-table td { padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.8); }
.data-table tr:hover { background: rgba(255,255,255,0.02); }
.user-cell { display: flex; align-items: center; gap: 0.75rem; }
.cell-avatar { width: 36px; height: 36px; background: linear-gradient(135deg, #00d9ff, #0099cc); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; font-size: 0.9rem; }
.cell-info { display: flex; flex-direction: column; }
.cell-name { color: white; font-weight: 500; }
.cell-email { color: rgba(255,255,255,0.5); font-size: 0.8rem; }
.plan-badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.plan-badge.free { background: rgba(100,116,139,0.2); color: #94a3b8; }
.plan-badge.basic { background: rgba(59,130,246,0.2); color: #60a5fa; }
.plan-badge.pro { background: rgba(16,185,129,0.2); color: #34d399; }
.plan-badge.elite { background: rgba(245,158,11,0.2); color: #fbbf24; }
.status-badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.status-badge.ativo, .status-badge.active { background: rgba(34,197,94,0.2); color: #4ade80; }
.status-badge.free { background: rgba(100,116,139,0.2); color: #94a3b8; }
.status-badge.cancelado, .status-badge.canceled { background: rgba(239,68,68,0.2); color: #f87171; }
.date-cell { font-size: 0.85rem; color: rgba(255,255,255,0.5); }
.id-cell { font-family: monospace; font-size: 0.8rem; color: rgba(255,255,255,0.5); }
.actions-cell { display: flex; gap: 0.5rem; }
.btn-action { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 8px; cursor: pointer; transition: all 0.3s; }
.btn-action svg { width: 16px; height: 16px; color: rgba(255,255,255,0.6); }
.btn-action.edit:hover { background: rgba(59,130,246,0.2); border-color: #3b82f6; }
.btn-action.edit:hover svg { color: #60a5fa; }
.btn-action.delete:hover { background: rgba(239,68,68,0.2); border-color: #ef4444; }
.btn-action.delete:hover svg { color: #f87171; }
.table-footer { padding: 1rem; text-align: right; color: rgba(255,255,255,0.5); font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.05); }
.empty-state { padding: 3rem; text-align: center; color: rgba(255,255,255,0.4); }

/* ANALYTICS */
.analytics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
.analytics-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.5rem; }
.analytics-card.full-width { grid-column: 1 / -1; }
.analytics-card h3 { color: white; margin: 0 0 1.5rem 0; font-size: 1rem; }
.plan-distribution { display: flex; flex-direction: column; gap: 1rem; }
.plan-row { display: flex; align-items: center; gap: 1rem; }
.plan-name { min-width: 60px; color: rgba(255,255,255,0.7); font-size: 0.9rem; }
.plan-bar-container { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.plan-bar { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.plan-bar.free { background: linear-gradient(90deg, #64748b, #475569); }
.plan-bar.paid { background: linear-gradient(90deg, #22c55e, #16a34a); }
.plan-count { min-width: 30px; text-align: right; color: white; font-weight: 600; }
.revenue-info { display: flex; flex-direction: column; gap: 1rem; }
.revenue-item { display: flex; justify-content: space-between; align-items: center; }
.revenue-label { color: rgba(255,255,255,0.6); }
.revenue-value { color: #22c55e; font-weight: 700; font-size: 1.2rem; }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1.5rem; }
.summary-item { text-align: center; }
.summary-value { display: block; font-size: 2rem; font-weight: 700; color: white; margin-bottom: 0.25rem; }
.summary-label { color: rgba(255,255,255,0.5); font-size: 0.85rem; }

/* MODAL */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #111; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 0; width: 90%; max-width: 450px; }
.modal-header { display: flex; align-items: center; gap: 12px; padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-icon { width: 24px; height: 24px; color: #00d9ff; }
.modal-header h3 { margin: 0; color: white; }
.modal-body { padding: 1.5rem; }
.form-group { margin-bottom: 1.25rem; }
.form-group label { display: block; color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 0.5rem; }
.form-input, .form-select { width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 0.75rem 1rem; color: white; font-size: 0.95rem; }
.form-input.disabled { opacity: 0.5; cursor: not-allowed; }
.form-select { cursor: pointer; }
.form-select option { background: #111; color: white; }
.modal-footer { display: flex; justify-content: flex-end; gap: 1rem; padding: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); }
.btn-cancel { background: transparent; border: 1px solid rgba(255,255,255,0.2); color: rgba(255,255,255,0.7); padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
.btn-cancel:hover { border-color: rgba(255,255,255,0.4); color: white; }
.btn-save { background: linear-gradient(135deg, #00d9ff, #0099cc); border: none; color: white; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; transition: all 0.3s; font-weight: 600; }
.btn-save:hover { transform: translateY(-2px); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* LOADING */
.loading-container { display: flex; justify-content: center; align-items: center; min-height: 300px; }
.spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #00d9ff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.dashboard-content { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* MOBILE */
@media (max-width: 900px) {
  .sidebar { display: none; }
  .main-content { margin-left: 0; padding: 80px 20px 30px; }
  .mobile-menu-btn { display: block; }
  .mobile-overlay { display: block; }
  .mobile-menu { display: flex; }
  .dashboard-header { flex-direction: column; align-items: flex-start; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .search-input { min-width: 100%; }
}
@media (max-width: 500px) {
  .stats-grid { grid-template-columns: 1fr; }
  .metrics-row { grid-template-columns: 1fr; }
}
</style>
