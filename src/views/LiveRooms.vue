<script setup>
/**
 * 🔴 LiveRooms.vue - Jogos Ao Vivo
 * ODINENX v2.0 - Dados 100% REAIS da Football-Data.org API
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const mobileMenuOpen = ref(false)
const games = ref([])
const selectedFilter = ref('all')
const refreshInterval = ref(null)
const lastUpdate = ref(null)

// Football-Data.org API Key
const FOOTBALL_API_KEY = '1d1cd9e04db74a98ac8246a1668a0532'

// Ligas suportadas
const LEAGUES = {
  'BSA': { name: 'Brasileirão Série A', flag: '🇧🇷', code: 2013 },
  'PL': { name: 'Premier League', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', code: 2021 },
  'PD': { name: 'La Liga', flag: '🇪🇸', code: 2014 },
  'SA': { name: 'Serie A', flag: '🇮🇹', code: 2019 },
  'BL1': { name: 'Bundesliga', flag: '🇩🇪', code: 2002 },
  'FL1': { name: 'Ligue 1', flag: '🇫🇷', code: 2015 },
  'CL': { name: 'Champions League', flag: '🇪🇺', code: 2001 }
}

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  await loadGames()
  loading.value = false
  
  // Atualizar a cada 60 segundos
  refreshInterval.value = setInterval(loadGames, 60000)
})

onUnmounted(() => {
  if (refreshInterval.value) clearInterval(refreshInterval.value)
})

async function loadGames() {
  try {
    // Primeiro tenta buscar do Supabase (cache)
    const { data: cachedGames, error } = await supabase
      .from('game_rooms')
      .select('*')
      .order('match_date', { ascending: true })
    
    if (!error && cachedGames?.length > 0) {
      games.value = cachedGames.map(formatGame)
      lastUpdate.value = new Date()
      console.log(`✅ Carregou ${cachedGames.length} jogos do cache`)
      return
    }
    
    // Se não tem cache, busca da API diretamente
    await fetchLiveFromAPI()
  } catch (err) {
    console.error('Erro ao carregar jogos:', err)
    // Fallback: busca da API
    await fetchLiveFromAPI()
  }
}

async function fetchLiveFromAPI() {
  try {
    // Buscar jogos de hoje e próximos
    const today = new Date().toISOString().split('T')[0]
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    
    const response = await fetch(`https://api.football-data.org/v4/matches?dateFrom=${today}&dateTo=${nextWeek}`, {
      headers: { 'X-Auth-Token': FOOTBALL_API_KEY }
    })
    
    if (response.ok) {
      const data = await response.json()
      games.value = (data.matches || []).map(match => ({
        id: match.id,
        home_team: match.homeTeam.shortName || match.homeTeam.name,
        away_team: match.awayTeam.shortName || match.awayTeam.name,
        home_logo: match.homeTeam.crest,
        away_logo: match.awayTeam.crest,
        home_score: match.score?.fullTime?.home ?? (match.score?.halfTime?.home ?? null),
        away_score: match.score?.fullTime?.away ?? (match.score?.halfTime?.away ?? null),
        status: mapStatus(match.status),
        match_date: match.utcDate,
        league: match.competition.code,
        league_name: LEAGUES[match.competition.code]?.name || match.competition.name,
        league_flag: LEAGUES[match.competition.code]?.flag || '⚽',
        venue: match.venue || 'A definir',
        minute: match.minute || null
      }))
      lastUpdate.value = new Date()
      console.log(`✅ Carregou ${games.value.length} jogos da API`)
    }
  } catch (err) {
    console.error('Erro ao buscar da API:', err)
  }
}

function formatGame(game) {
  return {
    ...game,
    league_flag: LEAGUES[game.league]?.flag || '⚽',
    league_name: LEAGUES[game.league]?.name || game.league
  }
}

function mapStatus(apiStatus) {
  const statusMap = {
    'IN_PLAY': 'live',
    'PAUSED': 'halftime',
    'FINISHED': 'finished',
    'SCHEDULED': 'scheduled',
    'TIMED': 'scheduled',
    'POSTPONED': 'postponed',
    'CANCELLED': 'cancelled'
  }
  return statusMap[apiStatus] || 'scheduled'
}

const filteredGames = computed(() => {
  if (selectedFilter.value === 'all') return games.value
  if (selectedFilter.value === 'live') return games.value.filter(g => g.status === 'live' || g.status === 'halftime')
  if (selectedFilter.value === 'today') {
    const today = new Date().toDateString()
    return games.value.filter(g => new Date(g.match_date).toDateString() === today)
  }
  return games.value.filter(g => g.league === selectedFilter.value)
})

const liveCount = computed(() => games.value.filter(g => g.status === 'live' || g.status === 'halftime').length)
const todayCount = computed(() => {
  const today = new Date().toDateString()
  return games.value.filter(g => new Date(g.match_date).toDateString() === today).length
})

function getStatusClass(status) {
  const classes = {
    'live': 'status-live',
    'halftime': 'status-halftime',
    'finished': 'status-finished',
    'scheduled': 'status-scheduled',
    'postponed': 'status-postponed'
  }
  return classes[status] || 'status-scheduled'
}

function getStatusText(status, minute) {
  const texts = {
    'live': minute ? `${minute}'` : '🔴 AO VIVO',
    'halftime': 'INTERVALO',
    'finished': 'ENCERRADO',
    'scheduled': 'AGENDADO',
    'postponed': 'ADIADO'
  }
  return texts[status] || status
}

function formatDateTime(dateStr) {
  const date = new Date(dateStr)
  const day = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  const time = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  return `${day} às ${time}`
}

async function refreshGames() {
  loading.value = true
  await fetchLiveFromAPI()
  loading.value = false
}

const currentPlan = computed(() => plans[subscription.value?.plan] || plans.free)
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
        <router-link to="/live" class="nav-item live-nav active"><span class="live-indicator"></span><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>Jogos ao Vivo</router-link>
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>BET</router-link>
        <router-link to="/trade" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>TRADE</router-link>
        <router-link to="/cartola" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>Cartola FC</router-link>
        <div class="nav-category">Acompanhamento</div>
        <router-link to="/alerts" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>Alertas</router-link>
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
        <button @click="navigateTo('/live')" class="mobile-nav-item live-mobile active">🔴 Ao Vivo</button>
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</button>
        <button @click="navigateTo('/cartola')" class="mobile-nav-item">Cartola FC</button>
        <button @click="navigateTo('/alerts')" class="mobile-nav-item">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item">Configurações</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header">
        <div class="header-left">
          <h1>🔴 Jogos Ao Vivo</h1>
          <p v-if="lastUpdate">Última atualização: {{ lastUpdate.toLocaleTimeString('pt-BR') }}</p>
        </div>
        <button @click="refreshGames" class="btn-refresh" :disabled="loading">
          <svg :class="{ spinning: loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          Atualizar
        </button>
      </header>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card live-card">
          <div class="stat-icon-wrapper live"><div class="live-dot"></div><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ liveCount }}</span><span class="stat-label">Ao vivo agora</span></div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrapper"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ todayCount }}</span><span class="stat-label">Jogos hoje</span></div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrapper success"><svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ games.length }}</span><span class="stat-label">Total de jogos</span></div>
        </div>
      </div>

      <!-- Filters -->
      <div class="filters">
        <button @click="selectedFilter = 'all'" :class="{ active: selectedFilter === 'all' }">Todos</button>
        <button @click="selectedFilter = 'live'" :class="{ active: selectedFilter === 'live' }">🔴 Ao Vivo</button>
        <button @click="selectedFilter = 'today'" :class="{ active: selectedFilter === 'today' }">Hoje</button>
        <button @click="selectedFilter = 'BSA'" :class="{ active: selectedFilter === 'BSA' }">🇧🇷 Brasileirão</button>
        <button @click="selectedFilter = 'PL'" :class="{ active: selectedFilter === 'PL' }">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier</button>
        <button @click="selectedFilter = 'CL'" :class="{ active: selectedFilter === 'CL' }">🇪🇺 Champions</button>
      </div>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>

      <div v-else class="games-content">
        <!-- Games List -->
        <div v-if="filteredGames.length > 0" class="games-grid">
          <div v-for="game in filteredGames" :key="game.id" class="game-card" :class="getStatusClass(game.status)">
            <!-- League Header -->
            <div class="game-league">
              <span class="league-flag">{{ game.league_flag }}</span>
              <span class="league-name">{{ game.league_name }}</span>
              <span class="game-status" :class="getStatusClass(game.status)">{{ getStatusText(game.status, game.minute) }}</span>
            </div>
            
            <!-- Match Info -->
            <div class="match-info">
              <div class="team home">
                <img v-if="game.home_logo" :src="game.home_logo" :alt="game.home_team" class="team-logo" @error="$event.target.style.display='none'" />
                <div v-else class="team-logo-placeholder">⚽</div>
                <span class="team-name">{{ game.home_team }}</span>
              </div>
              
              <div class="score-container">
                <template v-if="game.home_score !== null">
                  <span class="score">{{ game.home_score }}</span>
                  <span class="score-divider">-</span>
                  <span class="score">{{ game.away_score }}</span>
                </template>
                <template v-else>
                  <span class="match-time">{{ formatDateTime(game.match_date) }}</span>
                </template>
              </div>
              
              <div class="team away">
                <img v-if="game.away_logo" :src="game.away_logo" :alt="game.away_team" class="team-logo" @error="$event.target.style.display='none'" />
                <div v-else class="team-logo-placeholder">⚽</div>
                <span class="team-name">{{ game.away_team }}</span>
              </div>
            </div>
            
            <!-- Live indicator -->
            <div v-if="game.status === 'live'" class="live-bar">
              <div class="live-progress" :style="{ width: `${(game.minute || 45) / 90 * 100}%` }"></div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <div class="empty-icon-wrapper"><svg class="empty-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>
          <h4>Nenhum jogo encontrado</h4>
          <p>Não há jogos {{ selectedFilter === 'live' ? 'ao vivo' : 'para o filtro selecionado' }} no momento.</p>
          <button @click="selectedFilter = 'all'" class="btn-start">Ver Todos os Jogos</button>
        </div>
      </div>

      <!-- API Info -->
      <div class="api-info">
        <span>📡 Dados em tempo real via Football-Data.org</span>
        <span>⚽ {{ Object.keys(LEAGUES).length }} ligas monitoradas</span>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard { display: flex; min-height: 100vh; background: #000; color: #fff; }
.sidebar { width: 260px; background: rgba(255, 255, 255, 0.02); border-right: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-direction: column; position: fixed; height: 100vh; left: 0; top: 0; }
.sidebar-header { padding: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.sidebar-logo { height: 35px; }
.sidebar-nav { flex: 1; padding: 20px 15px; display: flex; flex-direction: column; gap: 5px; overflow-y: auto; }
.nav-category { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255, 255, 255, 0.35); padding: 15px 15px 8px; font-weight: 600; }
.nav-category:first-child { padding-top: 0; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 15px; color: rgba(255, 255, 255, 0.6); border-radius: 10px; transition: all 0.3s; text-decoration: none; }
.nav-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
.nav-item.active { background: rgba(255, 255, 255, 0.1); color: #fff; }
.nav-item.live-nav { background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%); border: 1px solid rgba(255, 68, 68, 0.3); color: #ff6b6b; position: relative; }
.nav-item.live-nav.active { background: linear-gradient(135deg, rgba(255, 68, 68, 0.2) 0%, rgba(255, 140, 0, 0.2) 100%); border-color: rgba(255, 68, 68, 0.5); }
.live-indicator { position: absolute; top: 50%; right: 12px; transform: translateY(-50%); width: 8px; height: 8px; background: #ff4444; border-radius: 50%; animation: live-pulse 1.5s infinite; }
@keyframes live-pulse { 0%, 100% { opacity: 1; transform: translateY(-50%) scale(1); } 50% { opacity: 0.5; transform: translateY(-50%) scale(1.2); } }
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
.btn-refresh { display: flex; align-items: center; gap: 8px; padding: 12px 20px; background: rgba(255, 255, 255, 0.1); color: #fff; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; font-weight: 500; cursor: pointer; transition: all 0.3s; }
.btn-refresh:hover { background: rgba(255, 255, 255, 0.15); border-color: rgba(255, 255, 255, 0.3); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-refresh svg { width: 18px; height: 18px; }
.btn-refresh svg.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.loading-container { display: flex; justify-content: center; padding: 100px; }
.spinner { width: 40px; height: 40px; border: 3px solid rgba(255, 255, 255, 0.1); border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; display: flex; align-items: center; gap: 20px; }
.stat-card.live-card { background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%); border-color: rgba(255, 68, 68, 0.3); }
.stat-icon-wrapper { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; position: relative; }
.stat-icon-wrapper.live { background: rgba(255, 68, 68, 0.2); }
.stat-icon-wrapper.live .stat-svg { stroke: #ff6b6b; }
.live-dot { position: absolute; top: 5px; right: 5px; width: 8px; height: 8px; background: #ff4444; border-radius: 50%; animation: live-pulse 1.5s infinite; }
.stat-icon-wrapper.success { background: rgba(34, 197, 94, 0.15); }
.stat-icon-wrapper.success .stat-svg { stroke: #22c55e; }
.stat-svg { width: 28px; height: 28px; stroke: #fff; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 2rem; font-weight: 800; }
.stat-label { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }

.filters { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; }
.filters button { padding: 10px 18px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; color: rgba(255, 255, 255, 0.7); cursor: pointer; transition: all 0.3s; font-weight: 500; }
.filters button:hover { background: rgba(255, 255, 255, 0.1); }
.filters button.active { background: #fff; color: #000; border-color: #fff; }

.games-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
.game-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; transition: all 0.3s; }
.game-card:hover { border-color: rgba(255, 255, 255, 0.2); transform: translateY(-2px); }
.game-card.status-live { border-color: rgba(255, 68, 68, 0.5); background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.05) 100%); }

.game-league { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; font-size: 0.85rem; }
.league-flag { font-size: 1.2rem; }
.league-name { color: rgba(255, 255, 255, 0.7); flex: 1; }
.game-status { padding: 4px 10px; border-radius: 15px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
.game-status.status-live { background: rgba(255, 68, 68, 0.2); color: #ff6b6b; animation: status-pulse 1.5s infinite; }
@keyframes status-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
.game-status.status-halftime { background: rgba(234, 179, 8, 0.2); color: #eab308; }
.game-status.status-finished { background: rgba(107, 114, 128, 0.2); color: #9ca3af; }
.game-status.status-scheduled { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.game-status.status-postponed { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.match-info { display: flex; align-items: center; justify-content: space-between; gap: 15px; }
.team { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 120px; }
.team-logo { width: 50px; height: 50px; object-fit: contain; }
.team-logo-placeholder { width: 50px; height: 50px; background: rgba(255, 255, 255, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.team-name { font-size: 0.85rem; text-align: center; color: rgba(255, 255, 255, 0.9); font-weight: 500; }

.score-container { display: flex; align-items: center; gap: 8px; }
.score { font-size: 2rem; font-weight: 800; min-width: 30px; text-align: center; }
.score-divider { color: rgba(255, 255, 255, 0.3); font-size: 1.5rem; }
.match-time { font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); text-align: center; }

.live-bar { margin-top: 15px; height: 4px; background: rgba(255, 255, 255, 0.1); border-radius: 2px; overflow: hidden; }
.live-progress { height: 100%; background: linear-gradient(90deg, #ff6b6b, #ff8c00); border-radius: 2px; transition: width 0.3s; }

.empty-state { text-align: center; padding: 80px 40px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
.empty-icon-wrapper { width: 100px; height: 100px; background: rgba(255, 255, 255, 0.05); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 30px; }
.empty-svg { width: 50px; height: 50px; stroke: rgba(255, 255, 255, 0.5); }
.empty-state h4 { font-size: 1.5rem; margin-bottom: 10px; }
.empty-state p { color: rgba(255, 255, 255, 0.5); margin-bottom: 25px; }
.btn-start { padding: 15px 30px; background: #fff; color: #000; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-start:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2); }

.api-info { display: flex; justify-content: center; gap: 30px; margin-top: 40px; padding: 15px; background: rgba(255, 255, 255, 0.02); border-radius: 10px; color: rgba(255, 255, 255, 0.4); font-size: 0.85rem; }

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
  .games-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .page-header h1 { font-size: 1.5rem; }
  .api-info { flex-direction: column; gap: 10px; text-align: center; }
  .filters { justify-content: center; }
}
</style>
