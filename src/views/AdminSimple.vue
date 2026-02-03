<template>
  <div class="admin-container">
    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Não autorizado -->
    <div v-else-if="!isAdminUser" class="unauthorized">
      <h1>🚫 Acesso Negado</h1>
      <p>Você não tem permissão para acessar esta página.</p>
      <button @click="$router.push('/')" class="btn-back">Voltar ao Dashboard</button>
    </div>

    <!-- Painel Admin -->
    <div v-else>
      <!-- Header -->
      <div class="admin-header">
        <div class="header-content">
          <div class="header-left">
            <h1>🔧 Painel Administrativo</h1>
            <p>Controle total do sistema ODINENX</p>
          </div>
          <div class="header-right">
            <div class="admin-info">
              <span class="admin-badge">ADMINISTRADOR</span>
              <span class="admin-email">{{ user?.email }}</span>
            </div>
            <button @click="logout" class="btn-logout">
              Sair
            </button>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="admin-content">
        <!-- Tabs -->
        <div class="admin-tabs">
          <button 
            :class="['tab-button', { active: activeTab === 'dashboard' }]"
            @click="activeTab = 'dashboard'"
          >
            📊 Dashboard
          </button>
          <button 
            :class="['tab-button', { active: activeTab === 'users' }]"
            @click="activeTab = 'users'"
          >
            👥 Usuários
          </button>
          <button 
            :class="['tab-button', { active: activeTab === 'subscriptions' }]"
            @click="activeTab = 'subscriptions'"
          >
            💳 Assinaturas
          </button>
        </div>

        <!-- Dashboard -->
        <div v-show="activeTab === 'dashboard'" class="tab-content">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon blue">
                👥
              </div>
              <div class="stat-details">
                <span class="stat-value">{{ stats.totalUsers }}</span>
                <span class="stat-label">Total de Usuários</span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon green">
                💰
              </div>
              <div class="stat-details">
                <span class="stat-value">R$ {{ (stats.totalRevenue || 0).toLocaleString() }}</span>
                <span class="stat-label">Receita Total</span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon yellow">
                💳
              </div>
              <div class="stat-details">
                <span class="stat-value">{{ stats.activeSubscriptions }}</span>
                <span class="stat-label">Assinaturas Ativas</span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon purple">
                ⚡
              </div>
              <div class="stat-details">
                <span class="stat-value">{{ stats.trialUsers }}</span>
                <span class="stat-label">Usuários Trial</span>
              </div>
            </div>
          </div>

          <!-- Distribuição de Planos -->
          <div class="plans-distribution">
            <h3>📊 Distribuição de Planos</h3>
            <div class="plan-bars">
              <div v-for="plan in planDistribution" :key="plan.name" class="plan-bar">
                <div class="plan-info">
                  <div class="plan-name">{{ plan.name }}</div>
                  <div class="plan-count">{{ plan.count }} usuários</div>
                </div>
                <div class="bar-container">
                  <div 
                    :class="['bar', plan.id]" 
                    :style="{ width: plan.percentage + '%' }"
                  ></div>
                </div>
                <div class="plan-percentage">{{ plan.percentage.toFixed(1) }}%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Gerenciamento de Usuários -->
        <div v-show="activeTab === 'users'" class="tab-content">
          <!-- Filtros -->
          <div class="filters-section">
            <div class="filter-group">
              <input 
                v-model="userFilters.search" 
                placeholder="Buscar por email..."
                class="filter-input"
                @input="filterUsers"
              >
            </div>
            <div class="filter-group">
              <select v-model="userFilters.status" @change="filterUsers" class="filter-select">
                <option value="">Todos os status</option>
                <option value="active">Ativos</option>
                <option value="inactive">Inativos</option>
              </select>
            </div>
          </div>

          <!-- Tabela de Usuários -->
          <div class="table-container">
            <table class="users-table">
              <thead>
                <tr>
                  <th>Usuário</th>
                  <th>Status</th>
                  <th>Data de Cadastro</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id">
                  <td>
                    <div class="user-info">
                      <div class="user-avatar">
                        {{ (user.email?.charAt(0) || '?').toUpperCase() }}
                      </div>
                      <div class="user-details">
                        <div class="user-name">{{ user.email }}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span :class="['status-badge', user.status || 'inactive']">
                      {{ user.status === 'ACTIVE' ? 'Ativo' : 'Inativo' }}
                    </span>
                  </td>
                  <td>
                    <div class="date-info">
                      {{ formatDate(user.created_at) }}
                    </div>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        @click="viewUserDetails(user)"
                        class="btn-action view"
                      >
                        Ver Detalhes
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="filteredUsers.length === 0" class="no-users">
              <p>{{ allUsers.length === 0 ? 'Carregando usuários...' : 'Nenhum usuário encontrado com os filtros aplicados.' }}</p>
            </div>
          </div>
        </div>

        <!-- Assinaturas -->
        <div v-show="activeTab === 'subscriptions'" class="tab-content">
          <div class="table-container">
            <table class="users-table">
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Plano</th>
                  <th>Status</th>
                  <th>Valor</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sub in subscriptions" :key="sub.id">
                  <td>
                    <div class="user-info">
                      <div class="user-avatar">
                        {{ (sub.user_email?.charAt(0) || '?').toUpperCase() }}
                      </div>
                      <div class="user-details">
                        <div class="user-name">{{ sub.user_email || sub.customer_email }}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span :class="['plan-badge', getPlanFromPriceId(sub.price_id)]">
                      {{ getPlanDisplayName(getPlanFromPriceId(sub.price_id)) }}
                    </span>
                  </td>
                  <td>
                    <span :class="['status-badge', sub.status?.toLowerCase()]">
                      {{ sub.status }}
                    </span>
                  </td>
                  <td>
                    R$ {{ getPlanPrice(sub.price_id)?.toLocaleString() || '0' }}
                  </td>
                  <td>
                    {{ formatDate(sub.created_at) }}
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="subscriptions.length === 0" class="no-users">
              <p>Nenhuma assinatura encontrada.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { supabase } from '../lib/supabase'

