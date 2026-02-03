<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, isAdmin } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const activeTab = ref('dashboard')

// Admin data
const adminStats = ref(null)
const users = ref([])
const adminLogs = ref([])
const selectedUser = ref(null)

// Modals
const showGrantPlanModal = ref(false)
const showRevokeAccessModal = ref(false)
const grantPlanData = ref({ plan: 'basic' })

// Filters
const userFilter = ref('')
const planFilter = ref('all')

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
  loading.value = false
})

const loadAdminData = async () => {
  try {
    // Carregar usuários
    const { data: usersData } = await supabase
      .from('profiles')
      .select('*')
      .order('created_at', { ascending: false })
    
    users.value = usersData || []

    // Carregar logs administrativos
    const { data: logsData } = await supabase
      .from('admin_logs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50)
    
    adminLogs.value = logsData || []

  } catch (error) {
    console.error('Erro ao carregar dados admin:', error)
  }
}

const filteredUsers = computed(() => {
  let filtered = users.value
  
  if (userFilter.value) {
    const search = userFilter.value.toLowerCase()
    filtered = filtered.filter(u => 
      u.email?.toLowerCase().includes(search) || 
      u.full_name?.toLowerCase().includes(search)
    )
  }
  
  return filtered
})

const grantPlan = async () => {
  if (!selectedUser.value) return

  try {
    const { data } = await supabase
      .rpc('grant_plan_to_user', {
        target_user_id: selectedUser.value.id,
        plan_id: grantPlanData.value.plan,
        admin_id: user.value.id,
        expires_at: grantPlanData.value.expires_at || null
      })

    if (data?.success) {
      alert(`✅ Plano ${grantPlanData.value.plan} concedido com sucesso!`)
      await loadAdminData()
      showGrantPlanModal.value = false
    } else {
      alert(`❌ Erro: ${data?.error || 'Erro desconhecido'}`)
    }
  } catch (error) {
    console.error('Erro ao conceder plano:', error)
    alert('❌ Erro ao conceder plano')
  }
}

const revokeAccess = async () => {
  if (!selectedUser.value) return

  try {
    const { data } = await supabase
      .rpc('revoke_user_access', {
        target_user_id: selectedUser.value.id,
        admin_id: user.value.id
      })

    if (data?.success) {
      alert('✅ Acesso revogado com sucesso!')
      await loadAdminData()
      showRevokeAccessModal.value = false
    } else {
      alert(`❌ Erro: ${data?.error || 'Erro desconhecido'}`)
    }
  } catch (error) {
    console.error('Erro ao revogar acesso:', error)
    alert('❌ Erro ao revogar acesso')
  }
}

const openGrantPlanModal = (userObj) => {
  selectedUser.value = userObj
  grantPlanData.value = { plan: 'basic' }
  showGrantPlanModal.value = true
}

const openRevokeAccessModal = (userObj) => {
  selectedUser.value = userObj
  showRevokeAccessModal.value = true
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('pt-BR')
}

const getUserPlan = (userObj) => {
  return userObj.stripe_customer_id ? 'PAGO' : 'FREE'
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}
</script>

<template>
  <div class="admin-container">
    <!-- Header -->
    <header class="admin-header">
      <div class="header-content">
        <div class="header-left">
          <h1>🛡️ Painel Administrativo</h1>
          <p>Gerenciamento completo do sistema ODINENX</p>
        </div>
        <div class="header-right">
          <div class="admin-info">
            <span class="admin-badge">ADMINISTRADOR</span>
            <span class="admin-email">{{ user?.email }}</span>
          </div>
          <button @click="logout" class="btn-logout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16,17 21,12 16,7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Sair
          </button>
        </div>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Content -->
    <div v-else class="admin-content">
      
      <!-- Tabs -->
      <div class="admin-tabs">
        <button 
          @click="activeTab = 'dashboard'"
          :class="{ active: activeTab === 'dashboard' }"
          class="tab-button"
        >
          📊 Dashboard
        </button>
        <button 
          @click="activeTab = 'users'"
          :class="{ active: activeTab === 'users' }"
          class="tab-button"
        >
          👥 Usuários
        </button>
        <button 
          @click="activeTab = 'logs'"
          :class="{ active: activeTab === 'logs' }"
          class="tab-button"
        >
          📋 Logs
        </button>
      </div>

      <!-- Dashboard Tab -->
      <div v-show="activeTab === 'dashboard'" class="tab-content">
        
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ users.length }}</span>
              <span class="stat-label">Total de Usuários</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon green">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22,6 13.5,14.5 8.5,9.5 2,16"/>
                <polyline points="16,6 22,6 22,12"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ users.filter(u => u.stripe_customer_id).length }}</span>
              <span class="stat-label">Assinaturas Ativas</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon yellow">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ users.filter(u => !u.stripe_customer_id).length }}</span>
              <span class="stat-label">Usuários Free</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon purple">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ formatCurrency(users.filter(u => u.stripe_customer_id).length * 79) }}</span>
              <span class="stat-label">Receita Estimada</span>
            </div>
          </div>
        </div>

      </div>

      <!-- Users Tab -->
      <div v-show="activeTab === 'users'" class="tab-content">
        
        <!-- Filters -->
        <div class="filters-section">
          <div class="filter-group">
            <input 
              v-model="userFilter"
              type="text" 
              placeholder="🔍 Buscar por email ou nome..."
              class="filter-input"
            >
          </div>
        </div>

        <!-- Users Table -->
        <div class="table-container">
          <table class="users-table">
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Plano</th>
                <th>Cadastro</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="userObj in filteredUsers" :key="userObj.id">
                <td>
                  <div class="user-info">
                    <div class="user-avatar">{{ userObj.full_name?.[0] || userObj.email?.[0] || 'U' }}</div>
                    <div class="user-details">
                      <span class="user-name">{{ userObj.full_name || 'Usuário' }}</span>
                      <span class="user-email">{{ userObj.email }}</span>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="plan-badge" :class="getUserPlan(userObj).toLowerCase()">
                    {{ getUserPlan(userObj) }}
                  </span>
                </td>
                <td>{{ formatDate(userObj.created_at) }}</td>
                <td>
                  <div class="action-buttons">
                    <button 
                      @click="openGrantPlanModal(userObj)"
                      class="btn-action grant"
                    >
                      🎁 Conceder
                    </button>
                    <button 
                      @click="openRevokeAccessModal(userObj)"
                      class="btn-action revoke"
                    >
                      🚫 Revogar
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="filteredUsers.length === 0" class="empty-state">
            <p>Nenhum usuário encontrado</p>
          </div>
        </div>

      </div>

      <!-- Logs Tab -->
      <div v-show="activeTab === 'logs'" class="tab-content">
        
        <h3>📋 Logs Administrativos</h3>
        
        <div class="logs-container">
          <div v-if="adminLogs.length === 0" class="empty-state">
            <p>Nenhum log administrativo encontrado</p>
          </div>
          <div v-for="log in adminLogs" :key="log.id" class="log-item">
            <div class="log-header">
              <span class="log-action">{{ log.action }}</span>
              <span class="log-date">{{ formatDate(log.created_at) }}</span>
            </div>
            <div class="log-details">
              <p v-if="log.details"><strong>Detalhes:</strong> {{ JSON.stringify(log.details) }}</p>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Grant Plan Modal -->
    <div v-if="showGrantPlanModal" class="modal-overlay" @click="showGrantPlanModal = false">
      <div class="modal" @click.stop>
        <h3>🎁 Conceder Plano</h3>
        <p>Conceder plano para: <strong>{{ selectedUser?.email }}</strong></p>
        
        <div class="form-group">
          <label>Plano:</label>
          <select v-model="grantPlanData.plan" class="form-control">
            <option value="basic">Basic (R$ 79)</option>
            <option value="pro">Pro (R$ 199)</option>
            <option value="elite">Elite (R$ 399)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Data de Expiração (opcional):</label>
          <input v-model="grantPlanData.expires_at" type="datetime-local" class="form-control">
        </div>

        <div class="modal-actions">
          <button @click="grantPlan" class="btn-confirm">Conceder Plano</button>
          <button @click="showGrantPlanModal = false" class="btn-cancel">Cancelar</button>
        </div>
      </div>
    </div>

    <!-- Revoke Access Modal -->
    <div v-if="showRevokeAccessModal" class="modal-overlay" @click="showRevokeAccessModal = false">
      <div class="modal" @click.stop>
        <h3>🚫 Revogar Acesso</h3>
        <p>Tem certeza que deseja revogar o acesso de: <strong>{{ selectedUser?.email }}</strong>?</p>
        <p class="warning">⚠️ Esta ação irá:</p>
        <ul class="warning-list">
          <li>Expirar o trial do usuário</li>
          <li>Remover planos concedidos</li>
          <li>Bloquear acesso às funcionalidades pagas</li>
        </ul>

        <div class="modal-actions">
          <button @click="revokeAccess" class="btn-confirm danger">Revogar Acesso</button>
          <button @click="showRevokeAccessModal = false" class="btn-cancel">Cancelar</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a, #1a1a1a, #2d2d2d);
  color: white;
}

