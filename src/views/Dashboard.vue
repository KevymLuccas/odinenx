<script setup>
import { ref, onMounted, onUnmounted, computed, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, createCustomerPortal, cancelSubscription, plans, getTrialStatus, isAdmin as checkIsAdmin } from '../lib/stripe'
import ViewerCounter from '../components/ViewerCounter.vue'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const route = useRoute()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const showCancelModal = ref(false)
const canceling = ref(false)
const trialStatus = ref(null)
const userIsAdmin = ref(false)

// 📷 Sistema de Foto de Perfil
const userAvatar = ref(null)
const showAvatarModal = ref(false)
const uploadingAvatar = ref(false)
const avatarInput = ref(null)

// 🎯 Sistema de Foco/Preferência
const userFocus = ref('all') // 'all', 'bet', 'trade', 'cartola'
const showFocusSelector = ref(false)

// 📡 Feed em tempo real
const liveFeed = ref([])
const feedLoading = ref(false)
const feedInterval = ref(null)

// 📊 Estatísticas do Dashboard
const userStats = ref({
  analysesToday: 0,
  winRate: 0,
  opportunities: 0,
  totalWins: 0,
  totalLosses: 0
})
const recentAnalyses = ref([])
const liveGamesCount = ref(0)

// Dados em tempo real
const marketData = ref({
  crypto: null,
  forex: null,
  stocks: null
})
const cartolaData = ref({
  marketStatus: null,
  lastRound: null,
  highlights: []
})

// Toast function from App.vue
const showToast = inject('showToast', () => {})

// 📊 Carregar estatísticas do usuário
async function loadUserStats(userId) {
  try {
    // Buscar stats do usuário
    const { data: stats } = await supabase
      .from('user_stats')
      .select('*')
      .eq('user_id', userId)
      .single()
    
    if (stats) {
      const total = stats.wins + stats.losses
      userStats.value = {
        analysesToday: stats.analyses_today || 0,
        winRate: total > 0 ? Math.round((stats.wins / total) * 100) : 0,
        opportunities: stats.current_streak || 0,
        totalWins: stats.wins || 0,
        totalLosses: stats.losses || 0
      }
    }
  } catch (err) {
    console.log('Stats não disponíveis ainda:', err.message)
  }
}

// 📋 Carregar análises recentes
async function loadRecentAnalyses(userId) {
  try {
    const { data } = await supabase
      .from('analysis_history')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(5)
    
    if (data) recentAnalyses.value = data
  } catch (err) {
    console.log('Histórico não disponível:', err.message)
  }
}

// 🔴 Buscar contagem de jogos ao vivo
async function loadLiveGamesCount() {
  try {
    const response = await fetch('/api/live-games')
    const data = await response.json()
    if (data.live_count) liveGamesCount.value = data.live_count
  } catch (err) {
    console.log('Live games não disponível')
  }
}

// 📷 Upload de foto de perfil
async function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  if (file.size > 2 * 1024 * 1024) {
    showToast('error', 'Erro', 'A imagem deve ter no máximo 2MB')
    return
  }
  
  uploadingAvatar.value = true
  
  try {
    // Upload para Supabase Storage
    const fileExt = file.name.split('.').pop()
    const fileName = `${user.value.id}_${Date.now()}.${fileExt}`
    
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('avatars')
      .upload(fileName, file, { upsert: true })
    
    if (uploadError) throw uploadError
    
    // Obter URL pública
    const { data: { publicUrl } } = supabase.storage
      .from('avatars')
      .getPublicUrl(fileName)
    
    // Atualizar perfil do usuário
    const { error: updateError } = await supabase
      .from('profiles')
      .upsert({ 
        id: user.value.id, 
        avatar_url: publicUrl,
        updated_at: new Date().toISOString()
      })
    
    if (updateError) throw updateError
    
    userAvatar.value = publicUrl
    showAvatarModal.value = false
    showToast('success', 'Foto atualizada!', 'Sua foto de perfil foi alterada.')
  } catch (err) {
    console.error('Erro ao fazer upload:', err)
    showToast('error', 'Erro', 'Não foi possível atualizar a foto.')
  } finally {
    uploadingAvatar.value = false
  }
}

// 📷 Carregar avatar do usuário
async function loadUserAvatar(userId) {
  try {
    const { data } = await supabase
      .from('profiles')
      .select('avatar_url, focus_preference')
      .eq('id', userId)
      .single()
    
    if (data) {
      userAvatar.value = data.avatar_url
      userFocus.value = data.focus_preference || 'all'
    }
  } catch (err) {
    console.log('Avatar não disponível')
  }
}

// 🎯 Salvar foco do usuário
async function saveFocusPreference(focus) {
  userFocus.value = focus
  showFocusSelector.value = false
  
  try {
    await supabase
      .from('profiles')
      .upsert({ 
        id: user.value.id, 
        focus_preference: focus,
        updated_at: new Date().toISOString()
      })
    
    showToast('success', 'Preferência salva!', `Seu foco agora é: ${getFocusLabel(focus)}`)
    
    // Recarregar feed com novo foco
    loadLiveFeed()
  } catch (err) {
    console.error('Erro ao salvar foco:', err)
  }
}

// 🎯 Labels do foco
function getFocusLabel(focus) {
  const labels = {
    all: '📊 Todas as áreas',
    bet: '⚽ Apostas Esportivas',
    trade: '📈 Day Trade',
    cartola: '🏆 Cartola FC'
  }
  return labels[focus] || labels.all
}

// 📡 Carregar feed em tempo real baseado no foco
async function loadLiveFeed() {
  feedLoading.value = true
  liveFeed.value = []
  
  try {
    const focus = userFocus.value
    
    if (focus === 'all' || focus === 'bet') {
      await loadBetFeed()
    }
    
    if (focus === 'all' || focus === 'trade') {
      await loadTradeFeed()
    }
    
    if (focus === 'all' || focus === 'cartola') {
      await loadCartolaFeed()
    }
    
    // Ordenar por timestamp
    liveFeed.value.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    
  } catch (err) {
    console.error('Erro ao carregar feed:', err)
  } finally {
    feedLoading.value = false
  }
}

// 📡 Feed de Apostas
async function loadBetFeed() {
  try {
    const response = await fetch('/api/live-games')
    const data = await response.json()
    
    if (data.games?.length > 0) {
      // Adicionar jogos ao vivo no feed
      const liveGames = data.games.slice(0, 3)
      liveGames.forEach(game => {
        liveFeed.value.push({
          type: 'bet',
          icon: '⚽',
          title: `${game.home_team} x ${game.away_team}`,
          subtitle: `${game.home_score || 0} - ${game.away_score || 0} • ${game.minute}'`,
          status: '🔴 AO VIVO',
          timestamp: new Date().toISOString(),
          action: () => router.push('/live')
        })
      })
    }
    
    // Adicionar notícia genérica
    liveFeed.value.push({
      type: 'bet',
      icon: '📊',
      title: 'Análise do dia disponível',
      subtitle: `${liveGamesCount.value || 0} jogos para analisar hoje`,
      status: 'Novo',
      timestamp: new Date().toISOString(),
      action: () => router.push('/bet')
    })
  } catch (err) {
    console.log('Erro ao carregar feed BET')
  }
}

