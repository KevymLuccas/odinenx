<script setup>
/**
 * 🔔 Alerts.vue - Sistema de Alertas
 * ODINENX v2.0 - Visual consistente com Dashboard
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const mobileMenuOpen = ref(false)
const alerts = ref([])
const showCreateModal = ref(false)
const newAlert = ref({ name: '', type: 'price', asset: '', condition: 'above', value: '', active: true })

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  await loadAlerts()
  loading.value = false
})

async function loadAlerts() {
  try {
    const { data, error } = await supabase
      .from('user_alerts')
      .select('*')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })
    
    if (!error && data) alerts.value = data
  } catch (err) {
    console.log('Alertas não disponíveis:', err)
  }
}

async function createAlert() {
  if (!newAlert.value.name || !newAlert.value.asset || !newAlert.value.value) {
    alert('Preencha todos os campos!')
    return
  }
  
  try {
    const { data, error } = await supabase
      .from('user_alerts')
      .insert({
        user_id: user.value.id,
        name: newAlert.value.name,
        type: newAlert.value.type,
        asset: newAlert.value.asset,
        condition: newAlert.value.condition,
        target_value: parseFloat(newAlert.value.value),
        active: true
      })
      .select()
      .single()
    
    if (!error && data) {
      alerts.value.unshift(data)
      showCreateModal.value = false
      newAlert.value = { name: '', type: 'price', asset: '', condition: 'above', value: '', active: true }
    }
  } catch (err) {
    console.error('Erro ao criar alerta:', err)
    alert('Erro ao criar alerta')
  }
}

async function toggleAlert(alertItem) {
  try {
    const { error } = await supabase
      .from('user_alerts')
      .update({ active: !alertItem.active })
      .eq('id', alertItem.id)
    
    if (!error) alertItem.active = !alertItem.active
  } catch (err) {
    console.error('Erro ao atualizar alerta:', err)
  }
}

async function deleteAlert(alertId) {
  if (!confirm('Deseja excluir este alerta?')) return
  
  try {
    const { error } = await supabase
      .from('user_alerts')
      .delete()
      .eq('id', alertId)
    
    if (!error) alerts.value = alerts.value.filter(a => a.id !== alertId)
  } catch (err) {
    console.error('Erro ao excluir alerta:', err)
  }
}

const currentPlan = computed(() => plans[subscription.value?.plan] || plans.free)
const activeAlerts = computed(() => alerts.value.filter(a => a.active))

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
        <div class="nav-category">Ao Vivo</div>
        <router-link to="/live" class="nav-item live-nav"><span class="live-indicator"></span><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>Jogos ao Vivo</router-link>
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
        <button @click="navigateTo('/alerts')" class="mobile-nav-item active">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item">Configurações</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header">
        <div class="header-left"><h1>🔔 Alertas</h1><p>Configure notificações para seus ativos</p></div>
        <button @click="showCreateModal = true" class="btn-create">+ Novo Alerta</button>
      </header>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>

      <div v-else class="alerts-content">
        <!-- Stats -->
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-icon-wrapper"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></div><div class="stat-info"><span class="stat-value">{{ alerts.length }}</span><span class="stat-label">Total de alertas</span></div></div>
          <div class="stat-card"><div class="stat-icon-wrapper success"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><div class="stat-info"><span class="stat-value">{{ activeAlerts.length }}</span><span class="stat-label">Alertas ativos</span></div></div>
          <div class="stat-card"><div class="stat-icon-wrapper warning"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div><div class="stat-info"><span class="stat-value">{{ currentPlan.limits?.alerts === -1 ? '∞' : currentPlan.limits?.alerts || 3 }}</span><span class="stat-label">Limite do plano</span></div></div>
        </div>

        <!-- Alerts List -->
        <div v-if="alerts.length > 0" class="alerts-list">
          <div v-for="alertItem in alerts" :key="alertItem.id" class="alert-card" :class="{ inactive: !alertItem.active }">
            <div class="alert-icon">🔔</div>
            <div class="alert-info">
              <h4>{{ alertItem.name }}</h4>
              <p>{{ alertItem.asset }} {{ alertItem.condition === 'above' ? '>' : '<' }} {{ alertItem.target_value }}</p>
            </div>
            <div class="alert-actions">
              <button @click="toggleAlert(alertItem)" class="btn-toggle" :class="{ active: alertItem.active }">
                {{ alertItem.active ? 'Ativo' : 'Pausado' }}
              </button>
              <button @click="deleteAlert(alertItem.id)" class="btn-delete">🗑️</button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <div class="empty-icon-wrapper"><svg class="empty-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></div>
          <h4>Nenhum alerta configurado</h4>
          <p>Crie alertas para ser notificado quando seus ativos atingirem valores específicos.</p>
          <button @click="showCreateModal = true" class="btn-start">Criar Primeiro Alerta</button>
        </div>
      </div>
    </main>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h3>Criar Novo Alerta</h3>
        <div class="form-group">
          <label>Nome do Alerta</label>
          <input v-model="newAlert.name" type="text" placeholder="Ex: Bitcoin acima de R$ 350.000" class="form-input" />
        </div>
        <div class="form-group">
          <label>Ativo</label>
          <input v-model="newAlert.asset" type="text" placeholder="Ex: BTC, PETR4, Flamengo" class="form-input" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Condição</label>
            <select v-model="newAlert.condition" class="form-select">
              <option value="above">Acima de</option>
              <option value="below">Abaixo de</option>
            </select>
          </div>
          <div class="form-group">
            <label>Valor</label>
            <input v-model="newAlert.value" type="number" placeholder="0.00" class="form-input" />
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showCreateModal = false" class="btn-cancel">Cancelar</button>
          <button @click="createAlert" class="btn-confirm">Criar Alerta</button>
        </div>
      </div>
    </div>
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
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; flex-wrap: wrap; gap: 20px; }
.page-header h1 { font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
.page-header p { color: rgba(255, 255, 255, 0.5); }
.btn-create { padding: 12px 25px; background: #fff; color: #000; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-create:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2); }

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

.alerts-list { display: flex; flex-direction: column; gap: 15px; }
.alert-card { display: flex; align-items: center; gap: 20px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; transition: all 0.3s; }
.alert-card:hover { border-color: rgba(255, 255, 255, 0.2); }
.alert-card.inactive { opacity: 0.5; }
.alert-icon { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; background: rgba(234, 179, 8, 0.2); }
.alert-info { flex: 1; }
.alert-info h4 { font-size: 1.1rem; margin-bottom: 5px; }
.alert-info p { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }
.alert-actions { display: flex; gap: 10px; }
.btn-toggle { padding: 8px 16px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2); background: transparent; color: rgba(255, 255, 255, 0.6); cursor: pointer; transition: all 0.3s; font-weight: 500; }
.btn-toggle.active { background: rgba(34, 197, 94, 0.2); border-color: #22c55e; color: #22c55e; }
.btn-delete { padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.3); background: transparent; cursor: pointer; transition: all 0.3s; }
.btn-delete:hover { background: rgba(239, 68, 68, 0.2); }

.empty-state { text-align: center; padding: 80px 40px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
.empty-icon-wrapper { width: 100px; height: 100px; background: rgba(234, 179, 8, 0.15); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 30px; }
.empty-svg { width: 50px; height: 50px; stroke: #eab308; }
.empty-state h4 { font-size: 1.5rem; margin-bottom: 10px; }
.empty-state p { color: rgba(255, 255, 255, 0.5); margin-bottom: 25px; }
.btn-start { padding: 15px 30px; background: #fff; color: #000; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-start:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal { background: #111; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 30px; max-width: 450px; width: 100%; }
.modal h3 { font-size: 1.5rem; margin-bottom: 25px; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; }
.form-input, .form-select { width: 100%; padding: 12px 15px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: #fff; font-size: 1rem; }
.form-input:focus, .form-select:focus { outline: none; border-color: rgba(255, 255, 255, 0.3); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.modal-actions { display: flex; gap: 15px; margin-top: 25px; }
.btn-cancel { flex: 1; padding: 12px; background: transparent; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; color: #fff; cursor: pointer; transition: all 0.3s; }
.btn-cancel:hover { border-color: #fff; }
.btn-confirm { flex: 1; padding: 12px; background: #fff; border: none; border-radius: 10px; color: #000; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-confirm:hover { transform: translateY(-2px); }

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
  .mobile-menu-btn { display: flex; }
  .mobile-overlay { display: block; }
  .mobile-menu { display: block; }
  .main-content { margin-left: 0; padding: 20px; padding-bottom: 100px; }
  .stats-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .page-header h1 { font-size: 1.5rem; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