export default {
  name: 'AdminPanel',
  data() {
    return {
      loading: true,
      isAdminUser: false,
      user: null,
      activeTab: 'dashboard',
      
      // Stats
      stats: {
        totalUsers: 0,
        totalRevenue: 0,
        activeSubscriptions: 0,
        trialUsers: 0
      },
      
      // Users
      allUsers: [],
      filteredUsers: [],
      userFilters: {
        search: '',
        status: ''
      },
      
      // Subscriptions
      subscriptions: [],
      
      // Plan distribution
      planDistribution: []
    }
  },
  
  async mounted() {
    await this.checkAdminAccess()
    if (this.isAdminUser) {
      await this.loadDashboardData()
    }
  },
  
  methods: {
    async checkAdminAccess() {
      try {
        const { data: { user } } = await supabase.auth.getUser()
        
        if (!user) {
          this.$router.push('/login')
          return
        }
        
        this.user = user
        
        // Lista de emails de administradores
        const adminEmails = [
          'administrador@fantomstore.com.br',
          'admin@fantomstore.com.br',
          'odinenx@fantomstore.com.br'
        ]
        
        this.isAdminUser = adminEmails.includes(user.email?.toLowerCase())
        
      } catch (error) {
        console.error('Erro ao verificar acesso admin:', error)
      } finally {
        this.loading = false
      }
    },
    
    async loadDashboardData() {
      try {
        await Promise.all([
          this.loadStats(),
          this.loadUsers(),
          this.loadSubscriptions()
        ])
        this.calculatePlanDistribution()
      } catch (error) {
        console.error('Erro ao carregar dados do dashboard:', error)
      }
    },
    
    async loadStats() {
      try {
        // Total de usuários
        const { count: usersCount } = await supabase
          .from('profiles')
          .select('*', { count: 'exact', head: true })
        
        this.stats.totalUsers = usersCount || 0
        
        // Assinaturas ativas
        const { data: activeSubscriptions } = await supabase
          .from('subscriptions')
          .select('price_id')
          .eq('status', 'active')
        
        this.stats.activeSubscriptions = activeSubscriptions?.length || 0
        
        // Calcular receita total
        let totalRevenue = 0
        if (activeSubscriptions) {
          activeSubscriptions.forEach(sub => {
            totalRevenue += this.getPlanPrice(sub.price_id) || 0
          })
        }
        this.stats.totalRevenue = totalRevenue
        
        // Usuários em trial
        const { count: trialCount } = await supabase
          .from('trial_users')
          .select('*', { count: 'exact', head: true })
          .gte('trial_ends_at', new Date().toISOString())
        
        this.stats.trialUsers = trialCount || 0
        
      } catch (error) {
        console.error('Erro ao carregar estatísticas:', error)
      }
    },
    
    async loadUsers() {
      try {
        const { data: users } = await supabase
          .from('profiles')
          .select('*')
          .order('created_at', { ascending: false })
        
        this.allUsers = users || []
        this.filterUsers()
      } catch (error) {
        console.error('Erro ao carregar usuários:', error)
        this.allUsers = []
      }
    },
    
    async loadSubscriptions() {
      try {
        const { data: subs } = await supabase
          .from('subscriptions')
          .select(`
            *,
            profiles(email)
          `)
          .order('created_at', { ascending: false })
        
        this.subscriptions = (subs || []).map(sub => ({
          ...sub,
          user_email: sub.profiles?.email || sub.customer_email
        }))
      } catch (error) {
        console.error('Erro ao carregar assinaturas:', error)
        this.subscriptions = []
      }
    },
    
    calculatePlanDistribution() {
      const plans = {
        free: { name: 'Free', count: 0, id: 'free' },
        basic: { name: 'Basic', count: 0, id: 'basic' },
        pro: { name: 'Pro', count: 0, id: 'pro' },
        elite: { name: 'Elite', count: 0, id: 'elite' }
      }
      
      // Contar usuários free
      plans.free.count = Math.max(0, this.stats.totalUsers - this.stats.activeSubscriptions)
      
      // Contar por assinaturas ativas
      this.subscriptions.forEach(sub => {
        if (sub.status === 'active') {
          const planType = this.getPlanFromPriceId(sub.price_id)
          if (plans[planType]) {
            plans[planType].count++
          }
        }
      })
      
      const total = this.stats.totalUsers || 1
      this.planDistribution = Object.values(plans).map(plan => ({
        ...plan,
        percentage: (plan.count / total) * 100
      }))
    },
    
    filterUsers() {
      let filtered = [...this.allUsers]
      
      if (this.userFilters.search) {
        const search = this.userFilters.search.toLowerCase()
        filtered = filtered.filter(user => 
          user.email?.toLowerCase().includes(search)
        )
      }
      
      // Adicionar status baseado na presença de dados
      filtered = filtered.map(user => ({
        ...user,
        status: user.email ? 'ACTIVE' : 'INACTIVE'
      }))
      
      if (this.userFilters.status) {
        filtered = filtered.filter(user => {
          if (this.userFilters.status === 'active') {
            return user.status === 'ACTIVE'
          } else if (this.userFilters.status === 'inactive') {
            return user.status === 'INACTIVE'
          }
          return true
        })
      }
      
      this.filteredUsers = filtered
    },
    
    getPlanFromPriceId(priceId) {
      const planMap = {
        'price_1SvMedD3mufAbT6c994DmZYw': 'basic',
        'price_1SMuL9D3mufAbT6cTJzOykjV': 'basic',    // R$ 79
        'price_1SMuOzD3mufAbT6cOKHNZPsT': 'pro',      // R$ 199  
        'price_1SMuPwD3mufAbT6c5v8vxzLj': 'elite'     // R$ 399
      }
      return planMap[priceId] || 'free'
    },
    
    getPlanPrice(priceId) {
      const priceMap = {
        'price_1SvMedD3mufAbT6c994DmZYw': 79,
        'price_1SMuL9D3mufAbT6cTJzOykjV': 79,
        'price_1SMuOzD3mufAbT6cOKHNZPsT': 199,
        'price_1SMuPwD3mufAbT6c5v8vxzLj': 399
      }
      return priceMap[priceId] || 0
    },
    
    getPlanDisplayName(planId) {
      const names = {
        free: 'Free',
        basic: 'Basic',
        pro: 'Pro',
        elite: 'Elite'
      }
      return names[planId] || planId
    },
    
    viewUserDetails(user) {
      alert(`Detalhes do usuário:\nEmail: ${user.email}\nID: ${user.id}\nCriado: ${this.formatDate(user.created_at)}`)
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleDateString('pt-BR')
    },
    
    async logout() {
      try {
        await supabase.auth.signOut()
        this.$router.push('/login')
      } catch (error) {
        console.error('Erro ao fazer logout:', error)
      }
    }
  }
}
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  min-height: 100dvh;
  min-height: -webkit-fill-available;
  background: linear-gradient(135deg, #0a0a0a, #1a1a1a, #2d2d2d);
  color: white;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
}