// 📡 Feed de Trade
async function loadTradeFeed() {
  try {
    // Buscar dados de mercado
    const [cryptoRes, forexRes] = await Promise.all([
      fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true').catch(() => null),
      fetch('https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL').catch(() => null)
    ])
    
    if (cryptoRes?.ok) {
      const crypto = await cryptoRes.json()
      
      if (crypto.bitcoin) {
        const btcChange = crypto.bitcoin.usd_24h_change?.toFixed(2) || 0
        liveFeed.value.push({
          type: 'trade',
          icon: '₿',
          title: 'Bitcoin (BTC)',
          subtitle: `$${crypto.bitcoin.usd?.toLocaleString('en-US')} • ${btcChange > 0 ? '📈' : '📉'} ${btcChange}%`,
          status: btcChange > 0 ? '🟢 Alta' : '🔴 Baixa',
          timestamp: new Date().toISOString(),
          action: () => router.push('/trade')
        })
      }
      
      if (crypto.ethereum) {
        const ethChange = crypto.ethereum.usd_24h_change?.toFixed(2) || 0
        liveFeed.value.push({
          type: 'trade',
          icon: 'Ξ',
          title: 'Ethereum (ETH)',
          subtitle: `$${crypto.ethereum.usd?.toLocaleString('en-US')} • ${ethChange > 0 ? '📈' : '📉'} ${ethChange}%`,
          status: ethChange > 0 ? '🟢 Alta' : '🔴 Baixa',
          timestamp: new Date().toISOString(),
          action: () => router.push('/trade')
        })
      }
    }
    
    if (forexRes?.ok) {
      const forex = await forexRes.json()
      if (forex.USDBRL) {
        liveFeed.value.push({
          type: 'trade',
          icon: '💵',
          title: 'Dólar (USD/BRL)',
          subtitle: `R$ ${parseFloat(forex.USDBRL.bid).toFixed(2)} • Variação: ${forex.USDBRL.pctChange}%`,
          status: parseFloat(forex.USDBRL.pctChange) > 0 ? '🟢 Alta' : '🔴 Baixa',
          timestamp: new Date().toISOString(),
          action: () => router.push('/trade')
        })
      }
    }
  } catch (err) {
    console.log('Erro ao carregar feed TRADE')
  }
}

// 📡 Feed de Cartola
async function loadCartolaFeed() {
  try {
    const [statusRes, partidasRes] = await Promise.all([
      fetch('/api/cartola/status').catch(() => null),
      fetch('/api/cartola/partidas').catch(() => null)
    ])
    
    if (statusRes?.ok) {
      const status = await statusRes.json()
      const isOpen = status.mercado?.status_mercado === 1
      
      liveFeed.value.push({
        type: 'cartola',
        icon: '🏆',
        title: 'Status do Mercado',
        subtitle: isOpen ? 'Mercado aberto para escalações!' : 'Mercado fechado',
        status: isOpen ? '🟢 Aberto' : '🔴 Fechado',
        timestamp: new Date().toISOString(),
        action: () => router.push('/cartola')
      })
      
      if (status.mercado?.rodada_atual) {
        liveFeed.value.push({
          type: 'cartola',
          icon: '📅',
          title: `Rodada ${status.mercado.rodada_atual}`,
          subtitle: 'Rodada atual do Cartola',
          status: 'Em andamento',
          timestamp: new Date().toISOString(),
          action: () => router.push('/cartola')
        })
      }
    }
    
    if (partidasRes?.ok) {
      const partidas = await partidasRes.json()
      const proximasPartidas = partidas.partidas?.slice(0, 2) || []
      
      proximasPartidas.forEach(partida => {
        liveFeed.value.push({
          type: 'cartola',
          icon: '⚽',
          title: `${partida.clube_casa_nome} x ${partida.clube_visitante_nome}`,
          subtitle: partida.aproveitamento_mandante || 'Próxima partida',
          status: 'Cartola',
          timestamp: new Date().toISOString(),
          action: () => router.push('/cartola')
        })
      })
    }
  } catch (err) {
    console.log('Erro ao carregar feed Cartola')
  }
}

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  // Check if user is admin
  userIsAdmin.value = await checkIsAdmin(session.user.id)
  
  // Verificar status do trial para usuários free (ADMIN IGNORA)
  if (!userIsAdmin.value && (!subscription.value?.plan || subscription.value.plan === 'free')) {
    trialStatus.value = await getTrialStatus(session.user.id)
    
    // 🚨 BLOQUEIO EFETIVO: Se trial expirou, redirecionar para página específica
    if (trialStatus.value?.expired) {
      router.push('/trial-expired')
      return
    }
  }
  
  // Show toast for login success
  if (route.query.login === 'success') {
    showToast('welcome', 'Bem-vindo de volta! 👋', 'Bom te ver novamente. Confira os palpites do dia!')
  }
  
  if (route.query.payment === 'success') {
    showToast('payment', 'Pagamento confirmado! 💳', 'Seu plano foi ativado. Acesso completo liberado!')
  }
  
  // 📊 Carregar dados do dashboard
  await Promise.all([
    loadUserStats(session.user.id),
    loadRecentAnalyses(session.user.id),
    loadLiveGamesCount(),
    loadUserAvatar(session.user.id)
  ])
  
  // Carregar feed em tempo real
  await loadLiveFeed()
  
  // Atualizar feed a cada 60 segundos
  feedInterval.value = setInterval(() => {
    loadLiveFeed()
    loadLiveGamesCount()
  }, 60000)
  
  loading.value = false
})

const currentPlan = computed(() => {
  // Admin SEMPRE tem plano Elite (sobrescreve qualquer assinatura)
  if (userIsAdmin.value === true) {
    console.log('🔐 Dashboard: Admin detectado, forçando plano Elite')
    return plans.elite
  }
  const planId = subscription.value?.plan || 'free'
  console.log('📋 Dashboard: Plano do usuário:', planId)
  return plans[planId] || plans.free
})

// Cleanup
onUnmounted(() => {
  if (feedInterval.value) {
    clearInterval(feedInterval.value)
  }
})

const isPaidPlan = computed(() => {
  return currentPlan.value.id !== 'free' || userIsAdmin.value
})

const isCanceledButActive = computed(() => {
  return subscription.value?.cancel_at_period_end === true
})

