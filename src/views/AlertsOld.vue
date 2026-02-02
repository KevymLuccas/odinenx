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
  
  // Verificar acesso aos Alertas
  if (!hasAccess(subscription.value, 'alerts')) {
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
      .from('alerts_config')
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
      .from('alerts_config')
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
  return marketData.value[type] || []
}

const logout = async () => { await supabase.auth.signOut(); router.push('/') }
const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value }
const navigateTo = (path) => { router.push(path); mobileMenuOpen.value = false }
</script>

<template>
  <div class="dashboard">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header"><router-link to="/"><img src="/logo.webp" alt="ODINENX" class="sidebar-logo" /></router-link></div>
      <nav class="sidebar-nav">
        <div class="nav-category">Principal</div>
        <router-link to="/dashboard" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>Dashboard</router-link>
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>BET</router-link>
        <router-link to="/trade" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>TRADE</router-link>
        <router-link to="/cartola" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>Cartola FC</router-link>
        <div class="nav-category">Acompanhamento</div>
        <router-link to="/alerts" class="nav-item active"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>Alertas</router-link>
        <router-link to="/history" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>Histórico</router-link>
        <div class="nav-category">Sistema</div>
        <router-link to="/settings" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Configurações</router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="plan-badge-sidebar">{{ currentPlan.name }}</div>
        <button @click="logout" class="logout-btn"><svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>Sair</button>
      </div>
    </aside>

    <!-- Mobile Menu Button -->
    <button class="mobile-menu-btn" @click="toggleMobileMenu">
      <svg v-if="!mobileMenuOpen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>

    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>
    <nav class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-header"><img src="/logo.webp" alt="ODINENX" class="mobile-logo" /></div>
      <div class="mobile-nav">
        <button @click="navigateTo('/dashboard')" class="mobile-nav-item">Dashboard</button>
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</button>
        <button @click="navigateTo('/cartola')" class="mobile-nav-item">Cartola FC</button>
        <button @click="navigateTo('/alerts')" class="mobile-nav-item active">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item">Configurações</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header"><h1>Alertas</h1><p>Notificações e alertas em tempo real</p></header>

      <div class="empty-state">
        <div class="icon-wrapper"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></div>
        <h2>Nenhum alerta</h2>
        <p>Você será notificado quando houver oportunidades importantes.</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard { display: flex; min-height: 100vh; background: #000; color: #fff; }
.sidebar { width: 260px; background: rgba(10, 10, 10, 0.95); border-right: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-direction: column; position: fixed; height: 100vh; z-index: 100; }
.sidebar-header { padding: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.sidebar-logo { height: 40px; width: auto; }
.sidebar-nav { flex: 1; padding: 20px 15px; display: flex; flex-direction: column; gap: 5px; overflow-y: auto; }
.nav-category { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255, 255, 255, 0.35); padding: 15px 15px 8px; font-weight: 600; }
.nav-category:first-child { padding-top: 0; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 15px; border-radius: 10px; color: rgba(255, 255, 255, 0.6); text-decoration: none; transition: all 0.3s; font-weight: 500; }
.nav-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
.nav-item.active { background: rgba(255, 255, 255, 0.1); color: #fff; }
.nav-icon { width: 20px; height: 20px; }
.sidebar-footer { padding: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.plan-badge-sidebar { background: rgba(255, 255, 255, 0.1); padding: 8px 15px; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 15px; font-size: 0.9rem; }
.logout-btn { width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px; background: transparent; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: rgba(255, 255, 255, 0.6); cursor: pointer; transition: all 0.3s; }
.logout-btn:hover { border-color: #ef4444; color: #ef4444; }
.logout-icon { width: 18px; height: 18px; }

.mobile-menu-btn { display: none; position: fixed; top: 20px; right: 20px; width: 50px; height: 50px; border-radius: 12px; background: rgba(255, 255, 255, 0.95); border: none; box-shadow: 0 5px 30px rgba(0, 0, 0, 0.3); z-index: 1000; cursor: pointer; align-items: center; justify-content: center; }
.mobile-menu-btn svg { width: 28px; height: 28px; stroke: #000; }
.mobile-overlay { display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); z-index: 998; }
.mobile-menu { display: none; position: fixed; bottom: 0; left: 0; right: 0; background: #0a0a0a; border-top-left-radius: 25px; border-top-right-radius: 25px; padding: 25px; z-index: 999; transform: translateY(100%); transition: transform 0.3s ease; }
.mobile-menu.open { transform: translateY(0); }
.mobile-menu-header { text-align: center; margin-bottom: 20px; }
.mobile-logo { height: 35px; }
.mobile-nav { display: flex; flex-direction: column; gap: 8px; }
.mobile-nav-item { padding: 15px 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #fff; font-weight: 500; cursor: pointer; transition: all 0.3s; text-align: left; }
.mobile-nav-item:hover, .mobile-nav-item.active { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); }
.mobile-logout { width: 100%; margin-top: 15px; padding: 15px; background: transparent; border: 1px solid #ef4444; border-radius: 12px; color: #ef4444; font-weight: 600; cursor: pointer; }

.main-content { flex: 1; margin-left: 260px; padding: 30px; }
.page-header { margin-bottom: 40px; }
.page-header h1 { font-size: 2rem; font-weight: 800; margin-bottom: 8px; }
.page-header p { color: rgba(255, 255, 255, 0.5); }

.empty-state { max-width: 500px; margin: 0 auto; text-align: center; padding: 80px 40px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
.icon-wrapper { width: 100px; height: 100px; background: rgba(168, 85, 247, 0.15); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 30px; }
.icon-wrapper svg { width: 50px; height: 50px; stroke: #a855f7; }
.empty-state h2 { font-size: 1.5rem; margin-bottom: 10px; }
.empty-state p { color: rgba(255, 255, 255, 0.5); }

@media (max-width: 968px) {
  .sidebar { display: none; }
  .mobile-menu-btn { display: flex; }
  .mobile-overlay { display: block; }
  .mobile-menu { display: block; }
  .main-content { margin-left: 0; padding: 20px; padding-bottom: 100px; }
}
</style>
