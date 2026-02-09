<script setup>
/**
 * 📊 History.vue - Histórico de Análises
 * ODINENX v2.0 - Visual consistente com Dashboard
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans, isAdmin as checkIsAdmin } from '../lib/stripe'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const mobileMenuOpen = ref(false)
const history = ref([])
const activeFilter = ref('all')
const userIsAdmin = ref(false)

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  userIsAdmin.value = await checkIsAdmin(session.user.id)
  await loadHistory()
  loading.value = false
})

async function loadHistory() {
  try {
    const { data, error } = await supabase
      .from('analysis_history')
      .select('*')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })
      .limit(50)
    
    if (!error && data) history.value = data
  } catch (err) {
    console.log('Histórico não disponível:', err)
  }
}

const currentPlan = computed(() => plans[subscription.value?.plan] || plans.free)
const filteredHistory = computed(() => activeFilter.value === 'all' ? history.value : history.value.filter(h => h.type === activeFilter.value))

const logout = async () => { await supabase.auth.signOut(); router.push('/') }
const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value }
const navigateTo = (path) => { router.push(path); mobileMenuOpen.value = false }
const formatDate = (date) => new Date(date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
</script>

<template>
  <div class="dashboard">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header"><router-link to="/"><img src="/logo.webp" alt="ODINENX" class="sidebar-logo" /></router-link></div>
      <nav class="sidebar-nav">
        <div class="nav-category">Principal</div>
        <router-link to="/dashboard" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>Dashboard</router-link>
        <div class="nav-category">Ao Vivo</div>
        <router-link to="/live" class="nav-item live-nav"><span class="live-indicator"></span><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>Jogos ao Vivo</router-link>
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>BET</router-link>
        <router-link to="/trade" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>TRADE</router-link>
        <router-link to="/cartola" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>Cartola FC</router-link>
        <div class="nav-category">Acompanhamento</div>
        <router-link to="/alerts" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>Alertas</router-link>
        <router-link to="/history" class="nav-item active"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>Histórico</router-link>
        <div class="nav-category">Sistema</div>
        <router-link to="/settings" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Configurações</router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="plan-badge-sidebar">{{ currentPlan.name }}</div>
        <button @click="logout" class="logout-btn"><svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>Sair</button>
      </div>
    </aside>

    <!-- Mobile -->
    <button class="mobile-menu-btn" @click="toggleMobileMenu">
      <svg v-if="!mobileMenuOpen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>
    <nav class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-header"><img src="/logo.webp" alt="ODINENX" class="mobile-logo" /></div>
      <div class="mobile-nav">
        <button @click="navigateTo('/dashboard')" class="mobile-nav-item">Dashboard</button>
        <button @click="navigateTo('/live')" class="mobile-nav-item live-mobile">🔴 Ao Vivo</button>
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</button>
        <button @click="navigateTo('/cartola')" class="mobile-nav-item">Cartola FC</button>
        <button @click="navigateTo('/alerts')" class="mobile-nav-item">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item active">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item">Configurações</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header"><div class="header-left"><h1>📊 Histórico</h1><p>Suas análises e operações anteriores</p></div></header>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>

      <div v-else class="history-content">
        <!-- Stats -->
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-icon-wrapper"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21H3V3"/><path d="M21 9l-6 6-4-4-6 6"/></svg></div><div class="stat-info"><span class="stat-value">{{ history.length }}</span><span class="stat-label">Total de análises</span></div></div>
          <div class="stat-card"><div class="stat-icon-wrapper success"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><div class="stat-info"><span class="stat-value">{{ history.filter(h => h.result === 'win').length }}</span><span class="stat-label">Análises corretas</span></div></div>
          <div class="stat-card"><div class="stat-icon-wrapper warning"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></div><div class="stat-info"><span class="stat-value">{{ history.length > 0 ? Math.round((history.filter(h => h.result === 'win').length / history.length) * 100) : 0 }}%</span><span class="stat-label">Taxa de acerto</span></div></div>
        </div>

        <!-- Filters -->
        <div class="filters-section">
          <button class="filter-btn" :class="{ active: activeFilter === 'all' }" @click="activeFilter = 'all'">Todos</button>
          <button class="filter-btn" :class="{ active: activeFilter === 'bet' }" @click="activeFilter = 'bet'">🎰 BET</button>
          <button class="filter-btn" :class="{ active: activeFilter === 'trade' }" @click="activeFilter = 'trade'">📈 TRADE</button>
          <button class="filter-btn" :class="{ active: activeFilter === 'cartola' }" @click="activeFilter = 'cartola'">⚽ Cartola</button>
        </div>

        <!-- History List -->
        <div v-if="filteredHistory.length > 0" class="history-list">
          <div v-for="item in filteredHistory" :key="item.id" class="history-card">
            <div class="history-type" :class="item.type">{{ item.type === 'bet' ? '🎰' : item.type === 'trade' ? '📈' : '⚽' }}</div>
            <div class="history-info"><h4>{{ item.title }}</h4><p>{{ item.description }}</p><span class="history-date">{{ formatDate(item.created_at) }}</span></div>
            <div class="history-result" :class="item.result">{{ item.result === 'win' ? '✅' : item.result === 'loss' ? '❌' : '⏳' }}</div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <div class="empty-icon-wrapper"><svg class="empty-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg></div>
          <h4>Nenhuma análise ainda</h4>
          <p>Suas análises e operações aparecerão aqui conforme você usa a plataforma.</p>
          <router-link to="/bet" class="btn-start">Fazer Primeira Análise</router-link>
        </div>
      </div>
    </main>

    <!-- Bottom Navigation Mobile -->
    <BottomNav :showAdmin="userIsAdmin" />
  </div>
</template>

<style scoped>
.dashboard { display: flex; display: -webkit-box; display: -webkit-flex; min-height: 100vh; min-height: 100dvh; min-height: -webkit-fill-available; background: #000; color: #fff; -webkit-overflow-scrolling: touch; }
.sidebar { width: 260px; background: rgba(255, 255, 255, 0.02); border-right: 1px solid rgba(255, 255, 255, 0.1); display: flex; display: -webkit-box; display: -webkit-flex; -webkit-box-orient: vertical; -webkit-box-direction: normal; flex-direction: column; position: fixed; height: 100vh; height: 100dvh; height: -webkit-fill-available; left: 0; top: 0; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
.sidebar-header { padding: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.sidebar-logo { height: 35px; }
.sidebar-nav { flex: 1; padding: 20px 15px; display: flex; flex-direction: column; gap: 5px; overflow-y: auto; }
.nav-category { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255, 255, 255, 0.35); padding: 15px 15px 8px; font-weight: 600; }
.nav-category:first-child { padding-top: 0; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 15px; color: rgba(255, 255, 255, 0.6); border-radius: 10px; transition: all 0.3s; text-decoration: none; }
.nav-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
.nav-item.active { background: rgba(255, 255, 255, 0.1); color: #fff; }
.nav-item.live-nav { background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%); border: 1px solid rgba(255, 68, 68, 0.3); color: #ff6b6b; position: relative; }
.live-indicator { position: absolute; top: 50%; right: 12px; transform: translateY(-50%); width: 8px; height: 8px; background: #ff4444; border-radius: 50%; animation: live-pulse 1.5s infinite; }
@keyframes live-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.nav-icon { width: 20px; height: 20px; flex-shrink: 0; }
.sidebar-footer { padding: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-direction: column; gap: 15px; }
.plan-badge-sidebar { background: rgba(255, 255, 255, 0.1); padding: 8px 15px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; text-align: center; }
.logout-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: transparent; border: 1px solid rgba(255, 255, 255, 0.2); color: rgba(255, 255, 255, 0.6); padding: 10px; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
.logout-btn:hover { border-color: #ff6b6b; color: #ff6b6b; }
.logout-icon { width: 18px; height: 18px; }

.main-content { flex: 1; margin-left: 260px; padding: 30px; }
.page-header { margin-bottom: 40px; }
.page-header h1 { font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
.page-header p { color: rgba(255, 255, 255, 0.5); }

.loading-container { display: flex; justify-content: center; padding: 100px; }
.spinner { width: 40px; height: 40px; border: 3px solid rgba(255, 255, 255, 0.1); border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }
.stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; display: flex; align-items: center; gap: 20px; }
.stat-icon-wrapper { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; }
.stat-icon-wrapper.success { background: rgba(34, 197, 94, 0.15); }
.stat-icon-wrapper.success .stat-svg { stroke: #22c55e; }
.stat-icon-wrapper.warning { background: rgba(234, 179, 8, 0.15); }
.stat-icon-wrapper.warning .stat-svg { stroke: #eab308; }
.stat-svg { width: 28px; height: 28px; stroke: #fff; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 2rem; font-weight: 800; }
.stat-label { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }

.filters-section { display: flex; gap: 10px; margin-bottom: 30px; flex-wrap: wrap; }
.filter-btn { padding: 10px 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; color: rgba(255, 255, 255, 0.7); cursor: pointer; transition: all 0.3s; font-weight: 500; }
.filter-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
.filter-btn.active { background: #fff; color: #000; border-color: #fff; }

.history-list { display: flex; flex-direction: column; gap: 15px; }
.history-card { display: flex; align-items: center; gap: 20px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; transition: all 0.3s; }
.history-card:hover { border-color: rgba(255, 255, 255, 0.2); transform: translateX(5px); }
.history-type { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; background: rgba(255, 255, 255, 0.05); }
.history-type.bet { background: rgba(239, 68, 68, 0.2); }
.history-type.trade { background: rgba(59, 130, 246, 0.2); }
.history-type.cartola { background: rgba(34, 197, 94, 0.2); }
.history-info { flex: 1; }
.history-info h4 { font-size: 1.1rem; margin-bottom: 5px; }
.history-info p { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; margin-bottom: 5px; }
.history-date { font-size: 0.8rem; color: rgba(255, 255, 255, 0.3); }
.history-result { font-size: 1.5rem; }

.empty-state { text-align: center; padding: 80px 40px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
.empty-icon-wrapper { width: 100px; height: 100px; background: rgba(234, 179, 8, 0.15); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 30px; }
.empty-svg { width: 50px; height: 50px; stroke: #eab308; }
.empty-state h4 { font-size: 1.5rem; margin-bottom: 10px; }
.empty-state p { color: rgba(255, 255, 255, 0.5); margin-bottom: 25px; }
.btn-start { display: inline-block; padding: 15px 30px; background: #fff; color: #000; text-decoration: none; border-radius: 10px; font-weight: 600; transition: all 0.3s; }
.btn-start:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2); }

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
.mobile-nav-item.live-mobile { background: linear-gradient(135deg, rgba(255, 68, 68, 0.15) 0%, rgba(255, 140, 0, 0.15) 100%); border: 1px solid rgba(255, 68, 68, 0.3); color: #ff6b6b; }
.mobile-logout { width: 100%; margin-top: 15px; padding: 15px; background: transparent; border: 1px solid #ef4444; border-radius: 12px; color: #ef4444; font-weight: 600; cursor: pointer; }

@media (max-width: 968px) {
  .sidebar { display: none; }
  .mobile-menu-btn { display: none; }
  .mobile-overlay { display: none; }
  .mobile-menu { display: none; }
  .main-content { margin-left: 0; padding: 20px; padding-bottom: 85px; }
  .stats-grid { grid-template-columns: 1fr; }
  .page-header h1 { font-size: 1.5rem; }
}
</style>