const isTrialExpired = computed(() => {
  return trialStatus.value?.expired === true
})

const trialDaysRemaining = computed(() => {
  return trialStatus.value?.daysRemaining || 0
})

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}

const openBillingPortal = async () => {
  try {
    await createCustomerPortal()
  } catch (error) {
    console.error('Erro ao abrir portal:', error)
  }
}

const handleCancelSubscription = async () => {
  canceling.value = true
  try {
    await cancelSubscription()
    subscription.value = await getSubscriptionStatus(user.value.id)
    showCancelModal.value = false
  } catch (error) {
    console.error('Erro ao cancelar:', error)
    alert('Erro ao cancelar assinatura. Tente novamente.')
  } finally {
    canceling.value = false
  }
}

const mobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const navigateTo = (path) => {
  router.push(path)
  mobileMenuOpen.value = false
}
</script>

<template>
  <div class="dashboard">
    <!-- Admin Viewer Counter -->
    <ViewerCounter v-if="userIsAdmin" :isAdmin="true" class="admin-viewer-counter" />
    
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/">
          <img src="/logo.webp" alt="ODINENX" class="sidebar-logo" />
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <!-- PRINCIPAL -->
        <div class="nav-category">Principal</div>
        <router-link to="/dashboard" class="nav-item active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          Dashboard
        </router-link>

        <!-- 🔴 AO VIVO v2.0 -->
        <div class="nav-category">Ao Vivo</div>
        <router-link to="/live" class="nav-item live-nav">
          <span class="live-indicator"></span>
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="10 8 16 12 10 16 10 8"/>
          </svg>
          Jogos ao Vivo
        </router-link>

        <!-- MÓDULOS -->
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
          BET
        </router-link>
        <router-link to="/trade" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
            <polyline points="16 7 22 7 22 13"/>
          </svg>
          TRADE
        </router-link>
        <router-link to="/cartola" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2a10 10 0 0 0-7.07 17.07M12 2a10 10 0 0 1 7.07 17.07"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          Cartola FC
        </router-link>

        <!-- ACOMPANHAMENTO -->
        <div class="nav-category">Acompanhamento</div>
        <router-link to="/alerts" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          Alertas
        </router-link>
        <router-link to="/history" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 8v4l3 3"/>
            <circle cx="12" cy="12" r="10"/>
          </svg>
          Histórico
        </router-link>

        <!-- SISTEMA -->
        <div class="nav-category">Sistema</div>
        <router-link to="/settings" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          Configurações
        </router-link>
        
        <!-- ADMIN (só aparece para admins) -->
        <router-link v-if="userIsAdmin" to="/admin" class="nav-item admin-link">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          Painel Admin
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="plan-badge-sidebar">
          {{ currentPlan.name }}
        </div>
        <button @click="logout" class="logout-btn">
          <svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Sair
        </button>
      </div>
    </aside>

    <!-- Mobile Menu Button -->
    <button class="mobile-menu-btn" @click="toggleMobileMenu">
      <svg v-if="!mobileMenuOpen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- Mobile Menu Overlay -->
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>
    
    <!-- Mobile Menu -->
    <nav class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-header">
        <img src="/logo.webp" alt="ODINENX" class="mobile-logo" />
      </div>
      <div class="mobile-nav">
        <button @click="navigateTo('/dashboard')" class="mobile-nav-item active">Dashboard</button>
        <button @click="navigateTo('/live')" class="mobile-nav-item live-mobile">🔴 Ao Vivo</button>
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</button>
        <button @click="navigateTo('/cartola')" class="mobile-nav-item">Cartola FC</button>
        <button @click="navigateTo('/alerts')" class="mobile-nav-item">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item">Configurações</button>
        <button v-if="userIsAdmin" @click="navigateTo('/admin')" class="mobile-nav-item admin-mobile">Painel Admin</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-left">
          <h1>Dashboard</h1>
          <p>Bem-vindo de volta, {{ user?.user_metadata?.name || 'Usuário' }}!</p>
        </div>
        <div class="header-right">
          <div class="user-info">
            <!-- Avatar com upload -->
            <div class="user-avatar-wrapper" @click="showAvatarModal = true">
              <img v-if="userAvatar" :src="userAvatar" alt="Avatar" class="user-avatar-img" />
              <div v-else class="user-avatar">
                {{ (user?.user_metadata?.name || user?.email || 'U')[0].toUpperCase() }}
              </div>
              <span class="avatar-edit-badge">📷</span>
            </div>
            <div class="user-details">
              <span class="user-name">{{ user?.user_metadata?.name || 'Usuário' }}</span>
              <span class="user-email">{{ user?.email }}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Seletor de Foco -->
      <div class="focus-selector-bar">
        <button class="focus-current" @click="showFocusSelector = !showFocusSelector">
          <span class="focus-icon">🎯</span>
          <span class="focus-text">{{ getFocusLabel(userFocus) }}</span>
          <svg class="focus-arrow" :class="{ open: showFocusSelector }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        
        <Transition name="dropdown">
          <div v-if="showFocusSelector" class="focus-dropdown">
            <button 
              v-for="focus in ['all', 'bet', 'trade', 'cartola']" 
              :key="focus"
              @click="saveFocusPreference(focus)"
              class="focus-option"
              :class="{ active: userFocus === focus }"
            >
              <span>{{ getFocusLabel(focus) }}</span>
              <svg v-if="userFocus === focus" class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
      </div>

      <!-- Content -->
      <div v-else class="dashboard-content">
        
        <!-- 🚨 ALERTA TRIAL EXPIRADO -->
        <div v-if="isTrialExpired && !isPaidPlan" class="trial-expired-alert">
          <div class="alert-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <div class="alert-content">
            <h3>🔒 Trial Expirado</h3>
            <p>Seu período gratuito de 3 dias terminou. Assine um plano para continuar usando todas as funcionalidades.</p>
            <router-link to="/pricing" class="btn-upgrade">
              Assinar Agora
            </router-link>
          </div>
        </div>

        <!-- ⏰ CONTADOR TRIAL (apenas para usuários free com trial ativo) -->
        <div v-if="!isPaidPlan && !isTrialExpired && trialStatus" class="trial-counter">
          <div class="trial-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
          </div>
          <div class="trial-info">
            <h3>⏰ Trial Gratuito</h3>
            <p class="trial-days">
              <strong>{{ trialDaysRemaining }}</strong> 
              {{ trialDaysRemaining === 1 ? 'dia restante' : 'dias restantes' }}
            </p>
            <div class="trial-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${((3 - trialDaysRemaining) / 3) * 100}%` }"></div>
              </div>
              <span class="progress-text">{{ 3 - trialDaysRemaining }}/3 dias utilizados</span>
            </div>
            <router-link to="/pricing" class="btn-trial">
              Assinar Antes que Expire
            </router-link>
          </div>
        </div>

        <!-- Stats Cards - Filtrado por Foco -->
        <div class="stats-grid">
          <!-- Análises Hoje - Sempre visível -->
          <div class="stat-card" v-if="userFocus === 'all' || userFocus === 'bet'">
            <div class="stat-icon-wrapper">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 21H3V3"/>
                <path d="M21 9l-6 6-4-4-6 6"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ userStats.analysesToday }}</span>
              <span class="stat-label">Análises hoje</span>
            </div>
          </div>
          <!-- Taxa de Acerto - BET -->
          <div class="stat-card" v-if="userFocus === 'all' || userFocus === 'bet'">
            <div class="stat-icon-wrapper success">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ userStats.winRate }}%</span>
              <span class="stat-label">Taxa de acerto</span>
            </div>
          </div>
          <!-- Jogos ao Vivo - BET -->
          <div class="stat-card live-card" v-if="userFocus === 'all' || userFocus === 'bet'" @click="router.push('/live')">
            <div class="stat-icon-wrapper warning">
              <span class="live-dot"></span>
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polygon points="10 8 16 12 10 16 10 8"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ liveGamesCount }}</span>
              <span class="stat-label">🔴 Ao Vivo</span>
            </div>
          </div>
          
          <!-- 📈 TRADE Stats -->
          <div class="stat-card" v-if="userFocus === 'all' || userFocus === 'trade'" @click="router.push('/trade')">
            <div class="stat-icon-wrapper trade-green">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                <polyline points="16 7 22 7 22 13"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ marketData.btc || '--' }}</span>
              <span class="stat-label">BTC/USD</span>
            </div>
          </div>
          <div class="stat-card" v-if="userFocus === 'trade'" @click="router.push('/trade')">
            <div class="stat-icon-wrapper trade-blue">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ marketData.usd || '--' }}</span>
              <span class="stat-label">USD/BRL</span>
            </div>
          </div>
          
          <!-- 🏆 CARTOLA Stats -->
          <div class="stat-card" v-if="userFocus === 'all' || userFocus === 'cartola'" @click="router.push('/cartola')">
            <div class="stat-icon-wrapper cartola-gold">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 2a10 10 0 0 0-7.07 17.07"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ cartolaData.status || 'Mercado' }}</span>
              <span class="stat-label">Cartola FC</span>
            </div>
          </div>
          <div class="stat-card" v-if="userFocus === 'cartola'" @click="router.push('/cartola')">
            <div class="stat-icon-wrapper cartola-green">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ cartolaData.rodada || '--' }}</span>
              <span class="stat-label">Rodada Atual</span>
            </div>
          </div>
          
          <!-- Análises Restantes - Sempre visível -->
          <div class="stat-card">
            <div class="stat-icon-wrapper primary">
              <svg class="stat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ currentPlan.limits?.analysisPerDay === -1 ? '∞' : currentPlan.limits?.analysisPerDay }}</span>
              <span class="stat-label">Análises restantes</span>
            </div>
          </div>
        </div>

        <!-- Plan Card -->
        <div class="plan-section">
          <div class="plan-card-dashboard">
            <div class="plan-info-dash">
              <div class="plan-badge-large" :class="{ 'canceled': isCanceledButActive }">
                {{ currentPlan.name }}
                <span v-if="isCanceledButActive" class="canceled-tag">Cancelado</span>
              </div>
              <h3>Seu Plano Atual</h3>
              <p v-if="currentPlan.id === 'free'">
                Faça upgrade para desbloquear mais recursos
              </p>
              <p v-else-if="isCanceledButActive" class="cancel-notice">
                <svg class="warning-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                Assinatura cancelada. Acesso até: {{ subscription?.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString('pt-BR') : 'N/A' }}
              </p>
              <p v-else>
                Próxima cobrança: {{ subscription?.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString('pt-BR') : 'N/A' }}
              </p>
            </div>
            <div class="plan-actions-dash">
              <router-link v-if="currentPlan.id === 'free'" to="/pricing" class="btn-upgrade">
                Fazer Upgrade
              </router-link>
              <template v-else>
                <button @click="openBillingPortal" class="btn-manage">
                  Gerenciar Assinatura
                </button>
                <button v-if="!isCanceledButActive" @click="showCancelModal = true" class="btn-cancel">
                  Cancelar Assinatura
                </button>
                <router-link v-else to="/pricing" class="btn-reactivate">
                  Reativar Assinatura
                </router-link>
              </template>
            </div>
          </div>
        </div>

        <!-- 📡 Feed em Tempo Real -->
        <div class="live-feed-section">
          <div class="section-header">
            <h2>
              <span class="live-dot-header"></span>
              Atualizações em Tempo Real
            </h2>
            <button @click="loadLiveFeed" class="btn-refresh-feed" :disabled="feedLoading">
              <svg class="refresh-icon" :class="{ spinning: feedLoading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6"/>
                <path d="M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
            </button>
          </div>
          
          <div v-if="feedLoading && liveFeed.length === 0" class="feed-loading">
            <div class="spinner-small"></div>
            <span>Carregando atualizações...</span>
          </div>
          
          <div v-else-if="liveFeed.length > 0" class="feed-list">
            <div 
              v-for="(item, index) in liveFeed.slice(0, 6)" 
              :key="index"
              class="feed-item"
              :class="item.type"
              @click="item.action"
            >
              <div class="feed-icon">{{ item.icon }}</div>
              <div class="feed-content">
                <span class="feed-title">{{ item.title }}</span>
                <span class="feed-subtitle">{{ item.subtitle }}</span>
              </div>
              <div class="feed-status" :class="item.type">{{ item.status }}</div>
            </div>
          </div>
          
          <div v-else class="feed-empty">
            <span>📡</span>
            <p>Nenhuma atualização disponível</p>
          </div>
        </div>

        <!-- Quick Actions - Filtrado por Foco -->
        <div class="quick-actions">
          <h2>Ações Rápidas</h2>
          <div class="actions-grid">
            <!-- BET Action -->
            <div class="action-card" v-if="userFocus === 'all' || userFocus === 'bet'">
              <div class="action-icon-wrapper bet">
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
              </div>
              <h4>Nova Análise BET</h4>
              <p>Analise partidas esportivas</p>
              <router-link to="/bet" class="action-btn">Iniciar</router-link>
            </div>
            
            <!-- Ao Vivo Action - BET -->
            <div class="action-card live-action" v-if="userFocus === 'bet'">
              <div class="action-icon-wrapper live">
                <span class="live-dot-action"></span>
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polygon points="10 8 16 12 10 16 10 8"/>
                </svg>
              </div>
              <h4>Jogos ao Vivo</h4>
              <p>{{ liveGamesCount }} jogos acontecendo</p>
              <router-link to="/live" class="action-btn live-btn">Assistir</router-link>
            </div>
            
            <!-- TRADE Action -->
            <div class="action-card" v-if="userFocus === 'all' || userFocus === 'trade'">
              <div class="action-icon-wrapper trade">
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                  <polyline points="16 7 22 7 22 13"/>
                </svg>
              </div>
              <h4>Nova Análise TRADE</h4>
              <p>Cripto, Forex e Ações</p>
              <router-link to="/trade" class="action-btn">Iniciar</router-link>
            </div>
            
            <!-- Paper Trading - TRADE -->
            <div class="action-card" v-if="userFocus === 'trade'">
              <div class="action-icon-wrapper paper">
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <h4>Paper Trading</h4>
              <p>Pratique sem risco</p>
              <router-link to="/paper-trading" class="action-btn">Praticar</router-link>
            </div>
            
            <!-- CARTOLA Action -->
            <div class="action-card" v-if="userFocus === 'all' || userFocus === 'cartola'">
              <div class="action-icon-wrapper cartola">
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 2a10 10 0 0 0-7.07 17.07M12 2a10 10 0 0 1 7.07 17.07"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
              <h4>Cartola FC</h4>
              <p>Escale seu time com IA</p>
              <router-link to="/cartola" class="action-btn">Acessar</router-link>
            </div>
            
            <!-- Scouts - CARTOLA -->
            <div class="action-card" v-if="userFocus === 'cartola'">
              <div class="action-icon-wrapper scouts">
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <h4>Ver Scouts</h4>
              <p>Pontuação em tempo real</p>
              <router-link to="/cartola" class="action-btn">Ver</router-link>
            </div>
            
            <!-- Relatórios - Sempre visível -->
            <div class="action-card">
              <div class="action-icon-wrapper report">
                <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <h4>Relatórios</h4>
              <p>Seu desempenho detalhado</p>
              <router-link to="/history" class="action-btn">Ver</router-link>
            </div>
          </div>
        </div>

        <!-- Recent Analyses -->
        <div class="recent-section">
          <div class="section-header">
            <h2>Análises Recentes</h2>
            <router-link to="/history" class="see-all">Ver tudo →</router-link>
          </div>
          
          <!-- Se tem análises -->
          <div v-if="recentAnalyses.length > 0" class="analyses-list">
            <div v-for="analysis in recentAnalyses" :key="analysis.id" class="analysis-item">
              <div class="analysis-icon" :class="analysis.type">
                {{ analysis.type === 'bet' ? '⚽' : analysis.type === 'trade' ? '📈' : '🏆' }}
              </div>
              <div class="analysis-info">
                <span class="analysis-title">{{ analysis.title }}</span>
                <span class="analysis-meta">{{ analysis.asset }} • {{ new Date(analysis.created_at).toLocaleDateString('pt-BR') }}</span>
              </div>
              <div class="analysis-result" :class="analysis.result">
                {{ analysis.result === 'win' ? '✅ Green' : analysis.result === 'loss' ? '❌ Red' : '⏳ Pendente' }}
              </div>
            </div>
          </div>
          
          <!-- Se não tem análises -->
          <div v-else class="empty-state">
            <div class="empty-icon-wrapper">
              <svg class="empty-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <h4>Nenhuma análise ainda</h4>
            <p>Comece fazendo sua primeira análise!</p>
            <router-link to="/bet" class="btn-start">Fazer Análise</router-link>
          </div>
        </div>
      </div>
    </main>

    <!-- Cancel Modal -->
    <div v-if="showCancelModal" class="modal-overlay" @click.self="showCancelModal = false">
      <div class="modal">
        <div class="modal-icon-wrapper">
          <svg class="modal-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h3>Cancelar Assinatura?</h3>
        <p>Tem certeza que deseja cancelar sua assinatura do plano <strong>{{ currentPlan.name }}</strong>?</p>
        <ul class="cancel-info">
          <li>Você continuará tendo acesso até o fim do período pago</li>
          <li>Perderá acesso aos recursos premium após essa data</li>
          <li>Pode reativar a qualquer momento</li>
        </ul>
        <div class="modal-actions">
          <button @click="showCancelModal = false" class="btn-keep" :disabled="canceling">
            Manter Assinatura
          </button>
          <button @click="handleCancelSubscription" class="btn-confirm-cancel" :disabled="canceling">
            {{ canceling ? 'Cancelando...' : 'Confirmar Cancelamento' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 📷 Modal de Upload de Avatar -->
    <div v-if="showAvatarModal" class="modal-overlay" @click.self="showAvatarModal = false">
      <div class="avatar-modal">
        <button class="modal-close" @click="showAvatarModal = false">&times;</button>
        <h3>📷 Alterar Foto de Perfil</h3>
        
        <div class="avatar-preview-container">
          <img 
            v-if="userAvatar" 
            :src="userAvatar" 
            alt="Preview" 
            class="avatar-preview"
          />
          <div v-else class="avatar-preview-placeholder">
            {{ userName?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
        </div>
        
        <input 
          ref="avatarInput"
          type="file" 
          accept="image/png,image/jpeg,image/webp"
          @change="handleAvatarUpload"
          style="display: none"
        />
        
        <div class="avatar-modal-actions">
          <button 
            class="btn-upload-avatar" 
            @click="avatarInput?.click()"
            :disabled="uploadingAvatar"
          >
            {{ uploadingAvatar ? 'Enviando...' : '📤 Escolher Imagem' }}
          </button>
          <p class="avatar-hint">PNG, JPG ou WEBP - Máx. 2MB</p>
        </div>
      </div>
    </div>

    <!-- Bottom Navigation Mobile -->
    <BottomNav :showAdmin="userIsAdmin" />
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  display: -webkit-box;
  display: -webkit-flex;
  min-height: 100vh;
  min-height: 100dvh;
  min-height: -webkit-fill-available;
  background: #000;
  color: #fff;
  -webkit-overflow-scrolling: touch;
}

/* Admin Viewer Counter */
.admin-viewer-counter {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: rgba(255, 255, 255, 0.02);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  display: -webkit-box;
  display: -webkit-flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  height: 100dvh;
  height: -webkit-fill-available;
  left: 0;
  top: 0;
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
  -webkit-transform: translateZ(0);
  transform: translateZ(0);
}

.sidebar-header {
  padding: 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  height: 35px;
}

.sidebar-nav {
  -webkit-box-flex: 1;
  flex: 1;
  padding: 20px 15px;
  display: flex;
  display: -webkit-box;
  display: -webkit-flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  flex-direction: column;
  gap: 5px;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.nav-category {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.35);
  padding: 15px 15px 8px;
  font-weight: 600;
}

.nav-category:first-child {
  padding-top: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  transition: all 0.3s;
  text-decoration: none;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.admin-link {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
}

.nav-item.admin-link:hover {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
}

/* 🔴 Link Ao Vivo com destaque */
.nav-item.live-nav {
  background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%);
  border: 1px solid rgba(255, 68, 68, 0.3);
  color: #ff6b6b;
  position: relative;
}

.nav-item.live-nav:hover {
  background: linear-gradient(135deg, rgba(255, 68, 68, 0.2) 0%, rgba(255, 140, 0, 0.2) 100%);
}

.live-indicator {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background: #ff4444;
  border-radius: 50%;
  animation: live-pulse 1.5s infinite;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7); }
  50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(255, 68, 68, 0); }
}

