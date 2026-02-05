<script setup>
/**
 * 🔴 LiveRooms.vue - Jogos Ao Vivo com Acompanhamento de Apostas
 * ODINENX v2.0 - Dados em tempo real via API-Football (api-sports.io)
 * Sistema de pontuação conforme odds selecionadas
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
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

// Ligas suportadas (para exibição de filtros)
const LEAGUES = {
  'BSA': { name: 'Brasileirão Série A', flag: '🇧🇷' },
  'PL': { name: 'Premier League', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  'PD': { name: 'La Liga', flag: '🇪🇸' },
  'SA': { name: 'Serie A', flag: '🇮🇹' },
  'BL1': { name: 'Bundesliga', flag: '🇩🇪' },
  'FL1': { name: 'Ligue 1', flag: '🇫🇷' },
  'CL': { name: 'Champions League', flag: '🇪🇺' }
}

const apiError = ref(null)
const isRefreshing = ref(false)

// ===============================================
// 🎯 SISTEMA DE ACOMPANHAMENTO DE APOSTAS
// ===============================================
const showOddsModal = ref(false)
const selectedGame = ref(null)
const userBets = ref([]) // Apostas ativas do usuário
const savingBet = ref(false)

// Tipos de odds disponíveis
const oddTypes = [
  { id: 'home', label: 'Vitória Casa', icon: '🏠', category: '1x2' },
  { id: 'draw', label: 'Empate', icon: '🤝', category: '1x2' },
  { id: 'away', label: 'Vitória Fora', icon: '✈️', category: '1x2' },
  { id: 'over_0.5', label: 'Over 0.5 Gols', icon: '⬆️', category: 'gols' },
  { id: 'over_1.5', label: 'Over 1.5 Gols', icon: '⬆️', category: 'gols' },
  { id: 'over_2.5', label: 'Over 2.5 Gols', icon: '⬆️', category: 'gols' },
  { id: 'over_3.5', label: 'Over 3.5 Gols', icon: '⬆️', category: 'gols' },
  { id: 'under_0.5', label: 'Under 0.5 Gols', icon: '⬇️', category: 'gols' },
  { id: 'under_1.5', label: 'Under 1.5 Gols', icon: '⬇️', category: 'gols' },
  { id: 'under_2.5', label: 'Under 2.5 Gols', icon: '⬇️', category: 'gols' },
  { id: 'under_3.5', label: 'Under 3.5 Gols', icon: '⬇️', category: 'gols' },
  { id: 'btts_yes', label: 'Ambas Marcam - Sim', icon: '⚽', category: 'btts' },
  { id: 'btts_no', label: 'Ambas Marcam - Não', icon: '🚫', category: 'btts' },
  { id: 'home_1h', label: 'Casa Vence 1º Tempo', icon: '1️⃣', category: 'tempo' },
  { id: 'draw_1h', label: 'Empate 1º Tempo', icon: '1️⃣', category: 'tempo' },
  { id: 'away_1h', label: 'Fora Vence 1º Tempo', icon: '1️⃣', category: 'tempo' },
]

// Dados do formulário de odd
const betForm = ref({
  selectedOdds: [],
  oddValues: {}, // { 'home': 1.85, 'over_2.5': 2.10 }
  stake: 100 // Valor apostado
})

// Carregar apostas ativas do usuário
async function loadUserBets() {
  if (!user.value) return
  
  try {
    const { data, error } = await supabase
      .from('user_odds')
      .select('*, game_rooms(*)')
      .eq('user_id', user.value.id)
      .eq('status', 'pending')
    
    if (data) {
      userBets.value = data
    }
  } catch (err) {
    console.error('Erro ao carregar apostas:', err)
  }
}

// Abrir modal de odds para um jogo
function openOddsModal(game) {
  selectedGame.value = game
  betForm.value = {
    selectedOdds: [],
    oddValues: {},
    stake: 100
  }
  showOddsModal.value = true
}

// Fechar modal
function closeOddsModal() {
  showOddsModal.value = false
  selectedGame.value = null
}

// Toggle seleção de odd
function toggleOddSelection(oddId) {
  const idx = betForm.value.selectedOdds.indexOf(oddId)
  if (idx > -1) {
    betForm.value.selectedOdds.splice(idx, 1)
    delete betForm.value.oddValues[oddId]
  } else {
    betForm.value.selectedOdds.push(oddId)
    betForm.value.oddValues[oddId] = '' // Valor inicial vazio
  }
}

// Salvar acompanhamento
async function saveOddTracking() {
  if (!user.value || !selectedGame.value) return
  if (betForm.value.selectedOdds.length === 0) {
    alert('Selecione pelo menos uma odd para acompanhar!')
    return
  }
  
  // Validar se todas as odds têm valor
  for (const oddId of betForm.value.selectedOdds) {
    if (!betForm.value.oddValues[oddId] || parseFloat(betForm.value.oddValues[oddId]) <= 1) {
      alert(`Informe a odd para: ${oddTypes.find(o => o.id === oddId)?.label}`)
      return
    }
  }
  
  savingBet.value = true
  
  try {
    // Primeiro, criar ou buscar a sala do jogo
    let roomId = null
    
    const { data: existingRoom } = await supabase
      .from('game_rooms')
      .select('id')
      .eq('fixture_id', selectedGame.value.id)
      .single()
    
    if (existingRoom) {
      roomId = existingRoom.id
    } else {
      // Criar sala para o jogo
      const { data: newRoom, error: roomError } = await supabase
        .from('game_rooms')
        .insert({
          fixture_id: selectedGame.value.id,
          home_team: selectedGame.value.home_team,
          away_team: selectedGame.value.away_team,
          home_team_logo: selectedGame.value.home_logo,
          away_team_logo: selectedGame.value.away_logo,
          home_score: selectedGame.value.home_score || 0,
          away_score: selectedGame.value.away_score || 0,
          minute: selectedGame.value.minute || 0,
          status: selectedGame.value.status,
          league: selectedGame.value.league_name,
          league_logo: selectedGame.value.league_logo,
          start_time: selectedGame.value.match_date,
          owner_id: user.value.id
        })
        .select()
        .single()
      
      if (roomError) throw roomError
      roomId = newRoom.id
    }
    
    // Inserir cada odd selecionada
    const oddsToInsert = betForm.value.selectedOdds.map(oddId => ({
      room_id: roomId,
      user_id: user.value.id,
      odd_type: oddTypes.find(o => o.id === oddId)?.category || 'other',
      odd_pick: oddId,
      odd_value: parseFloat(betForm.value.oddValues[oddId]),
      status: 'pending'
    }))
    
    const { error: oddsError } = await supabase
      .from('user_odds')
      .insert(oddsToInsert)
    
    if (oddsError) throw oddsError
    
    // Recarregar apostas
    await loadUserBets()
    
    closeOddsModal()
    alert('✅ Acompanhamento salvo! Suas odds serão monitoradas.')
    
  } catch (err) {
    console.error('Erro ao salvar:', err)
    alert('Erro ao salvar acompanhamento. Tente novamente.')
  } finally {
    savingBet.value = false
  }
}

// Calcular status da aposta baseado no placar atual
function getBetStatus(bet, game) {
  if (!game) return 'pending'
  
  const totalGoals = (game.home_score || 0) + (game.away_score || 0)
  const homeScore = game.home_score || 0
  const awayScore = game.away_score || 0
  
  switch (bet.odd_pick) {
    // 1x2
    case 'home':
      if (game.status === 'finished') return homeScore > awayScore ? 'won' : 'lost'
      return homeScore > awayScore ? 'winning' : homeScore < awayScore ? 'losing' : 'pending'
    case 'draw':
      if (game.status === 'finished') return homeScore === awayScore ? 'won' : 'lost'
      return homeScore === awayScore ? 'winning' : 'losing'
    case 'away':
      if (game.status === 'finished') return awayScore > homeScore ? 'won' : 'lost'
      return awayScore > homeScore ? 'winning' : awayScore < homeScore ? 'losing' : 'pending'
    
    // Over/Under
    case 'over_0.5':
      if (totalGoals >= 1) return game.status === 'finished' ? 'won' : 'winning'
      return game.status === 'finished' ? 'lost' : 'pending'
    case 'over_1.5':
      if (totalGoals >= 2) return game.status === 'finished' ? 'won' : 'winning'
      return game.status === 'finished' ? 'lost' : 'pending'
    case 'over_2.5':
      if (totalGoals >= 3) return game.status === 'finished' ? 'won' : 'winning'
      return game.status === 'finished' ? 'lost' : 'pending'
    case 'over_3.5':
      if (totalGoals >= 4) return game.status === 'finished' ? 'won' : 'winning'
      return game.status === 'finished' ? 'lost' : 'pending'
    case 'under_0.5':
      if (totalGoals >= 1) return game.status === 'finished' ? 'lost' : 'losing'
      return game.status === 'finished' ? 'won' : 'winning'
    case 'under_1.5':
      if (totalGoals >= 2) return game.status === 'finished' ? 'lost' : 'losing'
      return game.status === 'finished' ? 'won' : 'winning'
    case 'under_2.5':
      if (totalGoals >= 3) return game.status === 'finished' ? 'lost' : 'losing'
      return game.status === 'finished' ? 'won' : 'winning'
    case 'under_3.5':
      if (totalGoals >= 4) return game.status === 'finished' ? 'lost' : 'losing'
      return game.status === 'finished' ? 'won' : 'winning'
    
    // BTTS
    case 'btts_yes':
      if (homeScore > 0 && awayScore > 0) return game.status === 'finished' ? 'won' : 'winning'
      return game.status === 'finished' ? 'lost' : 'pending'
    case 'btts_no':
      if (homeScore > 0 && awayScore > 0) return game.status === 'finished' ? 'lost' : 'losing'
      return game.status === 'finished' ? 'won' : 'winning'
    
    default:
      return 'pending'
  }
}

// Buscar jogo ativo para uma aposta
function getGameForBet(bet) {
  return games.value.find(g => g.id === bet.game_rooms?.fixture_id) || null
}

// Verificar se o usuário tem acompanhamento neste jogo
function hasTrackingForGame(gameId) {
  return userBets.value.some(b => b.game_rooms?.fixture_id === gameId)
}

// Buscar apostas do usuário para um jogo específico
function getBetsForGame(gameId) {
  return userBets.value.filter(b => b.game_rooms?.fixture_id === gameId)
}

// 🏟️ Entrar na sala do jogo
async function enterGameRoom(game) {
  try {
    // Buscar ou criar sala
    let { data: existingRoom } = await supabase
      .from('game_rooms')
      .select('id')
      .eq('fixture_id', game.id)
      .single()
    
    if (!existingRoom) {
      // Criar nova sala
      const { data: newRoom, error } = await supabase
        .from('game_rooms')
        .insert({
          fixture_id: game.id,
          home_team: game.home_team,
          away_team: game.away_team,
          home_team_logo: game.home_logo,
          away_team_logo: game.away_logo,
          home_score: game.home_score || 0,
          away_score: game.away_score || 0,
          minute: game.minute || 0,
          status: game.status,
          league: game.league_name,
          league_logo: game.league_logo,
          start_time: game.match_date,
          owner_id: user.value.id
        })
        .select()
        .single()
      
      if (error) throw error
      existingRoom = newRoom
    }
    
    // Redirecionar para a sala
    router.push(`/live/${existingRoom.id}`)
  } catch (err) {
    console.error('Erro ao entrar na sala:', err)
    alert('Erro ao entrar na sala. Tente novamente.')
  }
}

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  await loadGames()
  await loadUserBets() // Carregar apostas ativas
  loading.value = false
  
  // Atualizar a cada 30 segundos para jogos ao vivo
  refreshInterval.value = setInterval(async () => {
    await loadGames()
    await loadUserBets() // Atualizar status das apostas
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval.value) clearInterval(refreshInterval.value)
})

async function loadGames() {
  try {
    isRefreshing.value = true
    apiError.value = null
    await fetchLiveFromAPI()
  } catch (err) {
    console.error('Erro ao carregar jogos:', err)
    apiError.value = 'Erro ao carregar jogos. Tentando novamente...'
  } finally {
    isRefreshing.value = false
  }
}

async function fetchLiveFromAPI() {
  try {
    const response = await fetch('/api/live-games')
    const data = await response.json()
    
    console.log('🔴 API Response:', data)
    
    if (data.success && data.games) {
      games.value = data.games
      lastUpdate.value = new Date()
      apiError.value = null
      console.log(`✅ ${data.live_count || 0} jogos ao vivo, ${data.count} total`)
    } else if (data.games) {
      games.value = data.games
      lastUpdate.value = new Date()
    } else if (data.message) {
      apiError.value = data.message
    }
  } catch (err) {
    console.error('Erro ao buscar da API:', err)
    apiError.value = 'Falha na conexão. Verificando...'
  }
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
          <p v-if="lastUpdate">
            Atualização: {{ lastUpdate.toLocaleTimeString('pt-BR') }}
            <span v-if="isRefreshing" class="refresh-indicator">⟳ Atualizando...</span>
          </p>
          <p v-if="apiError" class="api-error">⚠️ {{ apiError }}</p>
        </div>
        <button @click="refreshGames" class="btn-refresh" :disabled="loading || isRefreshing">
          <svg :class="{ spinning: loading || isRefreshing }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          {{ isRefreshing ? 'Atualizando...' : 'Atualizar' }}
        </button>
      </header>

      <!-- Auto-update indicator -->
      <div class="auto-update-bar">
        <span class="auto-dot"></span>
        Atualização automática a cada 30 segundos
      </div>

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
              <img v-if="game.league_flag && game.league_flag.startsWith('http')" :src="game.league_flag" class="league-flag-img" @error="$event.target.style.display='none'" />
              <span v-else class="league-flag">{{ game.league_flag || '⚽' }}</span>
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
            
            <!-- Tracking Info (se já tem acompanhamento) -->
            <div v-if="hasTrackingForGame(game.id)" class="tracking-info">
              <div class="tracking-bets">
                <div v-for="bet in getBetsForGame(game.id)" :key="bet.id" class="tracking-bet" :class="getBetStatus(bet, game)">
                  <span class="bet-pick">{{ oddTypes.find(o => o.id === bet.odd_pick)?.icon }} {{ oddTypes.find(o => o.id === bet.odd_pick)?.label }}</span>
                  <span class="bet-odd">@{{ bet.odd_value }}</span>
                  <span class="bet-status-icon">
                    <span v-if="getBetStatus(bet, game) === 'winning'">✅</span>
                    <span v-else-if="getBetStatus(bet, game) === 'losing'">❌</span>
                    <span v-else-if="getBetStatus(bet, game) === 'won'">🏆</span>
                    <span v-else-if="getBetStatus(bet, game) === 'lost'">💔</span>
                    <span v-else>⏳</span>
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Botão Entrar na Sala -->
            <button v-if="game.status === 'live' || game.status === 'halftime'" @click.stop="enterGameRoom(game)" class="btn-enter-room">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
              🏟️ Entrar na Sala
            </button>
            
            <!-- Botão Acompanhar (para jogos agendados) -->
            <button v-else-if="game.status === 'scheduled'" @click.stop="openOddsModal(game)" class="btn-track">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Definir Odds
            </button>
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
        <span>📡 Dados em tempo real via API-Football</span>
        <span>⚡ Atualização a cada 15 segundos</span>
        <span>⚽ +800 ligas disponíveis</span>
      </div>
      
      <!-- Seção de Apostas Ativas -->
      <div v-if="userBets.length > 0" class="active-bets-section">
        <h3>🎯 Suas Apostas em Andamento</h3>
        <div class="active-bets-grid">
          <div v-for="bet in userBets" :key="bet.id" class="active-bet-card" :class="getBetStatus(bet, getGameForBet(bet))">
            <div class="bet-game-info">
              <span class="bet-teams">{{ bet.game_rooms?.home_team }} vs {{ bet.game_rooms?.away_team }}</span>
              <span class="bet-league">{{ bet.game_rooms?.league }}</span>
            </div>
            <div class="bet-details">
              <span class="bet-type">{{ oddTypes.find(o => o.id === bet.odd_pick)?.icon }} {{ oddTypes.find(o => o.id === bet.odd_pick)?.label }}</span>
              <span class="bet-value">@{{ bet.odd_value }}</span>
            </div>
            <div class="bet-status-badge" :class="getBetStatus(bet, getGameForBet(bet))">
              <span v-if="getBetStatus(bet, getGameForBet(bet)) === 'winning'">✅ Ganhando</span>
              <span v-else-if="getBetStatus(bet, getGameForBet(bet)) === 'losing'">❌ Perdendo</span>
              <span v-else-if="getBetStatus(bet, getGameForBet(bet)) === 'won'">🏆 Ganhou!</span>
              <span v-else-if="getBetStatus(bet, getGameForBet(bet)) === 'lost'">💔 Perdeu</span>
              <span v-else>⏳ Aguardando</span>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <!-- Modal de Seleção de Odds -->
    <Teleport to="body">
      <div v-if="showOddsModal" class="modal-overlay" @click="closeOddsModal">
        <div class="modal-content odds-modal" @click.stop>
          <button class="modal-close" @click="closeOddsModal">×</button>
          
          <div class="modal-header">
            <h2>🎯 Selecione suas Odds</h2>
            <p>Quais apostas você está acompanhando neste jogo?</p>
          </div>
          
          <!-- Jogo Selecionado -->
          <div v-if="selectedGame" class="selected-game-preview">
            <div class="game-teams">
              <img v-if="selectedGame.home_logo" :src="selectedGame.home_logo" class="preview-logo" />
              <span>{{ selectedGame.home_team }}</span>
              <span class="vs">VS</span>
              <span>{{ selectedGame.away_team }}</span>
              <img v-if="selectedGame.away_logo" :src="selectedGame.away_logo" class="preview-logo" />
            </div>
            <div class="game-meta">
              <span>{{ selectedGame.league_name }}</span>
              <span v-if="selectedGame.status === 'live'" class="live-badge">🔴 {{ selectedGame.minute }}'</span>
            </div>
          </div>
          
          <!-- Categorias de Odds -->
          <div class="odds-categories">
            <!-- 1x2 -->
            <div class="odds-category">
              <h4>⚽ Resultado Final (1x2)</h4>
              <div class="odds-buttons">
                <button v-for="odd in oddTypes.filter(o => o.category === '1x2')" :key="odd.id"
                  @click="toggleOddSelection(odd.id)"
                  class="odd-btn" 
                  :class="{ selected: betForm.selectedOdds.includes(odd.id) }">
                  <span class="odd-icon">{{ odd.icon }}</span>
                  <span class="odd-label">{{ odd.label }}</span>
                </button>
              </div>
            </div>
            
            <!-- Gols -->
            <div class="odds-category">
              <h4>📊 Over/Under Gols</h4>
              <div class="odds-buttons">
                <button v-for="odd in oddTypes.filter(o => o.category === 'gols')" :key="odd.id"
                  @click="toggleOddSelection(odd.id)"
                  class="odd-btn" 
                  :class="{ selected: betForm.selectedOdds.includes(odd.id) }">
                  <span class="odd-icon">{{ odd.icon }}</span>
                  <span class="odd-label">{{ odd.label }}</span>
                </button>
              </div>
            </div>
            
            <!-- BTTS -->
            <div class="odds-category">
              <h4>🥅 Ambas Marcam (BTTS)</h4>
              <div class="odds-buttons">
                <button v-for="odd in oddTypes.filter(o => o.category === 'btts')" :key="odd.id"
                  @click="toggleOddSelection(odd.id)"
                  class="odd-btn" 
                  :class="{ selected: betForm.selectedOdds.includes(odd.id) }">
                  <span class="odd-icon">{{ odd.icon }}</span>
                  <span class="odd-label">{{ odd.label }}</span>
                </button>
              </div>
            </div>
            
            <!-- Tempo -->
            <div class="odds-category">
              <h4>⏱️ Primeiro Tempo</h4>
              <div class="odds-buttons">
                <button v-for="odd in oddTypes.filter(o => o.category === 'tempo')" :key="odd.id"
                  @click="toggleOddSelection(odd.id)"
                  class="odd-btn" 
                  :class="{ selected: betForm.selectedOdds.includes(odd.id) }">
                  <span class="odd-icon">{{ odd.icon }}</span>
                  <span class="odd-label">{{ odd.label }}</span>
                </button>
              </div>
            </div>
          </div>
          
          <!-- Valores das Odds Selecionadas -->
          <div v-if="betForm.selectedOdds.length > 0" class="selected-odds-values">
            <h4>💰 Informe as Odds</h4>
            <div class="odds-inputs">
              <div v-for="oddId in betForm.selectedOdds" :key="oddId" class="odd-input-row">
                <span class="odd-input-label">{{ oddTypes.find(o => o.id === oddId)?.icon }} {{ oddTypes.find(o => o.id === oddId)?.label }}</span>
                <input type="number" step="0.01" min="1.01" placeholder="Ex: 1.85" v-model="betForm.oddValues[oddId]" class="odd-input" />
              </div>
            </div>
          </div>
          
          <!-- Resumo e Botão -->
          <div class="modal-footer">
            <div class="odds-summary">
              <span v-if="betForm.selectedOdds.length === 0">Selecione pelo menos uma odd para acompanhar</span>
              <span v-else>{{ betForm.selectedOdds.length }} odd(s) selecionada(s)</span>
            </div>
            <div class="modal-actions">
              <button @click="closeOddsModal" class="btn-cancel">Cancelar</button>
              <button @click="saveOddTracking" :disabled="betForm.selectedOdds.length === 0 || savingBet" class="btn-save">
                <span v-if="savingBet">Salvando...</span>
                <span v-else>🎯 Iniciar Acompanhamento</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
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
.league-flag-img { width: 22px; height: 16px; object-fit: cover; border-radius: 2px; }
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

/* Botão Entrar na Sala */
.btn-enter-room { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; margin-top: 15px; padding: 14px; background: linear-gradient(135deg, #ff6b6b, #ff8c00); border: none; border-radius: 12px; color: #fff; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3); }
.btn-enter-room:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4); }
.btn-enter-room svg { width: 20px; height: 20px; }

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

