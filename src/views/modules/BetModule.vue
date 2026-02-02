<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans } from '../../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const loading = ref(true)
const jogoSelecionado = ref(null)
const erro = ref(null)

// API-Football Config (RapidAPI)
const API_KEY = '3e22b287c91d57f0f583c6ea5dbb4f37'
const API_HOST = 'v3.football.api-sports.io'

// Ligas
const LIGAS_CONFIG = {
  brasileirao: { id: 71, nome: 'Brasileirão Série A', pais: '🇧🇷', season: 2025 },
  libertadores: { id: 13, nome: 'Libertadores', pais: '🏆', season: 2025 },
  premier: { id: 39, nome: 'Premier League', pais: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', season: 2025 },
  laliga: { id: 140, nome: 'La Liga', pais: '🇪🇸', season: 2025 }
}

const jogos = ref([])
const ligaSelecionada = ref('brasileirao')
const apiStatus = ref({ requests: 0, limit: 100 })

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  await carregarJogos()
})

watch(ligaSelecionada, () => carregarJogos())

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

// Buscar jogos da API-Football - SEM FALLBACK
const carregarJogos = async () => {
  loading.value = true
  erro.value = null
  jogos.value = []
  
  const liga = LIGAS_CONFIG[ligaSelecionada.value]
  const today = new Date().toISOString().split('T')[0]
  const endDate = getDatePlusDays(30)
  
  try {
    // Buscar fixtures (jogos)
    const response = await fetch(
      `https://${API_HOST}/fixtures?league=${liga.id}&season=${liga.season}&from=${today}&to=${endDate}`,
      {
        method: 'GET',
        headers: {
          'x-apisports-key': API_KEY,
          'x-apisports-host': API_HOST
        }
      }
    )
    
    if (!response.ok) {
      throw new Error(`Erro HTTP: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Verificar erros da API
    if (data.errors && Object.keys(data.errors).length > 0) {
      const errorMsg = Object.values(data.errors).join(', ')
      throw new Error(`API Error: ${errorMsg}`)
    }
    
    // Guardar status da API
    if (data.response) {
      apiStatus.value = {
        requests: data.response.length,
        remaining: data.response.length
      }
    }
    
    if (!data.response || data.response.length === 0) {
      throw new Error('Nenhum jogo encontrado para esta liga nos próximos 30 dias')
    }
    
    // Processar jogos
    const jogosProcessados = []
    
    for (const fixture of data.response.slice(0, 15)) {
      // Buscar odds para cada jogo
      const odds = await buscarOdds(fixture.fixture.id)
      const analise = calcularAnalise(odds, fixture)
      
      jogosProcessados.push({
        id: fixture.fixture.id,
        casa: fixture.teams.home.name,
        casaLogo: fixture.teams.home.logo,
        fora: fixture.teams.away.name,
        foraLogo: fixture.teams.away.logo,
        data: formatarData(fixture.fixture.date),
        hora: formatarHora(fixture.fixture.date),
        estadio: fixture.fixture.venue?.name || 'A definir',
        cidade: fixture.fixture.venue?.city || '',
        status: fixture.fixture.status.short,
        liga: fixture.league.name,
        ligaLogo: fixture.league.logo,
        rodada: fixture.league.round,
        ...analise
      })
    }
    
    jogos.value = jogosProcessados
    
  } catch (error) {
    console.error('Erro ao carregar jogos:', error)
    erro.value = error.message
  } finally {
    loading.value = false
  }
}

// Buscar odds reais
const buscarOdds = async (fixtureId) => {
  try {
    const response = await fetch(
      `https://${API_HOST}/odds?fixture=${fixtureId}`,
      {
        method: 'GET',
        headers: {
          'x-apisports-key': API_KEY,
          'x-apisports-host': API_HOST
        }
      }
    )
    
    if (!response.ok) return null
    
    const data = await response.json()
    
    if (data.response && data.response.length > 0 && data.response[0].bookmakers) {
      const bookmaker = data.response[0].bookmakers[0]
      const bets = bookmaker?.bets || []
      
      return {
        bookmaker: bookmaker?.name || 'N/A',
        matchWinner: bets.find(b => b.name === 'Match Winner')?.values || null,
        overUnder: bets.find(b => b.name === 'Goals Over/Under')?.values || null,
        btts: bets.find(b => b.name === 'Both Teams Score')?.values || null,
        doubleChance: bets.find(b => b.name === 'Double Chance')?.values || null
      }
    }
    
    return null
  } catch (error) {
    console.error('Erro ao buscar odds:', error)
    return null
  }
}

// Calcular análise baseada nas odds
const calcularAnalise = (odds, fixture) => {
  let oddCasa = 0, oddEmpate = 0, oddFora = 0
  let oddOver25 = 0, oddUnder25 = 0
  let oddBTTSYes = 0, oddBTTSNo = 0
  let bookmaker = 'Sem odds disponíveis'
  let hasOdds = false
  
  if (odds?.matchWinner) {
    hasOdds = true
    bookmaker = odds.bookmaker
    
    const home = odds.matchWinner.find(v => v.value === 'Home')
    const draw = odds.matchWinner.find(v => v.value === 'Draw')
    const away = odds.matchWinner.find(v => v.value === 'Away')
    
    if (home) oddCasa = parseFloat(home.odd)
    if (draw) oddEmpate = parseFloat(draw.odd)
    if (away) oddFora = parseFloat(away.odd)
  }
  
  if (odds?.overUnder) {
    const over = odds.overUnder.find(v => v.value === 'Over 2.5')
    const under = odds.overUnder.find(v => v.value === 'Under 2.5')
    
    if (over) oddOver25 = parseFloat(over.odd)
    if (under) oddUnder25 = parseFloat(under.odd)
  }
  
  if (odds?.btts) {
    const yes = odds.btts.find(v => v.value === 'Yes')
    const no = odds.btts.find(v => v.value === 'No')
    
    if (yes) oddBTTSYes = parseFloat(yes.odd)
    if (no) oddBTTSNo = parseFloat(no.odd)
  }
  
  // Calcular probabilidades das odds
  let probCasa = 0, probEmpate = 0, probFora = 0
  let probOver25 = 0, probUnder25 = 0, probBTTS = 0
  
  if (oddCasa > 0 && oddEmpate > 0 && oddFora > 0) {
    const totalInv = (1/oddCasa) + (1/oddEmpate) + (1/oddFora)
    probCasa = Math.round((1/oddCasa) / totalInv * 100)
    probEmpate = Math.round((1/oddEmpate) / totalInv * 100)
    probFora = 100 - probCasa - probEmpate
  }
  
  if (oddOver25 > 0) probOver25 = Math.round((1/oddOver25) * 100)
  if (oddUnder25 > 0) probUnder25 = Math.round((1/oddUnder25) * 100)
  if (oddBTTSYes > 0) probBTTS = Math.round((1/oddBTTSYes) * 100)
  
  // xG estimado
  const xgTotal = oddOver25 > 0 ? (oddOver25 < 1.7 ? 3.2 : oddOver25 < 2.0 ? 2.7 : 2.3) : 2.5
  const xgCasa = probCasa > 0 ? (xgTotal * (probCasa / 100) * 1.3).toFixed(2) : '1.3'
  const xgFora = probFora > 0 ? (xgTotal * (probFora / 100) * 1.1).toFixed(2) : '1.1'
  
  // Melhor aposta
  let melhorAposta = 'Aguardando odds'
  let confianca = 0
  
  if (hasOdds) {
    if (probCasa >= 55) {
      melhorAposta = `Vitória ${fixture.teams.home.name}`
      confianca = probCasa
    } else if (probFora >= 50) {
      melhorAposta = `Vitória ${fixture.teams.away.name}`
      confianca = probFora
    } else if (probOver25 >= 55) {
      melhorAposta = 'Over 2.5 Gols'
      confianca = probOver25
    } else if (probUnder25 >= 60) {
      melhorAposta = 'Under 2.5 Gols'
      confianca = probUnder25
    } else if (probBTTS >= 55) {
      melhorAposta = 'Ambas Marcam'
      confianca = probBTTS
    } else {
      melhorAposta = 'Dupla Chance 1X'
      confianca = probCasa + probEmpate
    }
  }
  
  return {
    oddCasa: oddCasa || '-',
    oddEmpate: oddEmpate || '-',
    oddFora: oddFora || '-',
    oddOver25: oddOver25 || '-',
    oddUnder25: oddUnder25 || '-',
    oddBTTSYes: oddBTTSYes || '-',
    oddBTTSNo: oddBTTSNo || '-',
    probCasa,
    probEmpate,
    probFora,
    probOver25,
    probUnder25,
    probBTTS,
    xgCasa: parseFloat(xgCasa),
    xgFora: parseFloat(xgFora),
    melhorAposta,
    confianca: Math.min(85, Math.round(confianca)),
    bookmaker,
    hasOdds
  }
}

const getDatePlusDays = (days) => {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().split('T')[0]
}

const formatarData = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

const formatarHora = (dateStr) => {
  return new Date(dateStr).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

const selecionarJogo = (jogo) => { jogoSelecionado.value = jogo }
const fecharModal = () => { jogoSelecionado.value = null }
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
        <router-link to="/bet" class="nav-item active"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>BET</router-link>
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
        <button @click="navigateTo('/bet')" class="mobile-nav-item active">BET</button>
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
          <h1>Módulo BET</h1>
          <p>Dados reais via API-Football • Odds de casas de apostas</p>
        </div>
        <div class="header-right">
          <div class="liga-selector">
            <select v-model="ligaSelecionada">
              <option value="brasileirao">🇧🇷 Brasileirão Série A</option>
              <option value="libertadores">🏆 Libertadores</option>
              <option value="premier">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League</option>
              <option value="laliga">🇪🇸 La Liga</option>
            </select>
          </div>
          <button @click="carregarJogos" class="btn-refresh" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: loading }"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          </button>
        </div>
      </header>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Buscando jogos e odds na API-Football...</p>
      </div>

      <!-- Erro -->
      <div v-else-if="erro" class="erro-state">
        <div class="erro-icon">⚠️</div>
        <h2>Erro ao carregar dados</h2>
        <p>{{ erro }}</p>
        <button @click="carregarJogos" class="btn-retry">Tentar novamente</button>
      </div>

      <!-- Conteúdo -->
      <div v-else class="bet-content">
        <div class="api-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <span>{{ jogos.length }} jogos encontrados • Dados em tempo real via <strong>API-Football</strong></span>
        </div>
        
        <div class="disclaimer-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <p><strong>Aviso:</strong> Odds reais de casas de apostas. Apostas envolvem riscos. Aposte com responsabilidade.</p>
        </div>

        <div class="jogos-grid">
          <div v-for="jogo in jogos" :key="jogo.id" class="jogo-card" @click="selecionarJogo(jogo)">
            <div class="jogo-header">
              <div class="jogo-info">
                <span class="jogo-data">{{ jogo.data }} • {{ jogo.hora }}</span>
                <span class="jogo-local">{{ jogo.estadio }}</span>
              </div>
              <span class="confianca-badge" :class="{ alta: jogo.confianca >= 60, media: jogo.confianca >= 45 && jogo.confianca < 60, sem: !jogo.hasOdds }">
                {{ jogo.hasOdds ? jogo.confianca + '%' : 'Sem odds' }}
              </span>
            </div>
            
            <div class="jogo-times">
              <div class="time">
                <img :src="jogo.casaLogo" @error="$event.target.src = '/icone.webp'" alt="">
                <span class="time-nome">{{ jogo.casa }}</span>
                <span class="time-odd" v-if="jogo.hasOdds">@{{ jogo.oddCasa }}</span>
              </div>
              <div class="versus">
                <span class="vs">VS</span>
                <span class="xg" v-if="jogo.hasOdds">{{ jogo.xgCasa }} - {{ jogo.xgFora }}</span>
              </div>
              <div class="time">
                <img :src="jogo.foraLogo" @error="$event.target.src = '/icone.webp'" alt="">
                <span class="time-nome">{{ jogo.fora }}</span>
                <span class="time-odd" v-if="jogo.hasOdds">@{{ jogo.oddFora }}</span>
              </div>
            </div>
            
            <div class="probabilidades-bar" v-if="jogo.hasOdds">
              <div class="prob casa" :style="{ width: jogo.probCasa + '%' }">{{ jogo.probCasa }}%</div>
              <div class="prob empate" :style="{ width: jogo.probEmpate + '%' }">{{ jogo.probEmpate }}%</div>
              <div class="prob fora" :style="{ width: jogo.probFora + '%' }">{{ jogo.probFora }}%</div>
            </div>
            <div class="no-odds-bar" v-else>
              <span>Odds não disponíveis ainda</span>
            </div>
            
            <div class="jogo-footer">
              <div class="melhor-aposta" v-if="jogo.hasOdds">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                {{ jogo.melhorAposta }}
              </div>
              <span class="bookmaker-tag" v-if="jogo.hasOdds">{{ jogo.bookmaker }}</span>
              <button class="btn-analisar">{{ jogo.hasOdds ? 'Ver Análise' : 'Ver Jogo' }}</button>
            </div>
          </div>
        </div>

        <div v-if="jogos.length === 0" class="no-games">
          <p>Nenhum jogo encontrado para esta liga.</p>
        </div>
      </div>

      <!-- Modal -->
      <div v-if="jogoSelecionado" class="modal-overlay" @click.self="fecharModal">
        <div class="modal-analise">
          <button class="modal-close" @click="fecharModal">×</button>
          
          <div class="modal-header-jogo">
            <div class="time-modal">
              <img :src="jogoSelecionado.casaLogo" @error="$event.target.src = '/icone.webp'">
              <h3>{{ jogoSelecionado.casa }}</h3>
            </div>
            <div class="vs-modal">
              <img :src="jogoSelecionado.ligaLogo" class="liga-logo" @error="$event.target.style.display='none'">
              <span class="data-modal">{{ jogoSelecionado.data }}</span>
              <span class="hora-modal">{{ jogoSelecionado.hora }}</span>
              <span class="rodada-modal">{{ jogoSelecionado.rodada }}</span>
            </div>
            <div class="time-modal">
              <img :src="jogoSelecionado.foraLogo" @error="$event.target.src = '/icone.webp'">
              <h3>{{ jogoSelecionado.fora }}</h3>
            </div>
          </div>

          <div class="estadio-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {{ jogoSelecionado.estadio }} {{ jogoSelecionado.cidade ? '• ' + jogoSelecionado.cidade : '' }}
          </div>
          
          <template v-if="jogoSelecionado.hasOdds">
            <div class="analise-secao">
              <h4>Resultado Final</h4>
              <div class="odds-grid">
                <div class="odd-card">
                  <span class="odd-label">{{ jogoSelecionado.casa }}</span>
                  <span class="odd-value">@{{ jogoSelecionado.oddCasa }}</span>
                  <span class="odd-prob">{{ jogoSelecionado.probCasa }}%</span>
                </div>
                <div class="odd-card">
                  <span class="odd-label">Empate</span>
                  <span class="odd-value">@{{ jogoSelecionado.oddEmpate }}</span>
                  <span class="odd-prob">{{ jogoSelecionado.probEmpate }}%</span>
                </div>
                <div class="odd-card">
                  <span class="odd-label">{{ jogoSelecionado.fora }}</span>
                  <span class="odd-value">@{{ jogoSelecionado.oddFora }}</span>
                  <span class="odd-prob">{{ jogoSelecionado.probFora }}%</span>
                </div>
              </div>
            </div>
            
            <div class="analise-secao">
              <h4>Gols Esperados (xG)</h4>
              <div class="xg-visual">
                <div class="xg-time">
                  <span class="xg-nome">{{ jogoSelecionado.casa }}</span>
                  <div class="xg-bar"><div class="xg-fill" :style="{ width: (jogoSelecionado.xgCasa / 3 * 100) + '%' }"></div></div>
                  <span class="xg-valor">{{ jogoSelecionado.xgCasa }}</span>
                </div>
                <div class="xg-time">
                  <span class="xg-nome">{{ jogoSelecionado.fora }}</span>
                  <div class="xg-bar"><div class="xg-fill fora" :style="{ width: (jogoSelecionado.xgFora / 3 * 100) + '%' }"></div></div>
                  <span class="xg-valor">{{ jogoSelecionado.xgFora }}</span>
                </div>
              </div>
            </div>
            
            <div class="analise-secao">
              <h4>Mercados Alternativos</h4>
              <div class="mercados-grid">
                <div class="mercado-card" v-if="jogoSelecionado.oddOver25 !== '-'">
                  <span class="mercado-nome">Over 2.5</span>
                  <span class="mercado-odd">@{{ jogoSelecionado.oddOver25 }}</span>
                  <span class="mercado-prob" :class="{ verde: jogoSelecionado.probOver25 >= 55 }">{{ jogoSelecionado.probOver25 }}%</span>
                </div>
                <div class="mercado-card" v-if="jogoSelecionado.oddUnder25 !== '-'">
                  <span class="mercado-nome">Under 2.5</span>
                  <span class="mercado-odd">@{{ jogoSelecionado.oddUnder25 }}</span>
                  <span class="mercado-prob" :class="{ verde: jogoSelecionado.probUnder25 >= 55 }">{{ jogoSelecionado.probUnder25 }}%</span>
                </div>
                <div class="mercado-card" v-if="jogoSelecionado.oddBTTSYes !== '-'">
                  <span class="mercado-nome">Ambas Marcam</span>
                  <span class="mercado-odd">@{{ jogoSelecionado.oddBTTSYes }}</span>
                  <span class="mercado-prob" :class="{ verde: jogoSelecionado.probBTTS >= 55 }">{{ jogoSelecionado.probBTTS }}%</span>
                </div>
                <div class="mercado-card" v-if="jogoSelecionado.oddBTTSNo !== '-'">
                  <span class="mercado-nome">Não Ambas</span>
                  <span class="mercado-odd">@{{ jogoSelecionado.oddBTTSNo }}</span>
                  <span class="mercado-prob" :class="{ verde: (100 - jogoSelecionado.probBTTS) >= 55 }">{{ 100 - jogoSelecionado.probBTTS }}%</span>
                </div>
              </div>
            </div>
            
            <div class="recomendacao-box">
              <div class="recomendacao-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                <span>Recomendação IA</span>
              </div>
              <p class="recomendacao-texto">{{ jogoSelecionado.melhorAposta }}</p>
              <div class="confianca-meter"><div class="meter-fill" :style="{ width: jogoSelecionado.confianca + '%' }"></div></div>
              <span class="confianca-label">{{ jogoSelecionado.confianca }}% de confiança • Fonte: {{ jogoSelecionado.bookmaker }}</span>
            </div>
          </template>
          
          <div v-else class="no-odds-modal">
            <div class="no-odds-icon">📊</div>
            <h3>Odds ainda não disponíveis</h3>
            <p>As casas de apostas ainda não publicaram as odds para este jogo. Volte mais próximo da data.</p>
          </div>
        </div>
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
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; gap: 20px; }
.header-left h1 { font-size: 2rem; font-weight: 800; margin-bottom: 8px; }
.header-left p { color: rgba(255, 255, 255, 0.5); }
.header-right { display: flex; gap: 10px; align-items: center; }
.liga-selector select { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 12px 20px; color: #fff; font-size: 1rem; cursor: pointer; }
.liga-selector select option { background: #111; }
.btn-refresh { width: 48px; height: 48px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
.btn-refresh:hover { background: rgba(255, 255, 255, 0.2); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-refresh svg { width: 22px; height: 22px; stroke: #fff; }
.btn-refresh svg.spinning { animation: spin 1s linear infinite; }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 100px 20px; }
.spinner { width: 50px; height: 50px; border: 3px solid rgba(255, 255, 255, 0.1); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-state p { margin-top: 20px; color: rgba(255, 255, 255, 0.5); }

.erro-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 20px; text-align: center; }
.erro-icon { font-size: 4rem; margin-bottom: 20px; }
.erro-state h2 { font-size: 1.5rem; margin-bottom: 10px; }
.erro-state p { color: rgba(255, 255, 255, 0.6); margin-bottom: 30px; max-width: 500px; }
.btn-retry { background: #fff; color: #000; border: none; padding: 15px 40px; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-retry:hover { transform: scale(1.05); }

.api-badge { display: flex; align-items: center; gap: 10px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 12px 20px; margin-bottom: 15px; }
.api-badge svg { width: 20px; height: 20px; stroke: #22c55e; }
.api-badge span { font-size: 0.85rem; color: rgba(255, 255, 255, 0.8); }

.disclaimer-box { display: flex; align-items: center; gap: 15px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; }
.disclaimer-box svg { width: 24px; height: 24px; stroke: #fbbf24; flex-shrink: 0; }
.disclaimer-box p { font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); }

.no-games { text-align: center; padding: 60px 20px; color: rgba(255, 255, 255, 0.5); }

.jogos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; }
.jogo-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.3s; }
.jogo-card:hover { transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.05); }
.jogo-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.jogo-info { display: flex; flex-direction: column; gap: 3px; }
.jogo-data { font-size: 0.85rem; color: rgba(255, 255, 255, 0.7); }
.jogo-local { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }
.confianca-badge { background: rgba(255, 255, 255, 0.1); padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.confianca-badge.alta { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.confianca-badge.media { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.confianca-badge.sem { background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.4); }
.jogo-times { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.time { display: flex; flex-direction: column; align-items: center; gap: 8px; flex: 1; }
.time img { width: 50px; height: 50px; object-fit: contain; }
.time-nome { font-weight: 600; font-size: 0.95rem; text-align: center; }
.time-odd { font-size: 0.8rem; color: #3b82f6; background: rgba(59, 130, 246, 0.1); padding: 3px 10px; border-radius: 10px; font-weight: 600; }
.versus { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.vs { font-size: 0.8rem; color: rgba(255, 255, 255, 0.3); }
.xg { font-size: 1.2rem; font-weight: 700; color: rgba(255, 255, 255, 0.6); }
.probabilidades-bar { display: flex; height: 30px; border-radius: 8px; overflow: hidden; margin-bottom: 15px; }
.prob { display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 600; min-width: 40px; }
.prob.casa { background: #22c55e; color: #000; }
.prob.empate { background: #6b7280; color: #fff; }
.prob.fora { background: #3b82f6; color: #fff; }
.no-odds-bar { display: flex; align-items: center; justify-content: center; height: 30px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-bottom: 15px; }
.no-odds-bar span { font-size: 0.8rem; color: rgba(255, 255, 255, 0.4); }
.jogo-footer { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.melhor-aposta { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7); }
.melhor-aposta svg { width: 16px; height: 16px; stroke: #22c55e; }
.bookmaker-tag { font-size: 0.7rem; color: rgba(255, 255, 255, 0.4); background: rgba(255, 255, 255, 0.05); padding: 4px 10px; border-radius: 6px; }
.btn-analisar { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 8px 16px; color: #fff; font-size: 0.85rem; cursor: pointer; transition: all 0.3s; }
.btn-analisar:hover { background: #fff; color: #000; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-analise { background: #111; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; width: 100%; max-width: 650px; max-height: 90vh; overflow-y: auto; padding: 30px; position: relative; }
.modal-close { position: absolute; top: 15px; right: 15px; width: 40px; height: 40px; background: rgba(255, 255, 255, 0.1); border: none; border-radius: 50%; color: #fff; font-size: 1.5rem; cursor: pointer; transition: all 0.3s; }
.modal-close:hover { background: #ef4444; }
.modal-header-jogo { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.time-modal { display: flex; flex-direction: column; align-items: center; gap: 10px; flex: 1; }
.time-modal img { width: 65px; height: 65px; object-fit: contain; }
.time-modal h3 { font-size: 1.1rem; text-align: center; }
.vs-modal { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.liga-logo { width: 40px; height: 40px; object-fit: contain; margin-bottom: 5px; }
.data-modal { font-size: 0.85rem; color: rgba(255, 255, 255, 0.5); }
.hora-modal { font-size: 1.3rem; font-weight: 700; }
.rodada-modal { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }
.estadio-info { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; margin-bottom: 25px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); }
.estadio-info svg { width: 16px; height: 16px; }
.analise-secao { margin-bottom: 25px; }
.analise-secao h4 { font-size: 0.9rem; color: rgba(255, 255, 255, 0.5); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
.odds-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.odd-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; text-align: center; }
.odd-label { display: block; font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 8px; }
.odd-value { display: block; font-size: 1.3rem; font-weight: 700; margin-bottom: 5px; color: #3b82f6; }
.odd-prob { font-size: 0.8rem; color: #22c55e; }
.xg-visual { display: flex; flex-direction: column; gap: 15px; }
.xg-time { display: flex; align-items: center; gap: 15px; }
.xg-nome { width: 100px; font-size: 0.9rem; }
.xg-bar { flex: 1; height: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 6px; overflow: hidden; }
.xg-fill { height: 100%; background: linear-gradient(90deg, #22c55e, #4ade80); border-radius: 6px; transition: width 0.5s; }
.xg-fill.fora { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.xg-valor { width: 40px; text-align: right; font-weight: 600; }
.mercados-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.mercado-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
.mercado-nome { font-size: 0.9rem; }
.mercado-odd { font-size: 0.85rem; color: #3b82f6; }
.mercado-prob { font-weight: 700; }
.mercado-prob.verde { color: #22c55e; }
.recomendacao-box { background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05)); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 16px; padding: 25px; text-align: center; }
.recomendacao-header { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 15px; }
.recomendacao-header svg { width: 24px; height: 24px; stroke: #22c55e; }
.recomendacao-header span { font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; }
.recomendacao-texto { font-size: 1.4rem; font-weight: 700; margin-bottom: 20px; }
.confianca-meter { height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
.meter-fill { height: 100%; background: linear-gradient(90deg, #22c55e, #4ade80); border-radius: 4px; transition: width 0.5s; }
.confianca-label { font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); }

.no-odds-modal { text-align: center; padding: 40px 20px; }
.no-odds-icon { font-size: 4rem; margin-bottom: 20px; }
.no-odds-modal h3 { font-size: 1.3rem; margin-bottom: 10px; }
.no-odds-modal p { color: rgba(255, 255, 255, 0.6); }

@media (max-width: 968px) {
  .sidebar { display: none; }
  .mobile-menu-btn { display: flex; }
  .mobile-overlay { display: block; }
  .mobile-menu { display: block; }
  .main-content { margin-left: 0; padding: 20px; padding-bottom: 100px; }
  .jogos-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .header-right { width: 100%; }
  .liga-selector { flex: 1; }
  .liga-selector select { width: 100%; }
}

@media (max-width: 480px) {
  .jogo-times { flex-direction: column; gap: 15px; }
  .time img { width: 40px; height: 40px; }
  .odds-grid { grid-template-columns: 1fr; }
  .mercados-grid { grid-template-columns: 1fr; }
  .modal-header-jogo { flex-direction: column; gap: 20px; }
}
</style>