.mobile-nav-item.live-mobile {
  background: linear-gradient(135deg, rgba(255, 68, 68, 0.15) 0%, rgba(255, 140, 0, 0.15) 100%);
  border: 1px solid rgba(255, 68, 68, 0.3);
  color: #ff6b6b;
}

.mobile-nav-item.admin-mobile {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.plan-badge-sidebar {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  text-align: center;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.6);
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.logout-icon {
  width: 18px;
  height: 18px;
}

/* Main Content */
.main-content {
  -webkit-box-flex: 1;
  flex: 1;
  margin-left: 260px;
  padding: 30px;
  padding-top: calc(30px + env(safe-area-inset-top, 0px));
  padding-bottom: calc(30px + env(safe-area-inset-bottom, 0px));
  -webkit-overflow-scrolling: touch;
}

/* Header */
.dashboard-header {
  display: flex;
  display: -webkit-box;
  display: -webkit-flex;
  -webkit-box-pack: justify;
  justify-content: space-between;
  -webkit-box-align: center;
  align-items: center;
  margin-bottom: 40px;
}

.header-left h1 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 5px;
}

.header-left p {
  color: rgba(255, 255, 255, 0.5);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 45px;
  height: 45px;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  color: white;
  border: 2px solid rgba(0, 217, 255, 0.5);
  box-shadow: 0 4px 15px rgba(0, 217, 255, 0.2);
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
}