/* API Error & Refresh Indicator */
.api-error { color: #f59e0b; font-size: 0.8rem; margin-top: 5px; display: flex; align-items: center; gap: 5px; }
.refresh-indicator { color: #8b5cf6; font-size: 0.75rem; margin-left: 10px; animation: pulse 1s infinite; }
.auto-update-bar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 8px; font-size: 0.85rem; color: #a78bfa; margin-bottom: 20px; }
.auto-dot { width: 8px; height: 8px; background: #8b5cf6; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Botão Acompanhar no Card */
.btn-track { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; margin-top: 15px; padding: 12px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2)); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 10px; color: #a78bfa; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-track:hover { background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(59, 130, 246, 0.3)); border-color: rgba(139, 92, 246, 0.5); transform: translateY(-2px); }
.btn-track.active { background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2)); border-color: rgba(34, 197, 94, 0.4); color: #22c55e; }
.btn-track svg { width: 18px; height: 18px; }

/* Tracking Info no Card */
.tracking-info { margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.tracking-bets { display: flex; flex-direction: column; gap: 8px; }
.tracking-bet { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; background: rgba(255, 255, 255, 0.03); border-radius: 8px; font-size: 0.85rem; }
.tracking-bet.winning { background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); }
.tracking-bet.losing { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }
.tracking-bet.won { background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2)); border: 1px solid rgba(34, 197, 94, 0.4); }
.tracking-bet.lost { background: rgba(107, 114, 128, 0.2); border: 1px solid rgba(107, 114, 128, 0.3); opacity: 0.7; }
.bet-pick { color: rgba(255, 255, 255, 0.8); }
.bet-odd { color: #a78bfa; font-weight: 600; }
.bet-status-icon { font-size: 1.1rem; }

/* Seção de Apostas Ativas */
.active-bets-section { margin-top: 40px; padding-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.active-bets-section h3 { font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; }
.active-bets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
.active-bet-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
.active-bet-card.winning { border-color: rgba(34, 197, 94, 0.4); background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.05)); }
.active-bet-card.losing { border-color: rgba(239, 68, 68, 0.4); background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05)); }
.active-bet-card.won { border-color: rgba(34, 197, 94, 0.5); background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.1)); }
.active-bet-card.lost { border-color: rgba(107, 114, 128, 0.3); opacity: 0.6; }
.bet-game-info { display: flex; flex-direction: column; gap: 3px; }
.bet-teams { font-weight: 600; color: #fff; }
.bet-league { font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); }
.bet-details { display: flex; justify-content: space-between; align-items: center; }
.bet-type { color: rgba(255, 255, 255, 0.8); font-size: 0.9rem; }
.bet-value { color: #a78bfa; font-weight: 700; font-size: 1.1rem; }
.bet-status-badge { padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-align: center; }
.bet-status-badge.winning { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.bet-status-badge.losing { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.bet-status-badge.won { background: rgba(34, 197, 94, 0.3); color: #22c55e; }
.bet-status-badge.lost { background: rgba(107, 114, 128, 0.2); color: #9ca3af; }
.bet-status-badge.pending { background: rgba(234, 179, 8, 0.2); color: #eab308; }

/* Modal Overlay */
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 20px; animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* Modal Content */
.modal-content { background: #111; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; max-width: 600px; width: 100%; max-height: 90vh; overflow-y: auto; position: relative; animation: slideUp 0.3s ease; }
@keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
.modal-close { position: absolute; top: 15px; right: 15px; width: 35px; height: 35px; background: rgba(255, 255, 255, 0.1); border: none; border-radius: 50%; color: #fff; font-size: 1.5rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; z-index: 10; }
.modal-close:hover { background: rgba(239, 68, 68, 0.3); color: #ef4444; }

/* Modal Header */
.modal-header { padding: 25px 25px 0; text-align: center; }
.modal-header h2 { font-size: 1.5rem; font-weight: 800; margin-bottom: 8px; }
.modal-header p { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }

/* Selected Game Preview */
.selected-game-preview { margin: 20px 25px; padding: 20px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; text-align: center; }
.game-teams { display: flex; align-items: center; justify-content: center; gap: 15px; font-weight: 600; flex-wrap: wrap; }
.preview-logo { width: 40px; height: 40px; object-fit: contain; }
.vs { color: rgba(255, 255, 255, 0.3); font-size: 0.9rem; }
.game-meta { margin-top: 10px; display: flex; justify-content: center; gap: 15px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.5); }
.live-badge { background: rgba(255, 68, 68, 0.2); color: #ff6b6b; padding: 3px 10px; border-radius: 15px; font-weight: 600; }

/* Odds Categories */
.odds-categories { padding: 0 25px 20px; display: flex; flex-direction: column; gap: 20px; }
.odds-category h4 { font-size: 0.9rem; font-weight: 600; color: rgba(255, 255, 255, 0.7); margin-bottom: 10px; }
.odds-buttons { display: flex; flex-wrap: wrap; gap: 8px; }
.odd-btn { display: flex; align-items: center; gap: 8px; padding: 10px 15px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: rgba(255, 255, 255, 0.7); cursor: pointer; transition: all 0.3s; font-size: 0.85rem; }
.odd-btn:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); }
.odd-btn.selected { background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2)); border-color: rgba(139, 92, 246, 0.5); color: #a78bfa; }
.odd-icon { font-size: 1.1rem; }
.odd-label { font-weight: 500; }

/* Selected Odds Values */
.selected-odds-values { padding: 0 25px 20px; }
.selected-odds-values h4 { font-size: 0.9rem; font-weight: 600; color: rgba(255, 255, 255, 0.7); margin-bottom: 15px; }
.odds-inputs { display: flex; flex-direction: column; gap: 10px; }
.odd-input-row { display: flex; align-items: center; justify-content: space-between; gap: 15px; padding: 12px 15px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; }
.odd-input-label { flex: 1; font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); }
.odd-input { width: 100px; padding: 10px 15px; background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; color: #fff; font-size: 1rem; font-weight: 600; text-align: center; }
.odd-input:focus { outline: none; border-color: #a78bfa; }
.odd-input::placeholder { color: rgba(255, 255, 255, 0.3); }

/* Modal Footer */
.modal-footer { padding: 20px 25px 25px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.odds-summary { text-align: center; margin-bottom: 15px; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }
.modal-actions { display: flex; gap: 10px; }
.btn-cancel { flex: 1; padding: 15px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: rgba(255, 255, 255, 0.6); font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-cancel:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
.btn-save { flex: 2; padding: 15px; background: linear-gradient(135deg, #8b5cf6, #3b82f6); border: none; border-radius: 10px; color: #fff; font-weight: 700; cursor: pointer; transition: all 0.3s; }
.btn-save:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

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
  .auto-update-bar { justify-content: center; }
  
  /* Modal Mobile */
  .modal-content { max-height: 85vh; margin: auto 10px; }
  .odds-buttons { justify-content: center; }
  .odd-btn { padding: 8px 12px; font-size: 0.8rem; }
  .odd-input-row { flex-direction: column; align-items: stretch; gap: 8px; }
  .odd-input { width: 100%; }
  .modal-actions { flex-direction: column; }
  .active-bets-grid { grid-template-columns: 1fr; }
  .game-teams { font-size: 0.9rem; }
}
</style>
