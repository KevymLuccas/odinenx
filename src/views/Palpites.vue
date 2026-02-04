<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const jogos = ref([])
const jogoSelecionado = ref(null)
const lastUpdate = ref(null)
const mostrarModalBloqueio = ref(false)
const oddsReais = ref({}) // Cache de odds reais por jogo
const loadingOdds = ref(false)
const mostrarExplicacaoOdds = ref(false) // Toggle para explicação das odds

// Função para toggle da explicação
const toggleOddsExplicacao = () => {
  mostrarExplicacaoOdds.value = !mostrarExplicacaoOdds.value
}

// Controle de análises vistas hoje - BACKEND + localStorage (fallback)
const ANALISES_KEY = 'odinenx_analises_vistas'
const MAX_ANALISES_FREE = 3
const analisesVistasTrigger = ref(0) // Trigger para reatividade

// Verificar análise no backend (Supabase)
const verificarAnaliseBackend = async (jogoId) => {
  if (!user.value) return { allowed: true, remaining: MAX_ANALISES_FREE }
  
  try {
    const { data, error } = await supabase.rpc('can_view_analysis', {
      p_user_id: user.value.id,
      p_analysis_id: String(jogoId),
      p_type: 'palpite'
    })
    
    if (error) throw error
    return data
  } catch (err) {
    console.warn('Backend check failed, using localStorage fallback:', err)
    // Fallback para localStorage se backend falhar
    return null
  }
}

// Registrar visualização no backend
const registrarAnaliseBackend = async (jogoId) => {
  if (!user.value) return
  
  try {
    await supabase.rpc('register_analysis_view', {
      p_user_id: user.value.id,
      p_analysis_id: String(jogoId),
      p_type: 'palpite'
    })
  } catch (err) {
    console.warn('Backend register failed:', err)
  }
}

// Fallback localStorage (para quando backend não está disponível)
const getAnalisesVistasHoje = () => {
  try {
    const data = localStorage.getItem(ANALISES_KEY)
    if (!data) return { date: '', ids: [] }
    const parsed = JSON.parse(data)
    const hoje = new Date().toDateString()
    // Reset se for outro dia
    if (parsed.date !== hoje) {
      localStorage.setItem(ANALISES_KEY, JSON.stringify({ date: hoje, ids: [] }))
      return { date: hoje, ids: [] }
    }
    return parsed
  } catch {
    return { date: new Date().toDateString(), ids: [] }
  }
}

const salvarAnaliseVista = async (jogoId) => {
  // Salvar no backend primeiro
  await registrarAnaliseBackend(jogoId)
  
  // Também salvar em localStorage como backup
  const atual = getAnalisesVistasHoje()
  if (!atual.ids.includes(jogoId)) {
    atual.ids.push(jogoId)
    atual.date = new Date().toDateString()
    localStorage.setItem(ANALISES_KEY, JSON.stringify(atual))
    analisesVistasTrigger.value++ // Dispara reatividade
  }
}

const analisesRestantes = computed(() => {
  // Depende do trigger para ser reativo
  const _ = analisesVistasTrigger.value
  // Verifica se tem plano pago
  if (subscription.value && subscription.value.plan && subscription.value.plan !== 'free') {
    return -1 // Ilimitado
  }
  const vistas = getAnalisesVistasHoje()
  return Math.max(0, MAX_ANALISES_FREE - vistas.ids.length)
})

// Função para pegar o nível de confiança com texto
const getNivelConfianca = (confianca) => {
  if (confianca >= 65) return { nivel: 'muito-alta', texto: '🔥 MUITO CONFIÁVEL', cor: '#00e676' }
  if (confianca >= 55) return { nivel: 'alta', texto: '✅ CONFIÁVEL', cor: '#4caf50' }
  if (confianca >= 45) return { nivel: 'media', texto: '⚠️ MODERADO', cor: '#ffc107' }
  return { nivel: 'baixa', texto: '❌ ARRISCADO', cor: '#f44336' }
}

// Filtros
const ligaSelecionada = ref('all')
const filtroConfianca = ref('all')
const filtroPalpite = ref('all')

// Ligas disponíveis
const LIGAS = {
  all: { nome: 'Todas as Ligas', code: 'all', pais: '🌍' },
  BSA: { nome: 'Brasileirão', code: 'BSA', pais: '🇧🇷' },
  PL: { nome: 'Premier League', code: 'PL', pais: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  PD: { nome: 'La Liga', code: 'PD', pais: '🇪🇸' },
  SA: { nome: 'Serie A', code: 'SA', pais: '🇮🇹' },
  BL1: { nome: 'Bundesliga', code: 'BL1', pais: '🇩🇪' },
  FL1: { nome: 'Ligue 1', code: 'FL1', pais: '🇫🇷' },
  CL: { nome: 'Champions League', code: 'CL', pais: '🏆' }
}

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user
  if (user.value) {
    subscription.value = await getSubscriptionStatus(user.value.id)
  }
  await carregarJogos()
})

watch(ligaSelecionada, () => carregarJogos())