.loading-container {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  min-height: 100vh;
  min-height: 100dvh;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #00d9ff;
  -webkit-animation: spin 0.8s linear infinite;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { -webkit-transform: rotate(360deg); transform: rotate(360deg); }
}

.unauthorized {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  text-align: center;
  padding: 2rem;
}

.unauthorized h1 {
  color: #ff6b6b;
  margin-bottom: 1rem;
}

.btn-back {
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 2rem;
  -webkit-tap-highlight-color: transparent;
}

.admin-header {
  background: rgba(255, 255, 255, 0.05);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2rem;
  padding-top: calc(2rem + env(safe-area-inset-top));
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-pack: justify;
  -webkit-justify-content: space-between;
  justify-content: space-between;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
}

.header-left h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 700;
}

.header-left p {
  margin: 0;
  color: rgba(255, 255, 255, 0.7);
}

.header-right {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  gap: 2rem;
}

.admin-info {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  -webkit-box-align: end;
  -webkit-align-items: flex-end;
  align-items: flex-end;
  gap: 0.5rem;
}

.admin-badge {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.admin-email {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  -webkit-tap-highlight-color: transparent;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.15);
  -webkit-transform: translateY(-2px);
  transform: translateY(-2px);
}

.admin-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  padding-bottom: calc(2rem + env(safe-area-inset-bottom));
}