.user-email {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Loading */
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
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon-wrapper {
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon-wrapper.success {
  background: rgba(34, 197, 94, 0.15);
}

.stat-icon-wrapper.success .stat-svg {
  stroke: #22c55e;
}

.stat-icon-wrapper.warning {
  background: rgba(234, 179, 8, 0.15);
}

.stat-icon-wrapper.warning .stat-svg {
  stroke: #eab308;
}

.stat-icon-wrapper.primary {
  background: rgba(59, 130, 246, 0.15);
}

.stat-icon-wrapper.primary .stat-svg {
  stroke: #3b82f6;
}

/* Trade Stats Colors */
.stat-icon-wrapper.trade-green {
  background: rgba(16, 185, 129, 0.15);
}

.stat-icon-wrapper.trade-green .stat-svg {
  stroke: #10b981;
}

.stat-icon-wrapper.trade-blue {
  background: rgba(59, 130, 246, 0.15);
}

.stat-icon-wrapper.trade-blue .stat-svg {
  stroke: #3b82f6;
}

/* Cartola Stats Colors */
.stat-icon-wrapper.cartola-gold {
  background: rgba(255, 193, 7, 0.15);
}

.stat-icon-wrapper.cartola-gold .stat-svg {
  stroke: #ffc107;
}

.stat-icon-wrapper.cartola-green {
  background: rgba(34, 197, 94, 0.15);
}

.stat-icon-wrapper.cartola-green .stat-svg {
  stroke: #22c55e;
}

.stat-svg {
  width: 28px;
  height: 28px;
  stroke: #fff;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
}

.stat-label {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

/* Plan Section */
.plan-section {
  margin-bottom: 40px;
}

.plan-card-dashboard {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 35px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.plan-badge-large {
  display: inline-block;
  background: #fff;
  color: #000;
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 1px;
  margin-bottom: 15px;
}

.plan-info-dash h3 {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.plan-info-dash p {
  color: rgba(255, 255, 255, 0.5);
}

.btn-upgrade,
.btn-manage {
  padding: 15px 30px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upgrade {
  background: #fff;
  color: #000;
  text-decoration: none;
}

.btn-upgrade:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

.btn-manage {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-manage:hover {
  border-color: #fff;
}

/* Quick Actions */
.quick-actions {
  margin-bottom: 40px;
}

.quick-actions h2 {
  font-size: 1.3rem;
  margin-bottom: 20px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.action-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  text-align: center;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.2);
}

.action-icon-wrapper {
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
}

.action-icon-wrapper.bet {
  background: rgba(34, 197, 94, 0.15);
}

.action-icon-wrapper.bet .action-svg {
  stroke: #22c55e;
}

.action-icon-wrapper.trade {
  background: rgba(59, 130, 246, 0.15);
}

.action-icon-wrapper.trade .action-svg {
  stroke: #3b82f6;
}

.action-icon-wrapper.calendar {
  background: rgba(168, 85, 247, 0.15);
}

.action-icon-wrapper.calendar .action-svg {
  stroke: #a855f7;
}

.action-icon-wrapper.report {
  background: rgba(234, 179, 8, 0.15);
}

.action-icon-wrapper.report .action-svg {
  stroke: #eab308;
}

.action-icon-wrapper.cartola {
  background: rgba(155, 89, 182, 0.15);
}

.action-icon-wrapper.cartola .action-svg {
  stroke: #9b59b6;
}

/* Live Action */
.action-icon-wrapper.live {
  background: rgba(255, 71, 87, 0.15);
  position: relative;
}

.action-icon-wrapper.live .action-svg {
  stroke: #ff4757;
}

.live-dot-action {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  background: #ff4757;
  border-radius: 50%;
  animation: pulse-live 1.5s infinite;
}

.action-card.live-action {
  border-color: rgba(255, 71, 87, 0.3);
}

.action-btn.live-btn {
  background: rgba(255, 71, 87, 0.2);
  color: #ff4757;
  border: 1px solid rgba(255, 71, 87, 0.3);
}

.action-btn.live-btn:hover {
  background: rgba(255, 71, 87, 0.3);
}

/* Paper Trading Action */
.action-icon-wrapper.paper {
  background: rgba(139, 92, 246, 0.15);
}

.action-icon-wrapper.paper .action-svg {
  stroke: #8b5cf6;
}

/* Scouts Action */
.action-icon-wrapper.scouts {
  background: rgba(34, 197, 94, 0.15);
}

.action-icon-wrapper.scouts .action-svg {
  stroke: #22c55e;
}

.action-svg {
  width: 28px;
  height: 28px;
  stroke: #fff;
}

.action-card h4 {
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.action-card p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  margin-bottom: 20px;
}

.action-btn {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Recent Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 1.3rem;
  margin: 0;
}

.see-all {
  color: #7c3aed;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.see-all:hover {
  color: #a855f7;
}

.analyses-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analysis-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.analysis-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(124, 58, 237, 0.3);
}

.analysis-icon {
  width: 45px;
  height: 45px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.analysis-icon.bet { background: rgba(34, 197, 94, 0.2); }
.analysis-icon.trade { background: rgba(59, 130, 246, 0.2); }
.analysis-icon.cartola { background: rgba(168, 85, 247, 0.2); }

.analysis-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.analysis-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.analysis-meta {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.analysis-result {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
}

.analysis-result.win { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.analysis-result.loss { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.analysis-result.pending { background: rgba(234, 179, 8, 0.2); color: #eab308; }

/* Live Card Animation */
.stat-card.live-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card.live-card:hover {
  transform: translateY(-3px);
  border-color: rgba(239, 68, 68, 0.5);
}

.live-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse-red 1.5s infinite;
}

@keyframes pulse-red {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.btn-start {
  display: inline-block;
  margin-top: 15px;
  padding: 12px 25px;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #fff;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-start:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(124, 58, 237, 0.4);
}

.empty-state {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 60px;
  text-align: center;
}

.empty-icon-wrapper {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.empty-svg {
  width: 40px;
  height: 40px;
  stroke: rgba(255, 255, 255, 0.4);
}

.empty-state h4 {
  font-size: 1.2rem;
  margin-bottom: 8px;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.5);
}

/* ===== MOBILE MENU ===== */
.mobile-menu-btn {
  display: none;
  position: fixed;
  top: calc(20px + env(safe-area-inset-top));
  right: calc(20px + env(safe-area-inset-right));
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  box-shadow: 0 5px 30px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  cursor: pointer;
  -webkit-box-align: center;
  align-items: center;
  -webkit-box-pack: center;
  justify-content: center;
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
}

.mobile-menu-btn svg {
  width: 28px;
  height: 28px;
  stroke: #000;
}

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 998;
  -webkit-backdrop-filter: blur(5px);
  backdrop-filter: blur(5px);
}

.mobile-menu {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #0a0a0a;
  border-top-left-radius: 25px;
  border-top-right-radius: 25px;
  padding: 25px;
  padding-bottom: calc(25px + env(safe-area-inset-bottom));
  z-index: 999;
  -webkit-transform: translateY(100%);
  transform: translateY(100%);
  -webkit-transition: -webkit-transform 0.3s ease;
  transition: transform 0.3s ease;
  max-height: 80vh;
  max-height: 80dvh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-menu.open {
  -webkit-transform: translateY(0);
  transform: translateY(0);
}

.mobile-menu-header {
  text-align: center;
  margin-bottom: 20px;
}

.mobile-logo {
  height: 35px;
}

.mobile-nav {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  gap: 8px;
}

.mobile-nav-item {
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-weight: 500;
  cursor: pointer;
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  text-align: left;
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.mobile-logout {
  width: 100%;
  margin-top: 15px;
  padding: 15px;
  background: transparent;
  border: 1px solid #ef4444;
  border-radius: 12px;
  color: #ef4444;
  font-weight: 600;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid,
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 968px) {
  .sidebar {
    display: none;
  }
  
  .mobile-menu-btn {
    display: none;
  }
  
  .mobile-overlay {
    display: none;
  }
  
  .mobile-menu {
    display: none;
  }
  
  .main-content {
    margin-left: 0;
    padding-left: calc(20px + env(safe-area-inset-left));
    padding-right: calc(20px + env(safe-area-inset-right));
    padding-bottom: 85px;
  }
  
  .dashboard-header {
    -webkit-box-orient: vertical;
    -webkit-box-direction: normal;
    -webkit-flex-direction: column;
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .plan-card-dashboard {
    -webkit-box-orient: vertical;
    -webkit-box-direction: normal;
    -webkit-flex-direction: column;
    flex-direction: column;
    text-align: center;
    gap: 25px;
  }
  
  .plan-actions-dash {
    -webkit-box-orient: vertical;
    -webkit-box-direction: normal;
    -webkit-flex-direction: column;
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .stats-grid,
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .main-content {
    padding: 20px;
    padding-left: calc(20px + env(safe-area-inset-left));
    padding-right: calc(20px + env(safe-area-inset-right));
    padding-bottom: calc(100px + env(safe-area-inset-bottom));
  }
}

/* Cancel Button */
.btn-cancel {
  padding: 12px 25px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background: transparent;
  color: #ff6b6b;
  border: 1px solid #ff6b6b;
}

.btn-cancel:hover {
  background: rgba(255, 107, 107, 0.1);
}

/* Reactivate Button */
.btn-reactivate {
  padding: 12px 25px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background: #4CAF50;
  color: #fff;
  text-decoration: none;
  border: none;
}

.btn-reactivate:hover {
  background: #45a049;
}

/* Plan Actions */
.plan-actions-dash {
  display: flex;
  gap: 15px;
  align-items: center;
}

/* Canceled Badge */
.plan-badge-large.canceled {
  background: linear-gradient(135deg, #ff6b6b, #ee5253);
}

.canceled-tag {
  font-size: 0.7rem;
  margin-left: 10px;
  opacity: 0.8;
}

.cancel-notice {
  color: #ff6b6b !important;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  max-width: 450px;
  width: 100%;
  text-align: center;
}

.modal-icon-wrapper {
  width: 70px;
  height: 70px;
  background: rgba(255, 107, 107, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.modal-svg {
  width: 35px;
  height: 35px;
  stroke: #ff6b6b;
}

.warning-icon {
  width: 18px;
  height: 18px;
  stroke: #eab308;
  vertical-align: middle;
  margin-right: 5px;
}

.modal h3 {
  font-size: 1.5rem;
  margin-bottom: 15px;
}

.modal p {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 25px;
}

.cancel-info {
  text-align: left;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 25px;
  list-style: none;
}

.cancel-info li {
  padding: 8px 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.cancel-info li::before {
  content: "•";
  color: #ff6b6b;
  margin-right: 10px;
}

.modal-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.btn-keep {
  padding: 15px 30px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
  color: #000;
  border: none;
}

.btn-keep:hover {
  transform: translateY(-2px);
}

.btn-keep:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm-cancel {
  padding: 15px 30px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: transparent;
  color: #ff6b6b;
  border: 1px solid #ff6b6b;
}

.btn-confirm-cancel:hover {
  background: rgba(255, 107, 107, 0.1);
}

.btn-confirm-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 500px) {
  .modal-actions {
    flex-direction: column;
  }
  
  .modal {
    padding: 30px 20px;
  }
}

/* ============================================= */
/* TRIAL COUNTER & EXPIRED ALERT STYLES */
/* ============================================= */

.trial-expired-alert {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, rgba(255, 107, 107, 0.05) 100%);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0%, 100% { border-color: rgba(255, 107, 107, 0.3); }
  50% { border-color: rgba(255, 107, 107, 0.6); }
}

.trial-expired-alert .alert-icon {
  background: rgba(255, 107, 107, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trial-expired-alert .alert-icon svg {
  width: 24px;
  height: 24px;
  color: #ff6b6b;
}

.trial-expired-alert .alert-content h3 {
  color: #ff6b6b;
  margin: 0 0 8px 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.trial-expired-alert .alert-content p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 16px 0;
  font-size: 0.95rem;
}

.trial-counter {
  background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(0, 217, 255, 0.05) 100%);
  border: 1px solid rgba(0, 217, 255, 0.3);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.trial-counter .trial-icon {
  background: rgba(0, 217, 255, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trial-counter .trial-icon svg {
  width: 24px;
  height: 24px;
  color: #00d9ff;
}

.trial-info {
  flex: 1;
}

.trial-info h3 {
  color: #00d9ff;
  margin: 0 0 8px 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.trial-days {
  color: white;
  margin: 0 0 12px 0;
  font-size: 1.1rem;
}

.trial-days strong {
  color: #00d9ff;
  font-size: 1.4rem;
  font-weight: 800;
}

.trial-progress {
  margin-bottom: 16px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00d9ff, #0099cc);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
}

.btn-trial, .btn-upgrade {
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.btn-trial:hover, .btn-upgrade:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 217, 255, 0.3);
}

.btn-upgrade {
  background: linear-gradient(135deg, #ff6b6b, #cc4444);
}

.btn-upgrade:hover {
  box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .trial-counter, .trial-expired-alert {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .trial-info, .alert-content {
    text-align: center;
  }
}

/* ========================================
   🎨 Avatar Upload System
   ======================================== */

.user-avatar-wrapper {
  position: relative;
  cursor: pointer;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.user-avatar-wrapper:hover {
  transform: scale(1.05);
}

.user-avatar-img {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(0, 217, 255, 0.5);
  box-shadow: 0 4px 15px rgba(0, 217, 255, 0.2);
  display: block;
}

.user-avatar-placeholder {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: white;
  border: 2px solid rgba(0, 217, 255, 0.5);
}

.avatar-edit-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 18px;
  height: 18px;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  border: 2px solid rgba(13, 26, 43, 0.9);
}

/* Avatar Modal */
.avatar-modal {
  background: linear-gradient(145deg, rgba(13, 26, 43, 0.98), rgba(8, 18, 32, 0.98));
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  max-width: 340px;
  width: 90%;
  text-align: center;
  position: relative;
}

.avatar-modal h3 {
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.avatar-preview-container {
  margin: 20px auto;
}

.avatar-preview {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid rgba(0, 217, 255, 0.4);
}

.avatar-preview-placeholder {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: bold;
  color: white;
  margin: 0 auto;
}

.avatar-modal-actions {
  margin-top: 20px;
}

.btn-upload-avatar {
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upload-avatar:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 217, 255, 0.4);
}

.btn-upload-avatar:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.avatar-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

/* ========================================
   🎯 Focus Selector
   ======================================== */

.focus-selector-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.05);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid rgba(0, 217, 255, 0.1);
}

.focus-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
}

.focus-selector {
  position: relative;
  flex: 1;
}

.focus-current {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(0, 217, 255, 0.1);
  border: 1px solid rgba(0, 217, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.focus-current:hover {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.5);
}

.focus-text {
  font-weight: 600;
  font-size: 0.95rem;
}

.focus-arrow {
  transition: transform 0.3s;
}

.focus-arrow.open {
  transform: rotate(180deg);
}

.focus-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: rgba(13, 26, 43, 0.98);
  border: 1px solid rgba(0, 217, 255, 0.3);
  border-radius: 8px;
  overflow: hidden;
  z-index: 100;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.focus-option {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.focus-option:last-child {
  border-bottom: none;
}

.focus-option:hover {
  background: rgba(0, 217, 255, 0.15);
}

.focus-option.active {
  background: rgba(0, 217, 255, 0.2);
  color: #00d9ff;
}

.focus-check {
  margin-left: auto;
  color: #00d9ff;
}

/* ========================================
   📡 Live Feed Section
   ======================================== */

.live-feed-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 217, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 32px;
}

.live-feed-section .section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.live-feed-section h2 {
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-dot-header {
  width: 10px;
  height: 10px;
  background: #ff4757;
  border-radius: 50%;
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.btn-refresh-feed {
  background: rgba(0, 217, 255, 0.1);
  border: 1px solid rgba(0, 217, 255, 0.3);
  color: #00d9ff;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh-feed:hover:not(:disabled) {
  background: rgba(0, 217, 255, 0.2);
}

.btn-refresh-feed:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-icon {
  width: 18px;
  height: 18px;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Feed Loading */
.feed-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: rgba(255, 255, 255, 0.6);
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0, 217, 255, 0.2);
  border-top-color: #00d9ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Feed List */
.feed-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feed-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s;
}

.feed-item:hover {
  background: rgba(0, 217, 255, 0.08);
  border-color: rgba(0, 217, 255, 0.2);
  transform: translateX(4px);
}

.feed-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.feed-item.bet .feed-icon {
  background: rgba(0, 217, 255, 0.15);
}

.feed-item.trade .feed-icon {
  background: rgba(16, 185, 129, 0.15);
}

.feed-item.cartola .feed-icon {
  background: rgba(255, 193, 7, 0.15);
}

.feed-content {
  flex: 1;
  min-width: 0;
}

.feed-title {
  display: block;
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-subtitle {
  display: block;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-status {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.feed-status.bet {
  background: rgba(0, 217, 255, 0.2);
  color: #00d9ff;
}

.feed-status.trade {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.feed-status.cartola {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

/* Feed Empty */
.feed-empty {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.4);
}

.feed-empty span {
  font-size: 32px;
  display: block;
  margin-bottom: 10px;
}

/* Mobile Feed Adjustments */
@media (max-width: 768px) {
  .focus-selector-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .focus-label {
    text-align: center;
  }
  
  .user-avatar-img,
  .user-avatar-placeholder {
    width: 44px;
    height: 44px;
  }
  
  .feed-item {
    padding: 12px;
  }
  
  .feed-icon {
    width: 38px;
    height: 38px;
    font-size: 18px;
  }
  
  .feed-title {
    font-size: 0.9rem;
  }
  
  .feed-status {
    font-size: 0.65rem;
    padding: 3px 8px;
  }
}
</style>