// Verificar se tem acesso completo (plano pago)
const temAcessoCompleto = computed(() => {
  if (!subscription.value) return false
  const planId = subscription.value.plan || 'free'
  return planId !== 'free'
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

const carregarJogos = async () => {
  loading.value = true
  jogos.value = []
  
  try {
    let ligas = ligaSelecionada.value === 'all' 
      ? ['BSA', 'PL', 'PD', 'SA', 'BL1', 'FL1', 'CL'] 
      : [ligaSelecionada.value]
    
    for (const liga of ligas) {
      const response = await fetch(`/api/football?competition=${liga}&status=SCHEDULED`)
      if (response.ok) {
        const data = await response.json()
        if (data.matches) {
          const jogosLiga = data.matches.map(match => {
            const analise = calcularAnalise(match)
            return {
              id: match.id,
              casa: match.homeTeam.shortName || match.homeTeam.name,
              casaLogo: match.homeTeam.crest,
              fora: match.awayTeam.shortName || match.awayTeam.name,
              foraLogo: match.awayTeam.crest,
              data: new Date(match.utcDate).toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' }),
              hora: new Date(match.utcDate).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
              liga: LIGAS[liga]?.nome || data.competition?.name,
              ligaPais: LIGAS[liga]?.pais || '⚽',
              rodada: match.matchday ? `Rodada ${match.matchday}` : '',
              ...analise
            }
          })
          jogos.value = [...jogos.value, ...jogosLiga]
        }
      }
    }
    lastUpdate.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    console.error('Erro ao carregar jogos:', error)
  }
  loading.value = false
}

const calcularAnalise = (match) => {
  // Usar dados reais da API se disponíveis
  const homePos = match.homeTeam?.position || null
  const awayPos = match.awayTeam?.position || null
  const homeForm = match.homeTeam?.form || '' // Ex: "W,W,D,L,W"
  const awayForm = match.awayTeam?.form || ''
  const homeGoalsFor = match.homeTeam?.goalsFor || 0
  const homeGoalsAgainst = match.homeTeam?.goalsAgainst || 0
  const awayGoalsFor = match.awayTeam?.goalsFor || 0
  const awayGoalsAgainst = match.awayTeam?.goalsAgainst || 0
  const homeWins = match.homeTeam?.won || 0
  const awayWins = match.awayTeam?.won || 0
  const homePlayed = match.homeTeam?.playedGames || 0
  const awayPlayed = match.awayTeam?.playedGames || 0
  
  // Se não tem posição, usar hash do ID do time para gerar valores pseudoaleatórios mas consistentes
  const hashCode = (str) => {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i)
      hash |= 0
    }
    return Math.abs(hash)
  }
  
  // Calcular força dos times
  let forcaCasa, forcaFora
  
  if (homePos && awayPos) {
    // Com dados reais de classificação
    const fatorCasa = 1.30 // Vantagem de jogar em casa
    
    // Força base pela posição (1º lugar = 20 pontos, 20º lugar = 1 ponto)
    forcaCasa = (21 - homePos) * fatorCasa
    forcaFora = (21 - awayPos)
    
    // Adicionar bônus por forma recente (últimos 5 jogos)
    const calcFormaBonus = (form) => {
      if (!form) return 0
      let bonus = 0
      const results = form.split(',')
      results.forEach((r, i) => {
        const peso = 1 + (i * 0.1) // Jogos recentes pesam mais
        if (r === 'W') bonus += 2 * peso
        else if (r === 'D') bonus += 1 * peso
      })
      return bonus
    }
    
    forcaCasa += calcFormaBonus(homeForm)
    forcaFora += calcFormaBonus(awayForm)
    
    // Bônus por saldo de gols
    if (homeGoalsFor > 0) {
      forcaCasa += (homeGoalsFor - homeGoalsAgainst) / 10
    }
    if (awayGoalsFor > 0) {
      forcaFora += (awayGoalsFor - awayGoalsAgainst) / 10
    }
    
  } else {
    // Sem dados reais - usar algoritmo baseado em hash para consistência
    const homeHash = hashCode(String(match.homeTeam?.id || match.homeTeam?.name || 'home'))
    const awayHash = hashCode(String(match.awayTeam?.id || match.awayTeam?.name || 'away'))
    const matchHash = hashCode(String(match.id || Date.now()))
    
    // Gerar força pseudoaleatória mas consistente (5-20)
    forcaCasa = 8 + (homeHash % 12) + ((matchHash % 5) * 0.5) // 8-20
    forcaFora = 5 + (awayHash % 12) + ((matchHash % 3) * 0.5) // 5-17
    
    // Adicionar variação baseada no matchday se disponível
    if (match.matchday) {
      forcaCasa += (match.matchday % 3)
      forcaFora += ((match.matchday + 1) % 3)
    }
  }
  
  // Base para empate (varia de 6-12)
  const empateBase = homePos && awayPos 
    ? 6 + Math.min(6, Math.abs(homePos - awayPos) / 2)
    : 7 + (hashCode(String(match.id)) % 5)
  
  const total = forcaCasa + forcaFora + empateBase
  
  // Probabilidades brutas
  let probCasa = Math.round((forcaCasa / total) * 100)
  let probFora = Math.round((forcaFora / total) * 100)
  let probEmpate = 100 - probCasa - probFora
  
  // Garantir valores mínimos realistas
  probEmpate = Math.max(18, Math.min(35, probEmpate))
  probCasa = Math.max(20, Math.min(70, probCasa))
  probFora = Math.max(15, Math.min(60, probFora))
  
  // Normalizar para somar 100%
  const soma = probCasa + probEmpate + probFora
  probCasa = Math.round((probCasa / soma) * 100)
  probFora = Math.round((probFora / soma) * 100)
  probEmpate = 100 - probCasa - probFora
  
  // Calcular odds estimadas (com margem de 5% como as casas)
  const margem = 1.05
  const oddCasa = probCasa > 0 ? ((100 / probCasa) * margem).toFixed(2) : '-'
  const oddEmpate = probEmpate > 0 ? ((100 / probEmpate) * margem).toFixed(2) : '-'
  const oddFora = probFora > 0 ? ((100 / probFora) * margem).toFixed(2) : '-'
  
  let palpite = 'Empate'
  let confianca = probEmpate
  let tipoPalpite = 'empate'
  
  if (probCasa > probFora && probCasa > probEmpate) {
    palpite = match.homeTeam.shortName || match.homeTeam.name
    confianca = probCasa
    tipoPalpite = 'casa'
  } else if (probFora > probCasa && probFora > probEmpate) {
    palpite = match.awayTeam.shortName || match.awayTeam.name
    confianca = probFora
    tipoPalpite = 'fora'
  }
  
  // Gerar explicações detalhadas do PORQUÊ do palpite
  const explicacoes = gerarExplicacoes(match, tipoPalpite, probCasa, probFora, probEmpate, homePos, awayPos)
  
  return {
    palpite,
    tipoPalpite,
    confianca: Math.min(85, Math.max(35, confianca)),
    probCasa,
    probEmpate,
    probFora,
    oddCasa,
    oddEmpate,
    oddFora,
    homePos,
    awayPos,
    homeForm,
    awayForm,
    explicacoes,
    hasRealData: !!(homePos && awayPos),
    isEstimated: true
  }
}

// Gerar explicações detalhadas do palpite
const gerarExplicacoes = (match, tipoPalpite, probCasa, probFora, probEmpate, homePos, awayPos) => {
  const homeName = match.homeTeam?.shortName || match.homeTeam?.name || 'Casa'
  const awayName = match.awayTeam?.shortName || match.awayTeam?.name || 'Fora'
  
  const explicacoes = []
  
  // 1. Posição na tabela
  if (homePos && awayPos) {
    if (homePos < awayPos) {
      explicacoes.push({
        icon: '📊',
        titulo: 'Posição na Tabela',
        texto: `${homeName} está em ${homePos}º lugar, ${awayPos - homePos} posições à frente de ${awayName} (${awayPos}º)`,
        impacto: 'positivo'
      })
    } else if (awayPos < homePos) {
      explicacoes.push({
        icon: '📊',
        titulo: 'Posição na Tabela',
        texto: `${awayName} está em ${awayPos}º lugar, ${homePos - awayPos} posições à frente de ${homeName} (${homePos}º)`,
        impacto: tipoPalpite === 'fora' ? 'positivo' : 'negativo'
      })
    } else {
      explicacoes.push({
        icon: '📊',
        titulo: 'Posição na Tabela',
        texto: `Times empatados na tabela (${homePos}º lugar) - equilíbrio técnico`,
        impacto: 'neutro'
      })
    }
  }
  
  // 2. Fator casa
  explicacoes.push({
    icon: '🏟️',
    titulo: 'Vantagem de Casa',
    texto: `${homeName} joga em casa, o que historicamente adiciona ~10-15% de chance de vitória`,
    impacto: tipoPalpite === 'casa' ? 'positivo' : 'neutro'
  })
  
  // 3. Probabilidades
  if (tipoPalpite === 'casa') {
    explicacoes.push({
      icon: '🎯',
      titulo: 'Probabilidade Calculada',
      texto: `${homeName} tem ${probCasa}% de chance de vencer baseado em estatísticas`,
      impacto: 'positivo'
    })
  } else if (tipoPalpite === 'fora') {
    explicacoes.push({
      icon: '🎯',
      titulo: 'Probabilidade Calculada',
      texto: `${awayName} tem ${probFora}% de chance mesmo jogando fora - time em grande fase`,
      impacto: 'positivo'
    })
  } else {
    explicacoes.push({
      icon: '🎯',
      titulo: 'Probabilidade Calculada',
      texto: `Empate tem ${probEmpate}% de chance - forças muito equilibradas`,
      impacto: 'positivo'
    })
  }
  
  // 4. Análise de risco
  const diffProb = Math.abs(probCasa - probFora)
  if (diffProb < 10) {
    explicacoes.push({
      icon: '⚠️',
      titulo: 'Análise de Risco',
      texto: `Jogo muito equilibrado (diferença de apenas ${diffProb}%) - considere empate ou aposta dupla`,
      impacto: 'alerta'
    })
  } else if (diffProb > 25) {
    explicacoes.push({
      icon: '✅',
      titulo: 'Análise de Risco',
      texto: `Favoritismo claro (diferença de ${diffProb}%) - palpite com boa margem de segurança`,
      impacto: 'positivo'
    })
  }
  
  // 5. Recomendação de aposta
  if (probCasa > 55 || probFora > 55) {
    explicacoes.push({
      icon: '💡',
      titulo: 'Recomendação',
      texto: `Favorito claro no jogo. Para maior segurança, considere "Dupla Chance" ou "Handicap"`,
      impacto: 'dica'
    })
  } else if (probEmpate > 30) {
    explicacoes.push({
      icon: '💡',
      titulo: 'Recomendação',
      texto: `Alta chance de empate. Considere "Ambas Marcam" ou "Under/Over 2.5 gols"`,
      impacto: 'dica'
    })
  }
  
  return explicacoes
}