.admin-header {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2rem;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
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
  display: flex;
  align-items: center;
  gap: 2rem;
}

.admin-info {
  display: flex;
  flex-direction: column;
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.btn-logout svg {
  width: 16px;
  height: 16px;
}

.admin-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

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
  border-top-color: #00d9ff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.admin-tabs {
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
}

.stat-icon.blue { background: rgba(0, 217, 255, 0.15); }
.stat-icon.green { background: rgba(34, 197, 94, 0.15); }
.stat-icon.yellow { background: rgba(245, 158, 11, 0.15); }
.stat-icon.purple { background: rgba(168, 85, 247, 0.15); }

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon.blue svg { color: #00d9ff; }
.stat-icon.green svg { color: #22c55e; }
.stat-icon.yellow svg { color: #f59e0b; }
.stat-icon.purple svg { color: #a855f7; }

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

.filters-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  flex: 1;
}

.filter-input {
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

.user-email {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.plan-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.plan-badge.free { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.plan-badge.pago { background: rgba(34, 197, 94, 0.2); color: #4ade80; }

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

.btn-action.grant {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.btn-action.grant:hover {
  background: rgba(34, 197, 94, 0.3);
}

.btn-action.revoke {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.btn-action.revoke:hover {
  background: rgba(239, 68, 68, 0.3);
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
}

.logs-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.log-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.log-action {
  background: rgba(0, 217, 255, 0.2);
  color: #00d9ff;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
}

.log-date {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
}

.log-details p {
  margin: 0.25rem 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
}

.modal h3 {
  margin: 0 0 1rem 0;
  color: white;
}

.modal p {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 1.5rem;
}

.warning {
  color: #fbbf24 !important;
  font-weight: 600;
}

.warning-list {
  color: rgba(255, 255, 255, 0.7);
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.form-control {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.75rem;
  color: white;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-confirm, .btn-cancel {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-confirm {
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  color: white;
}

.btn-confirm.danger {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
}

.btn-confirm:hover {
  transform: translateY(-2px);
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.15);
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .admin-tabs {
    flex-wrap: wrap;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .filters-section {
    flex-direction: column;
  }
  
  .users-table {
    font-size: 0.8rem;
  }
}
</style>