.admin-tabs {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.tab-button {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  border-bottom: 2px solid transparent;
  font-size: 1rem;
  font-weight: 600;
}

.tab-button:hover {
  color: rgba(255, 255, 255, 0.8);
}

.tab-button.active {
  color: #00d9ff;
  border-bottom-color: #00d9ff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.stat-icon {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.stat-icon.blue { background: rgba(0, 217, 255, 0.15); }
.stat-icon.green { background: rgba(34, 197, 94, 0.15); }
.stat-icon.yellow { background: rgba(245, 158, 11, 0.15); }
.stat-icon.purple { background: rgba(168, 85, 247, 0.15); }

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  display: block;
}

.stat-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.plans-distribution {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 3rem;
}

.plans-distribution h3 {
  margin: 0 0 1.5rem 0;
  color: white;
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

.plan-info {
  min-width: 120px;
  display: flex;
  flex-direction: column;
}

.plan-name {
  font-weight: 600;
  color: white;
}

.plan-count {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.bar-container {
  flex: 1;
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.bar.free { background: linear-gradient(90deg, #64748b, #475569); }
.bar.basic { background: linear-gradient(90deg, #3b82f6, #2563eb); }
.bar.pro { background: linear-gradient(90deg, #10b981, #059669); }
.bar.elite { background: linear-gradient(90deg, #f59e0b, #d97706); }

.plan-percentage {
  min-width: 60px;
  text-align: right;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

.filters-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  flex: 1;
}

.filter-input, .filter-select {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.75rem;
  color: white;
  font-size: 0.9rem;
}

.filter-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.table-container {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.users-table td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: rgba(0, 217, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #00d9ff;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: white;
}

.plan-badge, .status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.plan-badge.free { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.plan-badge.basic { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.plan-badge.pro { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.plan-badge.elite { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

.status-badge.active { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
.status-badge.inactive { background: rgba(239, 68, 68, 0.2); color: #f87171; }

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-action.view {
  background: rgba(0, 217, 255, 0.2);
  color: #00d9ff;
  border: 1px solid rgba(0, 217, 255, 0.3);
}

.btn-action.view:hover {
  background: rgba(0, 217, 255, 0.3);
}

.no-users {
  padding: 3rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
}

.date-info {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}
</style>