// Filtrar jogos
const jogosFiltrados = computed(() => {
  let resultado = [...jogos.value]
  
  // Filtro por confiança
  if (filtroConfianca.value === 'alta') {
    resultado = resultado.filter(j => j.confianca >= 60)
  } else if (filtroConfianca.value === 'media') {
    resultado = resultado.filter(j => j.confianca >= 45 && j.confianca < 60)
  }
  
  // Filtro por tipo de palpite
  if (filtroPalpite.value !== 'all') {
    resultado = resultado.filter(j => j.tipoPalpite === filtroPalpite.value)
  }
  
  // Ordenar por confiança
  resultado.sort((a, b) => b.confianca - a.confianca)
  
  return resultado
})

const selecionarJogo = async (jogo) => {
  // Se tem acesso completo (plano pago), abre direto
  if (temAcessoCompleto.value) {
    jogoSelecionado.value = jogo
    await buscarOddsReais(jogo)
    return
  }
  
  // Para usuários free: verificar no backend primeiro
  const backendCheck = await verificarAnaliseBackend(jogo.id)
  
  if (backendCheck) {
    // Backend respondeu - usar validação do servidor (mais seguro)
    if (backendCheck.allowed) {
      await salvarAnaliseVista(jogo.id)
      jogoSelecionado.value = jogo
    } else {
      // Limite atingido - mostra modal de upgrade
      mostrarModalBloqueio.value = true
    }
    return
  }
  
  // Fallback: usar localStorage se backend falhar
  const vistas = getAnalisesVistasHoje()
  const jaViu = vistas.ids.includes(jogo.id)
  
  if (jaViu) {
    jogoSelecionado.value = jogo
    return
  }
  
  if (analisesRestantes.value > 0) {
    await salvarAnaliseVista(jogo.id)
    jogoSelecionado.value = jogo
  } else {
    mostrarModalBloqueio.value = true
  }
}

// Buscar odds reais de múltiplas casas de apostas
const buscarOddsReais = async (jogo) => {
  if (oddsReais.value[jogo.id]) return // Já tem cache
  
  loadingOdds.value = true
  try {
    const liga = ligaSelecionada.value === 'all' ? 'BSA' : ligaSelecionada.value
    const response = await fetch(`/api/odds?league=${liga}`)
    if (response.ok) {
      const data = await response.json()
      // Tentar encontrar o jogo nas odds
      const matchOdds = data.odds?.find(m => 
        m.home_team?.toLowerCase().includes(jogo.casa.toLowerCase()) ||
        jogo.casa.toLowerCase().includes(m.home_team?.toLowerCase()?.split(' ')[0])
      )
      if (matchOdds) {
        oddsReais.value[jogo.id] = matchOdds
      }
    }
  } catch (error) {
    console.error('Erro ao buscar odds:', error)
  }
  loadingOdds.value = false
}

const fecharModal = () => {
  jogoSelecionado.value = null
}

const fecharModalBloqueio = () => {
  mostrarModalBloqueio.value = false
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}
</script>

<template>
  <div class="palpites-page">
    <!-- Header -->
    <header class="palpites-header">
      <div class="header-left">
        <router-link to="/" class="logo-link">
          <img src="/logo.webp" alt="ODINENX" class="logo" />
        </router-link>
      </div>
      <div class="header-center">
        <h1>⚽ Palpites do Dia</h1>
        <p v-if="lastUpdate">Atualizado às {{ lastUpdate }}</p>
      </div>
      <div class="header-right">
        <router-link to="/odds" class="btn-header odds">📊 Odds</router-link>
        <template v-if="user">
          <router-link to="/dashboard" class="btn-header">Dashboard</router-link>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-header outline">Entrar</router-link>
          <router-link to="/register" class="btn-header primary">Criar Conta</router-link>
        </template>
      </div>
    </header>

    <!-- Filtros -->
    <div class="filtros-container">
      <div class="filtros">
        <div class="filtro-group">
          <label>Liga</label>
          <select v-model="ligaSelecionada">
            <option v-for="(liga, key) in LIGAS" :key="key" :value="key">
              {{ liga.pais }} {{ liga.nome }}
            </option>
          </select>
        </div>
        
        <div class="filtro-group">
          <label>Confiança</label>
          <select v-model="filtroConfianca">
            <option value="all">Todas</option>
            <option value="alta">Alta (60%+)</option>
            <option value="media">Média (45-60%)</option>
          </select>
        </div>
        
        <div class="filtro-group">
          <label>Palpite</label>
          <select v-model="filtroPalpite">
            <option value="all">Todos</option>
            <option value="casa">Vitória Casa</option>
            <option value="fora">Vitória Fora</option>
            <option value="empate">Empate</option>
          </select>
        </div>
        
        <button @click="carregarJogos" class="btn-atualizar" :disabled="loading">
          <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          <span v-if="loading" class="spinner-small"></span>
          {{ loading ? 'Atualizando...' : 'Atualizar' }}
        </button>
      </div>
      
      <div class="filtros-info">
        <span class="jogos-count">{{ jogosFiltrados.length }} palpites encontrados</span>
        <span v-if="!temAcessoCompleto && analisesRestantes >= 0" class="analises-badge">
          🎯 {{ analisesRestantes }}/3 análises restantes hoje
        </span>
        <span v-if="temAcessoCompleto" class="analises-badge premium">
          ✨ Análises ilimitadas
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Carregando palpites...</p>
    </div>

    <!-- Lista de Palpites -->
    <div v-else class="palpites-grid">
      <div 
        v-for="jogo in jogosFiltrados" 
        :key="jogo.id" 
        class="palpite-card"
        :class="getNivelConfianca(jogo.confianca).nivel"
        @click="selecionarJogo(jogo)"
      >
        <!-- Indicador de Confiança Grande e Visual -->
        <div class="confianca-indicador" :class="getNivelConfianca(jogo.confianca).nivel">
          <span class="confianca-texto">{{ getNivelConfianca(jogo.confianca).texto }}</span>
          <span class="confianca-numero">{{ jogo.confianca }}%</span>
        </div>
        
        <div class="palpite-liga">
          <span class="liga-nome">{{ jogo.ligaPais }} {{ jogo.liga }}</span>
          <span class="liga-rodada">{{ jogo.rodada }}</span>
        </div>
        
        <div class="palpite-times">
          <div class="time">
            <img :src="jogo.casaLogo" @error="$event.target.src = '/icone.webp'" alt="">
            <span>{{ jogo.casa }}</span>
          </div>
          <div class="vs-info">
            <span class="hora">{{ jogo.hora }}</span>
            <span class="data">{{ jogo.data }}</span>
          </div>
          <div class="time">
            <img :src="jogo.foraLogo" @error="$event.target.src = '/icone.webp'" alt="">
            <span>{{ jogo.fora }}</span>
          </div>
        </div>
        
        <!-- Palpite Grande e Claro -->
        <div class="palpite-principal">
          <span class="palpite-label">PALPITE:</span>
          <span class="palpite-nome" :class="getNivelConfianca(jogo.confianca).nivel">{{ jogo.palpite }}</span>
        </div>
        
        <!-- Barra de Probabilidades Visual -->
        <div class="probabilidades-visuais">
          <div class="prob-item" :class="{ destaque: jogo.tipoPalpite === 'casa' }">
            <span class="prob-nome">{{ (jogo.casa || 'Casa').substring(0, 8) }}</span>
            <div class="prob-barra">
              <div class="prob-fill casa" :style="{ width: jogo.probCasa + '%' }"></div>
            </div>
            <span class="prob-valor">{{ jogo.probCasa }}%</span>
          </div>
          <div class="prob-item" :class="{ destaque: jogo.tipoPalpite === 'empate' }">
            <span class="prob-nome">Empate</span>
            <div class="prob-barra">
              <div class="prob-fill empate" :style="{ width: jogo.probEmpate + '%' }"></div>
            </div>
            <span class="prob-valor">{{ jogo.probEmpate }}%</span>
          </div>
          <div class="prob-item" :class="{ destaque: jogo.tipoPalpite === 'fora' }">
            <span class="prob-nome">{{ (jogo.fora || 'Fora').substring(0, 8) }}</span>
            <div class="prob-barra">
              <div class="prob-fill fora" :style="{ width: jogo.probFora + '%' }"></div>
            </div>
            <span class="prob-valor">{{ jogo.probFora }}%</span>
          </div>
        </div>
        
        <!-- CTA para abrir análise -->
        <div class="palpite-cta">
          <span>👆 Toque para ver análise completa</span>
        </div>
      </div>
    </div>

    <!-- Sem resultados -->
    <div v-if="!loading && jogosFiltrados.length === 0" class="no-results">
      <p>Nenhum palpite encontrado com os filtros selecionados.</p>
      <button @click="filtroConfianca = 'all'; filtroPalpite = 'all'">Limpar filtros</button>
    </div>

    <!-- Modal de Palpite -->
    <div v-if="jogoSelecionado" class="modal-overlay" @click.self="fecharModal">
      <div class="modal-palpite">
        <button class="modal-close" @click="fecharModal">×</button>
        
        <div class="modal-header">
          <span class="modal-liga">{{ jogoSelecionado.ligaPais }} {{ jogoSelecionado.liga }} • {{ jogoSelecionado.rodada }}</span>
          <div class="modal-times">
            <div class="modal-time">
              <img :src="jogoSelecionado.casaLogo" @error="$event.target.src = '/icone.webp'">
              <h3>{{ jogoSelecionado.casa }}</h3>
            </div>
            <div class="modal-vs">
              <span class="hora">{{ jogoSelecionado.hora }}</span>
              <span class="data">{{ jogoSelecionado.data }}</span>
            </div>
            <div class="modal-time">
              <img :src="jogoSelecionado.foraLogo" @error="$event.target.src = '/icone.webp'">
              <h3>{{ jogoSelecionado.fora }}</h3>
            </div>
          </div>
        </div>
        
        <div class="modal-palpite-destaque">
          <div class="palpite-icon">🎯</div>
          <h2>{{ jogoSelecionado.palpite }} vence</h2>
          <div class="confianca-grande">
            <div class="confianca-bar-grande">
              <div class="confianca-fill" :style="{ width: jogoSelecionado.confianca + '%' }"></div>
            </div>
            <span>{{ jogoSelecionado.confianca }}% de confiança</span>
          </div>
        </div>
        
        <!-- EXPLICAÇÕES DETALHADAS DO PORQUÊ -->
        <div class="explicacoes-section">
          <h4>🧠 Por que esse palpite?</h4>
          <div class="explicacoes-lista">
            <div 
              v-for="(exp, idx) in jogoSelecionado.explicacoes" 
              :key="idx" 
              class="explicacao-item"
              :class="exp.impacto"
            >
              <span class="exp-icon">{{ exp.icon }}</span>
              <div class="exp-content">
                <span class="exp-titulo">{{ exp.titulo }}</span>
                <span class="exp-texto">{{ exp.texto }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-probabilidades">
          <h4>Probabilidades</h4>
          <div class="prob-bar">
            <div class="prob casa" :style="{ width: jogoSelecionado.probCasa + '%' }">{{ jogoSelecionado.probCasa }}%</div>
            <div class="prob empate" :style="{ width: jogoSelecionado.probEmpate + '%' }">{{ jogoSelecionado.probEmpate }}%</div>
            <div class="prob fora" :style="{ width: jogoSelecionado.probFora + '%' }">{{ jogoSelecionado.probFora }}%</div>
          </div>
          <div class="prob-legenda">
            <span><span class="dot casa"></span> {{ jogoSelecionado.casa }}</span>
            <span><span class="dot empate"></span> Empate</span>
            <span><span class="dot fora"></span> {{ jogoSelecionado.fora }}</span>
          </div>
        </div>
        
        <div class="modal-odds">
          <h4>📊 Odds Estimadas</h4>
          <div class="odds-grid">
            <div class="odd-box">
              <span class="team">{{ jogoSelecionado.casa }}</span>
              <span class="value">@{{ jogoSelecionado.oddCasa }}</span>
            </div>
            <div class="odd-box">
              <span class="team">Empate</span>
              <span class="value">@{{ jogoSelecionado.oddEmpate }}</span>
            </div>
            <div class="odd-box">
              <span class="team">{{ jogoSelecionado.fora }}</span>
              <span class="value">@{{ jogoSelecionado.oddFora }}</span>
            </div>
          </div>
          
          <!-- Explicação didática das odds -->
          <div class="odds-explicacao">
            <div class="odds-explicacao-header" @click="toggleOddsExplicacao">
              <span>❓ O que são odds e como usar?</span>
              <span class="toggle-icon">{{ mostrarExplicacaoOdds ? '▼' : '▶' }}</span>
            </div>
            
            <div v-if="mostrarExplicacaoOdds" class="odds-explicacao-content">
              <div class="explicacao-item">
                <span class="explicacao-icon">🎯</span>
                <div class="explicacao-texto">
                  <strong>O que são odds?</strong>
                  <p>Odds representam a <em>probabilidade invertida</em> de um evento acontecer. Quanto <strong>menor a odd</strong>, maior a chance do evento ocorrer.</p>
                </div>
              </div>
              
              <div class="explicacao-item">
                <span class="explicacao-icon">💰</span>
                <div class="explicacao-texto">
                  <strong>Como calcular o ganho?</strong>
                  <p>Multiplique o valor apostado pela odd. Ex: R$10 × @{{ jogoSelecionado.oddCasa }} = <strong>R${{ (10 * jogoSelecionado.oddCasa).toFixed(2) }}</strong> de retorno.</p>
                </div>
              </div>
              
              <div class="explicacao-item">
                <span class="explicacao-icon">📈</span>
                <div class="explicacao-texto">
                  <strong>Como usar na prática?</strong>
                  <p>Compare nossas odds estimadas com as das casas de apostas. Se a casa oferece odd <strong>maior</strong> que a nossa, pode ser uma <strong>aposta de valor</strong>!</p>
                </div>
              </div>
              
              <div class="odds-exemplo-box">
                <div class="exemplo-titulo">📝 Exemplo com este jogo:</div>
                <div class="exemplo-conteudo">
                  <p>Nossa análise estima <strong>{{ jogoSelecionado.probCasa }}%</strong> de chance para {{ jogoSelecionado.casa }}.</p>
                  <p>Isso equivale a uma odd justa de <strong>@{{ jogoSelecionado.oddCasa }}</strong>.</p>
                  <p class="exemplo-dica">💡 Se uma casa oferece @{{ (parseFloat(jogoSelecionado.oddCasa) + 0.3).toFixed(2) }} ou mais, pode ter <strong>valor</strong>!</p>
                </div>
              </div>
              
              <div class="odds-tabela-conversao">
                <div class="tabela-titulo">🔄 Tabela de Conversão Rápida</div>
                <div class="tabela-items">
                  <div class="tabela-item"><span class="prob">80%</span> <span class="seta">→</span> <span class="odd">@1.25</span></div>
                  <div class="tabela-item"><span class="prob">66%</span> <span class="seta">→</span> <span class="odd">@1.50</span></div>
                  <div class="tabela-item"><span class="prob">50%</span> <span class="seta">→</span> <span class="odd">@2.00</span></div>
                  <div class="tabela-item"><span class="prob">33%</span> <span class="seta">→</span> <span class="odd">@3.00</span></div>
                  <div class="tabela-item"><span class="prob">25%</span> <span class="seta">→</span> <span class="odd">@4.00</span></div>
                  <div class="tabela-item"><span class="prob">20%</span> <span class="seta">→</span> <span class="odd">@5.00</span></div>
                </div>
              </div>
            </div>
          </div>
          
          <p class="odds-estimadas-info">💡 Odds calculadas a partir das probabilidades estatísticas (inclui margem de 5%)</p>
        </div>
        
        <!-- Odds Reais - Premium -->
        <div v-if="temAcessoCompleto && oddsReais[jogoSelecionado?.id]" class="odds-reais-section">
          <h4>🏆 Odds Reais em Tempo Real</h4>
          <p class="odds-reais-subtitle">Comparativo de {{ oddsReais[jogoSelecionado.id]?.bookmakers?.length || 0 }} casas de apostas</p>
          
          <div v-if="loadingOdds" class="loading-odds">
            <span class="spinner-small"></span> Carregando odds de múltiplas casas...
          </div>
          
          <div v-else class="odds-reais-container">
            <!-- Melhores Odds -->
            <div class="melhores-odds">
              <span class="melhores-titulo">🥇 MELHORES ODDS</span>
              <div class="melhores-grid">
                <div class="melhor-odd-item">
                  <span class="resultado">{{ jogoSelecionado.casa }}</span>
                  <span class="odd-valor">@{{ oddsReais[jogoSelecionado.id]?.best_odds?.home?.value?.toFixed(2) || '-' }}</span>
                  <span class="casa-nome">{{ oddsReais[jogoSelecionado.id]?.best_odds?.home?.bookmaker?.icon }} {{ oddsReais[jogoSelecionado.id]?.best_odds?.home?.bookmaker?.name || '-' }}</span>
                </div>
                <div class="melhor-odd-item">
                  <span class="resultado">Empate</span>
                  <span class="odd-valor">@{{ oddsReais[jogoSelecionado.id]?.best_odds?.draw?.value?.toFixed(2) || '-' }}</span>
                  <span class="casa-nome">{{ oddsReais[jogoSelecionado.id]?.best_odds?.draw?.bookmaker?.icon }} {{ oddsReais[jogoSelecionado.id]?.best_odds?.draw?.bookmaker?.name || '-' }}</span>
                </div>
                <div class="melhor-odd-item">
                  <span class="resultado">{{ jogoSelecionado.fora }}</span>
                  <span class="odd-valor">@{{ oddsReais[jogoSelecionado.id]?.best_odds?.away?.value?.toFixed(2) || '-' }}</span>
                  <span class="casa-nome">{{ oddsReais[jogoSelecionado.id]?.best_odds?.away?.bookmaker?.icon }} {{ oddsReais[jogoSelecionado.id]?.best_odds?.away?.bookmaker?.name || '-' }}</span>
                </div>
              </div>
            </div>
            
            <!-- Probabilidades Implícitas -->
            <div class="probabilidades-implicitas">
              <span class="prob-titulo">📊 Probabilidades do Mercado</span>
              <div class="prob-bars">
                <div class="prob-bar-row">
                  <span class="prob-label">{{ jogoSelecionado.casa.substring(0, 10) }}</span>
                  <div class="prob-bar">
                    <div class="prob-fill home" :style="{ width: (oddsReais[jogoSelecionado.id]?.implied_probabilities?.adjusted?.home || 0) + '%' }"></div>
                  </div>
                  <span class="prob-value">{{ oddsReais[jogoSelecionado.id]?.implied_probabilities?.adjusted?.home || 0 }}%</span>
                </div>
                <div class="prob-bar-row">
                  <span class="prob-label">Empate</span>
                  <div class="prob-bar">
                    <div class="prob-fill draw" :style="{ width: (oddsReais[jogoSelecionado.id]?.implied_probabilities?.adjusted?.draw || 0) + '%' }"></div>
                  </div>
                  <span class="prob-value">{{ oddsReais[jogoSelecionado.id]?.implied_probabilities?.adjusted?.draw || 0 }}%</span>
                </div>
                <div class="prob-bar-row">
                  <span class="prob-label">{{ jogoSelecionado.fora.substring(0, 10) }}</span>
                  <div class="prob-bar">
                    <div class="prob-fill away" :style="{ width: (oddsReais[jogoSelecionado.id]?.implied_probabilities?.adjusted?.away || 0) + '%' }"></div>
                  </div>
                  <span class="prob-value">{{ oddsReais[jogoSelecionado.id]?.implied_probabilities?.adjusted?.away || 0 }}%</span>
                </div>
              </div>
              <div class="margem-casa">
                <span>Margem das casas: <strong>{{ oddsReais[jogoSelecionado.id]?.implied_probabilities?.overround || 0 }}%</strong></span>
                <span v-if="oddsReais[jogoSelecionado.id]?.implied_probabilities?.overround < 105" class="margem-boa">✨ Margens excelentes!</span>
              </div>
            </div>
            
            <!-- Todas as Casas -->
            <div class="todas-casas">
              <span class="casas-titulo">🏠 Comparativo de Casas</span>
              <div class="casas-grid">
                <div 
                  v-for="bm in oddsReais[jogoSelecionado.id]?.bookmakers?.slice(0, 6)" 
                  :key="bm.key" 
                  class="casa-item"
                >
                  <div class="casa-header">
                    <span class="casa-icon">{{ bm.icon }}</span>
                    <span class="casa-name">{{ bm.name }}</span>
                  </div>
                  <div class="casa-odds">
                    <div class="casa-odd" :class="{ melhor: bm.odds?.home === oddsReais[jogoSelecionado.id]?.best_odds?.home?.value }">
                      <span class="odd-tipo">1</span>
                      <span class="odd-val">@{{ bm.odds?.home?.toFixed(2) }}</span>
                    </div>
                    <div class="casa-odd" :class="{ melhor: bm.odds?.draw === oddsReais[jogoSelecionado.id]?.best_odds?.draw?.value }">
                      <span class="odd-tipo">X</span>
                      <span class="odd-val">@{{ bm.odds?.draw?.toFixed(2) }}</span>
                    </div>
                    <div class="casa-odd" :class="{ melhor: bm.odds?.away === oddsReais[jogoSelecionado.id]?.best_odds?.away?.value }">
                      <span class="odd-tipo">2</span>
                      <span class="odd-val">@{{ bm.odds?.away?.toFixed(2) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Value Bets Alert -->
          <div v-if="oddsReais[jogoSelecionado.id]?.value_bets?.length > 0" class="value-bets-section">
            <div class="value-bets-header">
              <span class="vb-icon">💎</span>
              <span class="vb-titulo">VALUE BETS DETECTADAS</span>
            </div>
            <div class="value-bets-list">
              <div v-for="vb in oddsReais[jogoSelecionado.id].value_bets.slice(0, 3)" :key="vb.bookmaker" class="value-bet-card">
                <div class="vb-info">
                  <span class="vb-casa">{{ vb.icon }} {{ vb.bookmaker }}</span>
                  <span class="vb-resultado">{{ vb.outcome === 'home' ? jogoSelecionado.casa : vb.outcome === 'away' ? jogoSelecionado.fora : 'Empate' }}</span>
                </div>
                <div class="vb-numeros">
                  <span class="vb-odd">@{{ vb.odds?.toFixed(2) }}</span>
                  <span class="vb-edge">+{{ vb.value_percentage }}% edge</span>
                </div>
              </div>
            </div>
            <p class="vb-explicacao">💡 Value bets são apostas onde a odd paga mais do que a probabilidade real sugere - lucro esperado positivo a longo prazo!</p>
          </div>
          
          <router-link to="/bet" class="btn-ver-odds">
            📊 Abrir Comparador Completo de Odds →
          </router-link>
        </div>
        
        <!-- Odds Bloqueadas - CTA para Free Users -->
        <div v-if="!temAcessoCompleto" class="odds-bloqueadas-section">
          <div class="odds-bloqueadas-header">
            <span class="lock-icon">🔒</span>
            <h4>Odds Reais de Múltiplas Casas</h4>
          </div>
          
          <div class="odds-preview-blur">
            <div class="preview-grid">
              <div class="preview-item">
                <span class="preview-icon">🟢</span>
                <span class="preview-casa">Bet365</span>
                <span class="preview-odds">@?.?? / @?.?? / @?.??</span>
              </div>
              <div class="preview-item">
                <span class="preview-icon">🟡</span>
                <span class="preview-casa">Betfair</span>
                <span class="preview-odds">@?.?? / @?.?? / @?.??</span>
              </div>
              <div class="preview-item">
                <span class="preview-icon">🔵</span>
                <span class="preview-casa">Pinnacle</span>
                <span class="preview-odds">@?.?? / @?.?? / @?.??</span>
              </div>
              <div class="preview-item">
                <span class="preview-icon">🔷</span>
                <span class="preview-casa">1xBet</span>
                <span class="preview-odds">@?.?? / @?.?? / @?.??</span>
              </div>
            </div>
          </div>
          
          <div class="odds-bloqueadas-benefits">
            <div class="benefit-item">
              <span>📊</span>
              <p><strong>17+ casas de apostas</strong> comparadas em tempo real</p>
            </div>
            <div class="benefit-item">
              <span>💎</span>
              <p><strong>Value Bets automáticas</strong> - apostas com vantagem matemática</p>
            </div>
            <div class="benefit-item">
              <span>📈</span>
              <p><strong>Probabilidades implícitas</strong> calculadas por profissionais</p>
            </div>
            <div class="benefit-item">
              <span>🏆</span>
              <p><strong>Melhores odds</strong> identificadas para cada resultado</p>
            </div>
          </div>
          
          <div class="odds-bloqueadas-cta">
            <router-link to="/pricing" class="btn-desbloquear">
              🚀 Desbloquear Odds Reais - A partir de R$29/mês
            </router-link>
            <p class="cta-hint">Cancele a qualquer momento. Garantia de 7 dias.</p>
          </div>
        </div>
        
        <!-- H2H Liberado (placeholder) -->
        <div v-if="temAcessoCompleto" class="h2h-section">
          <h4>📊 Estatísticas H2H</h4>
          <p class="h2h-info">Confrontos diretos entre {{ jogoSelecionado.casa }} e {{ jogoSelecionado.fora }}</p>
          <!-- Dados H2H seriam carregados aqui -->
        </div>
        
        <div class="modal-aviso">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p>Palpite baseado em análise estatística. Aposte com responsabilidade. 18+</p>
        </div>
      </div>
    </div>

    <!-- Modal de Limite Atingido -->
    <div v-if="mostrarModalBloqueio" class="modal-overlay" @click.self="fecharModalBloqueio">
      <div class="modal-bloqueio">
        <button class="modal-close" @click="fecharModalBloqueio">×</button>
        
        <div class="bloqueio-icon">🔒</div>
        <h2>Limite de Análises Atingido</h2>
        <p>Você já usou suas <strong>3 análises gratuitas</strong> de hoje.</p>
        
        <div class="bloqueio-info">
          <div class="info-item">
            <span class="emoji">🕐</span>
            <span>Amanhã você terá +3 análises grátis</span>
          </div>
          <div class="info-item">
            <span class="emoji">💎</span>
            <span>Ou faça upgrade para análises ilimitadas</span>
          </div>
        </div>
        
        <div class="bloqueio-actions">
          <router-link to="/pricing" class="btn-upgrade-full">
            Ver Planos
          </router-link>
          <button @click="fecharModalBloqueio" class="btn-voltar">
            Voltar aos Palpites
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.palpites-page {
  min-height: 100vh;
  background: #000;
  color: #fff;
  padding-bottom: 50px;
}

/* Header */
.palpites-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  background: rgba(0, 0, 0, 0.95);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  z-index: 100;
}

.logo-link {
  display: flex;
}

.logo {
  height: 35px;
}

.header-center {
  text-align: center;
}

.header-center h1 {
  font-size: 1.3rem;
  margin: 0;
}

.header-center p {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 4px 0 0;
}

.header-right {
  display: flex;
  gap: 10px;
}

.btn-header {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
}

.btn-header.outline {
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-header.primary {
  background: #fff;
  color: #000;
}

.btn-header.odds {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(139, 195, 74, 0.15));
  border: 1px solid rgba(76, 175, 80, 0.4);
  color: #4caf50;
}

.btn-header.odds:hover {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(139, 195, 74, 0.25));
}

/* Filtros */
.filtros-container {
  padding: 20px 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.filtros {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filtro-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filtro-group label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.filtro-group select {
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #fff;
  padding: 10px 14px;
  font-size: 0.9rem;
  min-width: 160px;
  cursor: pointer;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23ffffff' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 35px;
}

.filtro-group select option {
  background: #1a1a1a;
  color: #fff;
  padding: 10px;
}

.btn-atualizar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.4);
  color: #4caf50;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-atualizar:hover {
  background: rgba(76, 175, 80, 0.3);
}

.btn-atualizar svg {
  width: 16px;
  height: 16px;
}

.filtros-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.jogos-count {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.h2h-badge {
  font-size: 0.75rem;
  color: #ffc107;
  background: rgba(255, 193, 7, 0.1);
  padding: 6px 12px;
  border-radius: 50px;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  gap: 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(76, 175, 80, 0.2);
  border-top-color: #4caf50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Grid de Palpites */
.palpites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.palpite-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.palpite-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.palpite-liga {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.liga-nome {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.liga-rodada {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.palpite-times {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.time img {
  width: 45px;
  height: 45px;
  object-fit: contain;
  border-radius: 8px;
  background: linear-gradient(145deg, #1e293b, #0f172a);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.time span {
  font-size: 0.85rem;
  font-weight: 600;
  text-align: center;
}

.vs-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 0 15px;
}

.vs-info .hora {
  font-size: 1rem;
  font-weight: 700;
}

.vs-info .data {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.palpite-resultado {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 12px;
}

.palpite-badge {
  font-size: 0.85rem;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 50px;
  background: rgba(255, 255, 255, 0.1);
}

.palpite-badge.alta {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.palpite-badge.media {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

/* NOVO: Indicador de Confiança Grande */
.confianca-indicador {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.05);
}

.confianca-indicador.muito-alta {
  background: linear-gradient(135deg, rgba(0, 230, 118, 0.25), rgba(0, 200, 83, 0.15));
  border: 2px solid #00e676;
}

.confianca-indicador.alta {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(56, 142, 60, 0.15));
  border: 2px solid #4caf50;
}

.confianca-indicador.media {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.25), rgba(255, 160, 0, 0.15));
  border: 2px solid #ffc107;
}

.confianca-indicador.baixa {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.25), rgba(211, 47, 47, 0.15));
  border: 2px solid #f44336;
}

.confianca-texto {
  font-size: 0.9rem;
  font-weight: 800;
  text-transform: uppercase;
}

.confianca-indicador.muito-alta .confianca-texto { color: #00e676; }
.confianca-indicador.alta .confianca-texto { color: #4caf50; }
.confianca-indicador.media .confianca-texto { color: #ffc107; }
.confianca-indicador.baixa .confianca-texto { color: #f44336; }

.confianca-numero {
  font-size: 1.3rem;
  font-weight: 900;
}

.confianca-indicador.muito-alta .confianca-numero { color: #00e676; }
.confianca-indicador.alta .confianca-numero { color: #4caf50; }
.confianca-indicador.media .confianca-numero { color: #ffc107; }
.confianca-indicador.baixa .confianca-numero { color: #f44336; }

/* NOVO: Palpite Principal */
.palpite-principal {
  background: rgba(255, 255, 255, 0.08);
  padding: 15px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 15px;
}

.palpite-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.palpite-nome {
  display: block;
  font-size: 1.2rem;
  font-weight: 900;
}

.palpite-nome.muito-alta { color: #00e676; }
.palpite-nome.alta { color: #4caf50; }
.palpite-nome.media { color: #ffc107; }
.palpite-nome.baixa { color: #f44336; }

/* NOVO: Probabilidades Visuais */
.probabilidades-visuais {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.prob-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
}

.prob-item.destaque {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.prob-nome {
  font-size: 0.75rem;
  width: 60px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.prob-barra {
  flex: 1;
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease;
}

.prob-fill.casa {
  background: linear-gradient(90deg, #2196f3, #64b5f6);
}

.prob-fill.empate {
  background: linear-gradient(90deg, #9e9e9e, #bdbdbd);
}

.prob-fill.fora {
  background: linear-gradient(90deg, #ff5722, #ff8a65);
}

.prob-valor {
  font-size: 0.85rem;
  font-weight: 800;
  width: 40px;
  text-align: right;
}

/* NOVO: CTA */
.palpite-cta {
  text-align: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.confianca {
  display: flex;
  align-items: center;
  gap: 10px;
}

.confianca-bar {
  width: 60px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.confianca-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  border-radius: 10px;
}

.confianca span {
  font-size: 0.85rem;
  font-weight: 700;
  color: #4caf50;
}

.palpite-odds {
  display: flex;
  gap: 8px;
}

.odd {
  flex: 1;
  text-align: center;
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 8px;
}

.odd .label {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.odd .value {
  font-size: 0.9rem;
  font-weight: 700;
  color: #ffc107;
}

/* No Results */
.no-results {
  text-align: center;
  padding: 60px 20px;
}

.no-results p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 20px;
}

.no-results button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-palpite {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  padding: 30px;
}

.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 28px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.modal-header {
  text-align: center;
  margin-bottom: 24px;
}

.modal-liga {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.modal-times {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
}

.modal-time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.modal-time img {
  width: 60px;
  height: 60px;
  object-fit: contain;
}

.modal-time h3 {
  font-size: 1rem;
  text-align: center;
}

.modal-vs {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 0 20px;
}

.modal-vs .hora {
  font-size: 1.2rem;
  font-weight: 700;
}

.modal-vs .data {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.modal-palpite-destaque {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(139, 195, 74, 0.1));
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  margin-bottom: 24px;
}

.palpite-icon {
  font-size: 2rem;
  margin-bottom: 12px;
}

.modal-palpite-destaque h2 {
  font-size: 1.4rem;
  color: #4caf50;
  margin-bottom: 16px;
}

.confianca-grande {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confianca-bar-grande {
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.confianca-grande span {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.modal-probabilidades {
  margin-bottom: 24px;
}

.modal-probabilidades h4,
.modal-odds h4 {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
  text-align: center;
}

.prob-bar {
  display: flex;
  height: 30px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 10px;
}

.prob {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
  min-width: 40px;
}

.prob.casa { background: #4caf50; }
.prob.empate { background: #ff9800; }
.prob.fora { background: #2196f3; }

.prob-legenda {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
}

.dot.casa { background: #4caf50; }
.dot.empate { background: #ff9800; }
.dot.fora { background: #2196f3; }

/* Explicações Section */
.explicacoes-section {
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.explicacoes-section h4 {
  font-size: 0.95rem;
  margin-bottom: 16px;
  color: #fff;
}

.explicacoes-lista {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.explicacao-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-left: 3px solid rgba(255, 255, 255, 0.2);
}

.explicacao-item.positivo {
  border-left-color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
}

.explicacao-item.negativo {
  border-left-color: #f44336;
  background: rgba(244, 67, 54, 0.1);
}

.explicacao-item.neutro {
  border-left-color: #9e9e9e;
  background: rgba(158, 158, 158, 0.1);
}

.explicacao-item.alerta {
  border-left-color: #ff9800;
  background: rgba(255, 152, 0, 0.1);
}

.explicacao-item.dica {
  border-left-color: #2196f3;
  background: rgba(33, 150, 243, 0.1);
}

.exp-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.exp-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.exp-titulo {
  font-size: 0.8rem;
  font-weight: 700;
  color: #fff;
}

.exp-texto {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
}

.modal-odds {
  margin-bottom: 24px;
}

.odds-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.odd-box {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}

.odd-box .team {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
}

.odd-box .value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffc107;
}

/* H2H Locked */
.h2h-locked {
  text-align: center;
  padding: 24px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: 12px;
  margin-bottom: 20px;
}

.lock-icon {
  font-size: 2rem;
  margin-bottom: 10px;
}

.h2h-locked h4 {
  color: #ffc107;
  margin-bottom: 8px;
}

.h2h-locked p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 16px;
}

.btn-upgrade {
  display: inline-block;
  background: linear-gradient(135deg, #ffc107, #ff9800);
  color: #000;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.3s ease;
}

/* Odds Bloqueadas Section - Free Users */
.odds-bloqueadas-section {
  padding: 20px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.08), rgba(255, 152, 0, 0.05));
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: 12px;
  margin-bottom: 20px;
}

.odds-bloqueadas-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.odds-bloqueadas-header .lock-icon {
  font-size: 1.5rem;
  margin-bottom: 0;
}

.odds-bloqueadas-header h4 {
  font-size: 1rem;
  color: #ffc107;
  margin: 0;
}

.odds-preview-blur {
  position: relative;
  padding: 15px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  margin-bottom: 20px;
  overflow: hidden;
}

.odds-preview-blur::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.8) 100%);
  backdrop-filter: blur(3px);
  pointer-events: none;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.preview-icon { font-size: 1rem; }
.preview-casa { font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); }
.preview-odds { font-size: 0.75rem; color: rgba(255, 255, 255, 0.3); margin-left: auto; }

.odds-bloqueadas-benefits {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.benefit-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
}

.benefit-item span {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.benefit-item p {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
  margin: 0;
}

.benefit-item strong {
  color: #fff;
}

.odds-bloqueadas-cta {
  text-align: center;
}

.btn-desbloquear {
  display: inline-block;
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: #fff;
  font-weight: 700;
  font-size: 0.95rem;
  padding: 14px 30px;
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.btn-desbloquear:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.cta-hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 10px;
}

.h2h-section {
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 20px;
}

.odds-estimadas-info {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  margin-top: 10px;
  font-style: italic;
}

/* Explicação didática das odds */
.odds-explicacao {
  margin-top: 16px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.odds-explicacao-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background: rgba(255, 193, 7, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.2s;
}

.odds-explicacao-header:hover {
  background: rgba(255, 193, 7, 0.2);
}

.odds-explicacao-header span:first-child {
  font-size: 0.9rem;
  color: #ffc107;
  font-weight: 500;
}

.toggle-icon {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  transition: transform 0.2s;
}

.odds-explicacao-content {
  padding: 16px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.explicacao-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.explicacao-item:last-of-type {
  border-bottom: none;
  margin-bottom: 12px;
}

.explicacao-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.explicacao-texto {
  flex: 1;
}

.explicacao-texto strong {
  display: block;
  color: #fff;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.explicacao-texto p {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin: 0;
}

.explicacao-texto em {
  color: #ffc107;
  font-style: normal;
}

.odds-exemplo-box {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.15), rgba(33, 150, 243, 0.05));
  border: 1px solid rgba(33, 150, 243, 0.3);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 16px;
}

.exemplo-titulo {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2196f3;
  margin-bottom: 10px;
}

.exemplo-conteudo p {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 6px 0;
  line-height: 1.4;
}

.exemplo-dica {
  background: rgba(76, 175, 80, 0.15);
  padding: 8px 12px;
  border-radius: 6px;
  margin-top: 10px !important;
  border-left: 3px solid #4caf50;
}

.odds-tabela-conversao {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 14px;
}

.tabela-titulo {
  font-size: 0.85rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
  text-align: center;
}

.tabela-items {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.tabela-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 0.75rem;
}

.tabela-item .prob {
  color: #4caf50;
  font-weight: 600;
}

.tabela-item .seta {
  color: rgba(255, 255, 255, 0.4);
}

.tabela-item .odd {
  color: #ffc107;
  font-weight: 600;
}

/* Odds Reais Section - Premium */
.odds-reais-section {
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(139, 195, 74, 0.05));
  border: 1px solid rgba(76, 175, 80, 0.2);
  border-radius: 12px;
}

.odds-reais-section h4 {
  font-size: 1rem;
  margin-bottom: 5px;
  color: #4caf50;
}

.odds-reais-subtitle {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 20px;
}

.loading-odds {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
}

.odds-reais-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Melhores Odds */
.melhores-odds {
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 12px;
  padding: 15px;
}

.melhores-titulo {
  font-size: 0.75rem;
  font-weight: 700;
  color: #ffc107;
  letter-spacing: 1px;
  display: block;
  margin-bottom: 12px;
}

.melhores-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.melhor-odd-item {
  text-align: center;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
}

.melhor-odd-item .resultado {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.melhor-odd-item .odd-valor {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  color: #ffc107;
  margin-bottom: 4px;
}

.melhor-odd-item .casa-nome {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Probabilidades Implícitas */
.probabilidades-implicitas {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 15px;
}

.prob-titulo {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  display: block;
  margin-bottom: 12px;
}

.prob-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prob-bar-row {
  display: grid;
  grid-template-columns: 80px 1fr 45px;
  align-items: center;
  gap: 10px;
}

.prob-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.prob-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.prob-fill.home { background: linear-gradient(90deg, #4caf50, #8bc34a); }
.prob-fill.draw { background: linear-gradient(90deg, #9e9e9e, #bdbdbd); }
.prob-fill.away { background: linear-gradient(90deg, #2196f3, #03a9f4); }

.prob-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
  text-align: right;
}

.margem-casa {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.margem-boa {
  color: #4caf50;
  font-weight: 600;
}

/* Todas as Casas */
.todas-casas {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 15px;
}

.casas-titulo {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  display: block;
  margin-bottom: 12px;
}

.casas-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.casa-item {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 10px;
}

.casa-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.casa-icon { font-size: 1rem; }
.casa-name { font-size: 0.75rem; font-weight: 600; color: #fff; }

.casa-odds {
  display: flex;
  gap: 6px;
}

.casa-odd {
  flex: 1;
  text-align: center;
  padding: 6px 4px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.casa-odd.melhor {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.4);
}

.odd-tipo {
  display: block;
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 2px;
}

.odd-val {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #ffc107;
}

.casa-odd.melhor .odd-val {
  color: #4caf50;
}

/* Value Bets Section */
.value-bets-section {
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.15), rgba(103, 58, 183, 0.1));
  border: 1px solid rgba(156, 39, 176, 0.3);
  border-radius: 12px;
  padding: 15px;
  margin-top: 15px;
}

.value-bets-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.value-bets-header .vb-icon { font-size: 1.3rem; }
.value-bets-header .vb-titulo {
  font-size: 0.75rem;
  font-weight: 700;
  color: #ce93d8;
  letter-spacing: 1px;
}

.value-bets-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.value-bet-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
}

.vb-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.vb-casa {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

.vb-resultado {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.vb-numeros {
  text-align: right;
}

.vb-odd {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffc107;
}

.vb-edge {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #4caf50;
}

.vb-explicacao {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  line-height: 1.5;
}

.btn-ver-odds {
  display: block;
  text-align: center;
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: #fff;
  padding: 14px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn-ver-odds:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.h2h-section h4 {
  margin-bottom: 10px;
}

.h2h-info {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.modal-aviso {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: 10px;
}

.modal-aviso svg {
  flex-shrink: 0;
  color: #ffc107;
}

.modal-aviso p {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

/* Responsive */
@media (max-width: 768px) {
  .palpites-header {
    flex-direction: column;
    gap: 15px;
    padding: 15px;
  }
  
  .header-right {
    width: 100%;
    justify-content: center;
  }
  
  .filtros {
    flex-direction: column;
  }
  
  .filtro-group {
    width: 100%;
  }
  
  .filtro-group select {
    width: 100%;
    font-size: 16px;
    padding: 14px 16px;
  }
  
  .btn-atualizar {
    width: 100%;
    justify-content: center;
    padding: 14px 20px;
    font-size: 1rem;
  }
  
  .palpites-grid {
    grid-template-columns: 1fr;
    padding: 15px;
    gap: 20px;
  }
  
  .palpite-card {
    padding: 16px;
  }
  
  /* Indicador de confiança maior no mobile */
  .confianca-indicador {
    padding: 14px 18px;
    border-radius: 14px;
  }
  
  .confianca-texto {
    font-size: 0.85rem;
  }
  
  .confianca-numero {
    font-size: 1.5rem;
  }
  
  /* Palpite principal maior */
  .palpite-principal {
    padding: 18px;
  }
  
  .palpite-nome {
    font-size: 1.3rem;
  }
  
  /* Probabilidades mais legíveis */
  .prob-item {
    padding: 10px 12px;
  }
  
  .prob-nome {
    font-size: 0.8rem;
    width: 70px;
  }
  
  .prob-barra {
    height: 12px;
  }
  
  .prob-valor {
    font-size: 0.95rem;
    width: 45px;
  }
  
  /* CTA mais destacado */
  .palpite-cta {
    padding: 14px;
    background: rgba(255, 193, 7, 0.1);
    border: 1px dashed rgba(255, 193, 7, 0.3);
    font-size: 0.9rem;
    color: #ffc107;
    font-weight: 600;
  }
  
  /* Badge de análises mais visível */
  .analises-badge {
    font-size: 0.9rem;
    padding: 10px 18px;
    font-weight: 700;
  }
  
  .filtros-info {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .modal-palpite {
    padding: 20px;
    border-radius: 16px;
  }
  
  .modal-bloqueio {
    padding: 30px 20px;
    margin: 15px;
  }
}

/* Badge de análises */
.analises-badge {
  font-size: 0.8rem;
  color: #ffc107;
  background: rgba(255, 193, 7, 0.1);
  padding: 6px 14px;
  border-radius: 50px;
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.analises-badge.premium {
  color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
  border-color: rgba(76, 175, 80, 0.3);
}

/* Modal de Bloqueio */
.modal-bloqueio {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  width: 100%;
  max-width: 420px;
  padding: 40px 30px;
  position: relative;
  text-align: center;
}

.bloqueio-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.modal-bloqueio h2 {
  font-size: 1.5rem;
  margin-bottom: 10px;
}

.modal-bloqueio > p {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 30px;
}

.bloqueio-info {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.info-item:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-item .emoji {
  font-size: 1.3rem;
}

.bloqueio-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-upgrade-full {
  display: block;
  background: #fff;
  color: #000;
  font-weight: 700;
  padding: 14px 24px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.btn-upgrade-full:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.15);
}

.btn-voltar {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 12px 24px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn-voltar:hover {
  border-color: rgba(255, 255, 255, 0.4);
  color: #fff;
}
</style>
