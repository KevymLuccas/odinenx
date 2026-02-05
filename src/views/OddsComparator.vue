<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const oddsData = ref([])
const selectedMatch = ref(null)
const lastUpdate = ref(null)
const error = ref(null)
const isDemo = ref(false)
const mostrarBloqueio = ref(false)

// Filtros
const ligaSelecionada = ref('BSA')
const filtroValue = ref('all') // all, value-only

// Ligas disponíveis
const LIGAS = {
  BSA: { nome: 'Brasileirão', code: 'BSA', pais: '🇧🇷' },
  PL: { nome: 'Premier League', code: 'PL', pais: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  PD: { nome: 'La Liga', code: 'PD', pais: '🇪🇸' },
  SA: { nome: 'Serie A', code: 'SA', pais: '🇮🇹' },
  BL1: { nome: 'Bundesliga', code: 'BL1', pais: '🇩🇪' },
  FL1: { nome: 'Ligue 1', code: 'FL1', pais: '🇫🇷' },
  CL: { nome: 'Champions League', code: 'CL', pais: '🏆' }
}

// Verificar acesso
const temAcessoCompleto = computed(() => {
  if (!subscription.value) return false
  const planId = subscription.value.plan || 'free'
  return planId !== 'free'
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user
  if (user.value) {
    subscription.value = await getSubscriptionStatus(user.value.id)
  }
  
  // Verificar se tem acesso (apenas planos pagos)
  if (!temAcessoCompleto.value) {
    mostrarBloqueio.value = true
    loading.value = false
    return
  }
  
  await carregarOdds()
})

watch(ligaSelecionada, () => carregarOdds())

const carregarOdds = async () => {
  // Bloquear se não tem acesso
  if (!temAcessoCompleto.value) {
    mostrarBloqueio.value = true
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    // API premium com odds reais de múltiplas casas
    const apiUrl = `/api/odds?league=${ligaSelecionada.value}&region=br`
    
    const response = await fetch(apiUrl)
    
    if (!response.ok) {
      throw new Error('Erro ao carregar odds')
    }
    
    const data = await response.json()
    oddsData.value = data.odds || []
    isDemo.value = data.demo || data.source === 'estimated'
    lastUpdate.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    
  } catch (err) {
    console.error('Erro:', err)
    error.value = 'Erro ao carregar odds. Tente novamente.'
  }
  
  loading.value = false
}

// Filtrar partidas
const partidasFiltradas = computed(() => {
  let resultado = [...oddsData.value]
  
  if (filtroValue.value === 'value-only') {
    resultado = resultado.filter(m => m.value_bets && m.value_bets.length > 0)
  }
  
  // Ordenar por número de value bets
  resultado.sort((a, b) => (b.value_bets?.length || 0) - (a.value_bets?.length || 0))
  
  return resultado
})

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

const formatTime = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

const getValueClass = (value) => {
  if (value >= 10) return 'value-hot'
  if (value >= 5) return 'value-good'
  return 'value-normal'
}

const abrirDetalhes = (match) => {
  selectedMatch.value = match
}

const fecharDetalhes = () => {
  selectedMatch.value = null
}

// Gerar explicações detalhadas para cada partida
const gerarExplicacoesOdds = (match) => {
  if (!match) return []
  
  const explicacoes = []
  const prob = match.implied_probabilities || {}
  const stats = match.stats || {}
  const valueBets = match.value_bets || []
  const overround = stats.overround || 0
  
  // 1. Análise do Favorito
  const probHome = prob.home || 0
  const probAway = prob.away || 0
  const probDraw = prob.draw || 0
  
  let favorito = ''
  let probFavorito = 0
  if (probHome > probAway && probHome > probDraw) {
    favorito = match.home_team
    probFavorito = probHome
  } else if (probAway > probHome && probAway > probDraw) {
    favorito = match.away_team
    probFavorito = probAway
  } else {
    favorito = 'Empate'
    probFavorito = probDraw
  }
  
  if (probFavorito > 50) {
    explicacoes.push({
      icon: '🎯',
      titulo: 'Favorito Claro',
      descricao: `${favorito} é o favorito com ${probFavorito.toFixed(0)}% de probabilidade implícita. As casas de apostas consideram este resultado mais provável baseado em forma recente, histórico e qualidade do elenco.`,
      tipo: 'positivo'
    })
  } else if (probFavorito > 35) {
    explicacoes.push({
      icon: '⚖️',
      titulo: 'Jogo Equilibrado',
      descricao: `Probabilidades próximas indicam incerteza. O resultado mais provável (${favorito}) tem apenas ${probFavorito.toFixed(0)}% de chance. Jogos assim são arriscados mas podem ter boas odds.`,
      tipo: 'neutro'
    })
  } else {
    explicacoes.push({
      icon: '🎲',
      titulo: 'Alta Imprevisibilidade',
      descricao: `Nenhum resultado tem probabilidade dominante. O mais provável (${favorito}) tem ${probFavorito.toFixed(0)}%. Muita variação entre casas indica incerteza no mercado.`,
      tipo: 'alerta'
    })
  }
  
  // 2. Análise do Overround (margem das casas)
  if (overround > 0) {
    if (overround < 105) {
      explicacoes.push({
        icon: '✨',
        titulo: 'Margens Excelentes',
        descricao: `Overround de ${overround.toFixed(1)}% é muito baixo! Casas de apostas estão oferecendo odds muito justas. Ótimo momento para apostar neste jogo.`,
        tipo: 'positivo'
      })
    } else if (overround < 110) {
      explicacoes.push({
        icon: '👍',
        titulo: 'Margens Aceitáveis',
        descricao: `Overround de ${overround.toFixed(1)}% está na média do mercado. As odds são justas, mas não excepcionais. Aposte se a análise indicar oportunidade.`,
        tipo: 'neutro'
      })
    } else {
      explicacoes.push({
        icon: '⚠️',
        titulo: 'Margens Altas',
        descricao: `Overround de ${overround.toFixed(1)}% indica que casas estão cobrando margem alta. Considere esperar odds melhores ou buscar em outras casas.`,
        tipo: 'alerta'
      })
    }
  }
  
  // 3. Análise de Value Bets
  if (valueBets.length > 0) {
    const melhorValue = valueBets[0]
    const outcomeName = melhorValue.outcome === 'home' ? match.home_team : 
                        melhorValue.outcome === 'away' ? match.away_team : 'Empate'
    explicacoes.push({
      icon: '💎',
      titulo: 'Value Bet Detectada!',
      descricao: `${melhorValue.bookmaker} oferece ${outcomeName} a @${melhorValue.odds?.toFixed(2)} com ${melhorValue.value_percentage}% de value. A odd paga mais do que a probabilidade real sugere - apostas assim geram lucro a longo prazo.`,
      tipo: 'positivo'
    })
    
    if (valueBets.length > 1) {
      explicacoes.push({
        icon: '🔥',
        titulo: `${valueBets.length} Value Bets Encontradas`,
        descricao: `Múltiplas value bets indicam divergência entre casas. Isso acontece quando o mercado ainda não convergiu ou há informação assimétrica. Boa oportunidade!`,
        tipo: 'positivo'
      })
    }
  } else {
    explicacoes.push({
      icon: '❌',
      titulo: 'Sem Value Bets',
      descricao: `Nenhuma odd oferece valor positivo neste momento. As casas precificaram bem este jogo. Não apostar pode ser a melhor decisão quando não há edge.`,
      tipo: 'neutro'
    })
  }
  
  // 4. Análise do Spread entre casas
  const spread = stats.spread || {}
  const maxSpread = Math.max(spread.home || 0, spread.away || 0, spread.draw || 0)
  
  if (maxSpread > 0.5) {
    explicacoes.push({
      icon: '📊',
      titulo: 'Alta Variação entre Casas',
      descricao: `Diferença de até ${maxSpread.toFixed(2)} entre odds das casas. Compare sempre antes de apostar! Pequenas diferenças podem impactar muito seu lucro a longo prazo.`,
      tipo: 'dica'
    })
  } else if (maxSpread > 0) {
    explicacoes.push({
      icon: '📈',
      titulo: 'Odds Estáveis',
      descricao: `Pouca variação entre casas (${maxSpread.toFixed(2)}). O mercado está em consenso sobre as probabilidades. Escolha a casa que preferir.`,
      tipo: 'neutro'
    })
  }
  
  // 5. Dica de apostas
  explicacoes.push({
    icon: '💡',
    titulo: 'Dica de Apostas',
    descricao: valueBets.length > 0 
      ? `Aposte apenas o que pode perder. Value bets são vantajosas a longo prazo, mas resultados individuais são imprevisíveis. Gestão de banca é essencial.`
      : `Sem value bets não significa que não pode apostar, mas suas chances de lucro a longo prazo são menores. Aposte por diversão, não por expectativa de lucro.`,
    tipo: 'dica'
  })
  
  return explicacoes
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}
</script>

<template>
  <div class="odds-page">
    <!-- BLOQUEIO PARA FREE USERS -->
    <div v-if="mostrarBloqueio" class="bloqueio-overlay">
      <div class="bloqueio-modal">
        <div class="bloqueio-icon">🔒</div>
        <h2>Área Exclusiva para Assinantes</h2>
        <p class="bloqueio-desc">
          O <strong>Comparador de Odds</strong> com dados em tempo real de <strong>17+ casas de apostas</strong> 
          é uma funcionalidade exclusiva dos planos <strong>Pro</strong> e <strong>Elite</strong>.
        </p>
        
        <div class="bloqueio-features">
          <div class="feature-item">
            <span class="feature-icon">📊</span>
            <div>
              <strong>17+ Casas de Apostas</strong>
              <p>Bet365, Betfair, Pinnacle, 1xBet e muito mais</p>
            </div>
          </div>
          <div class="feature-item">
            <span class="feature-icon">💎</span>
            <div>
              <strong>Value Bets Automáticas</strong>
              <p>Identificamos apostas com valor positivo em tempo real</p>
            </div>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📈</span>
            <div>
              <strong>Probabilidades Implícitas</strong>
              <p>Análise estatística profissional das odds</p>
            </div>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <div>
              <strong>Explicações Detalhadas</strong>
              <p>Entenda o porquê de cada recomendação</p>
            </div>
          </div>
        </div>
        
        <div class="bloqueio-planos">
          <div class="plano-card pro">
            <span class="plano-tag">MAIS POPULAR</span>
            <h3>Pro ⭐</h3>
            <div class="plano-preco">R$ 49,90<span>/mês</span></div>
            <ul>
              <li>✅ Odds em tempo real</li>
              <li>✅ Value bets ilimitadas</li>
              <li>✅ Palpites ilimitados</li>
              <li>✅ Análises completas</li>
            </ul>
          </div>
          <div class="plano-card elite">
            <h3>Elite 👑</h3>
            <div class="plano-preco">R$ 99,90<span>/mês</span></div>
            <ul>
              <li>✅ Tudo do Pro</li>
              <li>✅ Alertas personalizados</li>
              <li>✅ Paper Trading</li>
              <li>✅ Suporte prioritário</li>
            </ul>
          </div>
        </div>
        
        <div class="bloqueio-actions">
          <router-link to="/pricing" class="btn-upgrade">
            🚀 Ver Planos e Assinar
          </router-link>
          <router-link to="/palpites" class="btn-palpites">
            ← Voltar para Palpites (Gratuito)
          </router-link>
        </div>
        
        <p class="bloqueio-hint">
          💡 <strong>Dica:</strong> Usuários gratuitos podem ver até 3 palpites por dia em /palpites
        </p>
      </div>
    </div>
    
    <!-- CONTEÚDO PRINCIPAL (apenas para assinantes) -->
    <template v-if="!mostrarBloqueio">
    <!-- Header -->
    <header class="odds-header">
      <div class="header-left">
        <router-link to="/" class="logo-link">
          <img src="/logo.webp" alt="ODINENX" class="logo" />
        </router-link>
      </div>
      <div class="header-center">
        <h1>📊 Odds em Tempo Real</h1>
        <p v-if="lastUpdate">Atualizado às {{ lastUpdate }}</p>
      </div>
      <div class="header-right">
        <template v-if="user">
          <router-link to="/dashboard" class="btn-header">Dashboard</router-link>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-header outline">Entrar</router-link>
          <router-link to="/register" class="btn-header primary">Criar Conta</router-link>
        </template>
      </div>
    </header>

    <!-- Banner Premium Ativo -->
    <div class="premium-active-banner">
      <span>✨</span>
      <p><strong>Acesso Premium Ativo!</strong> Você tem acesso a odds reais de 17+ casas de apostas.</p>
    </div>

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
          <label>Filtro</label>
          <select v-model="filtroValue">
            <option value="all">Todas Partidas</option>
            <option value="value-only">Apenas Value Bets</option>
          </select>
        </div>
        
        <button @click="carregarOdds" class="btn-atualizar" :disabled="loading">
          <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          <span v-if="loading" class="spinner-small"></span>
          {{ loading ? 'Atualizando...' : 'Atualizar Odds' }}
        </button>
      </div>
      
      <div class="filtros-info">
        <span class="partidas-count">{{ partidasFiltradas.length }} partidas encontradas</span>
        <span class="premium-badge">
          ✨ Acesso completo ativo
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Carregando odds de múltiplas casas...</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="carregarOdds">Tentar novamente</button>
    </div>

    <!-- Lista de Partidas -->
    <div v-else class="odds-grid">
      <div 
        v-for="match in partidasFiltradas" 
        :key="match.id" 
        class="odds-card"
        :class="{ 'has-value': match.value_bets?.length > 0 }"
        @click="abrirDetalhes(match)"
      >
        <!-- Header do Card -->
        <div class="card-header">
          <span class="liga-badge">{{ match.sport_title }}</span>
          <span class="data-hora">{{ formatDate(match.commence_time) }} • {{ formatTime(match.commence_time) }}</span>
        </div>
        
        <!-- Times -->
        <div class="times-row">
          <div class="time home">
            <span class="time-nome">{{ match.home_team }}</span>
          </div>
          <span class="vs">VS</span>
          <div class="time away">
            <span class="time-nome">{{ match.away_team }}</span>
          </div>
        </div>
        
        <!-- Melhores Odds -->
        <div class="best-odds-section">
          <h4>🏆 Melhores Odds</h4>
          <div class="best-odds-grid">
            <div class="best-odd">
              <span class="outcome">Casa</span>
              <span class="odd-value">@{{ match.best_odds?.home?.value?.toFixed(2) || '-' }}</span>
              <span class="bookmaker">{{ match.best_odds?.home?.bookmaker?.icon }} {{ match.best_odds?.home?.bookmaker?.name || '-' }}</span>
            </div>
            <div class="best-odd">
              <span class="outcome">Empate</span>
              <span class="odd-value">@{{ match.best_odds?.draw?.value?.toFixed(2) || '-' }}</span>
              <span class="bookmaker">{{ match.best_odds?.draw?.bookmaker?.icon }} {{ match.best_odds?.draw?.bookmaker?.name || '-' }}</span>
            </div>
            <div class="best-odd">
              <span class="outcome">Fora</span>
              <span class="odd-value">@{{ match.best_odds?.away?.value?.toFixed(2) || '-' }}</span>
              <span class="bookmaker">{{ match.best_odds?.away?.bookmaker?.icon }} {{ match.best_odds?.away?.bookmaker?.name || '-' }}</span>
            </div>
          </div>
        </div>
        
        <!-- Probabilidades -->
        <div class="probabilities-section">
          <h4>📈 Probabilidades Implícitas</h4>
          <div class="prob-bars">
            <div class="prob-bar-item">
              <span class="label">{{ match.home_team.substring(0, 10) }}</span>
              <div class="bar">
                <div class="fill home" :style="{ width: match.implied_probabilities?.adjusted?.home + '%' }"></div>
              </div>
              <span class="value">{{ match.implied_probabilities?.adjusted?.home }}%</span>
            </div>
            <div class="prob-bar-item">
              <span class="label">Empate</span>
              <div class="bar">
                <div class="fill draw" :style="{ width: match.implied_probabilities?.adjusted?.draw + '%' }"></div>
              </div>
              <span class="value">{{ match.implied_probabilities?.adjusted?.draw }}%</span>
            </div>
            <div class="prob-bar-item">
              <span class="label">{{ match.away_team.substring(0, 10) }}</span>
              <div class="bar">
                <div class="fill away" :style="{ width: match.implied_probabilities?.adjusted?.away + '%' }"></div>
              </div>
              <span class="value">{{ match.implied_probabilities?.adjusted?.away }}%</span>
            </div>
          </div>
          <div class="overround">
            <span>Margem da casa: <strong>{{ match.implied_probabilities?.overround }}%</strong></span>
          </div>
        </div>
        
        <!-- Value Bets -->
        <div v-if="match.value_bets?.length > 0" class="value-bets-section">
          <h4>🔥 Value Bets Encontradas</h4>
          <div class="value-bets-list">
            <div 
              v-for="(vb, idx) in match.value_bets.slice(0, 3)" 
              :key="idx" 
              class="value-bet-item"
              :class="getValueClass(vb.value_percentage)"
            >
              <span class="vb-icon">{{ vb.icon }}</span>
              <div class="vb-info">
                <span class="vb-bookmaker">{{ vb.bookmaker }}</span>
                <span class="vb-outcome">{{ vb.outcome === 'home' ? match.home_team : vb.outcome === 'away' ? match.away_team : 'Empate' }}</span>
              </div>
              <div class="vb-stats">
                <span class="vb-odd">@{{ vb.odds?.toFixed(2) }}</span>
                <span class="vb-value">+{{ vb.value_percentage }}% value</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Análise Rápida no Card -->
        <div class="analise-rapida">
          <div class="analise-resumo">
            <span class="analise-icon">{{ match.value_bets?.length > 0 ? '✅' : '⏸️' }}</span>
            <span class="analise-texto">
              {{ match.value_bets?.length > 0 
                ? `${match.value_bets.length} oportunidade(s) de value detectada(s)` 
                : 'Sem value bets no momento' }}
            </span>
          </div>
          <span class="analise-dica">💡 Clique para ver análise detalhada</span>
        </div>
        
        <!-- CTA -->
        <div class="card-cta">
          <span>👆 Ver todas as {{ match.bookmakers?.length || 0 }} casas de apostas</span>
        </div>
      </div>
    </div>

    <!-- Modal de Detalhes -->
    <div v-if="selectedMatch" class="modal-overlay" @click.self="fecharDetalhes">
      <div class="modal-odds">
        <button class="modal-close" @click="fecharDetalhes">×</button>
        
        <div class="modal-header">
          <span class="modal-liga">{{ selectedMatch.sport_title }}</span>
          <div class="modal-times">
            <h2>{{ selectedMatch.home_team }}</h2>
            <span class="modal-vs">VS</span>
            <h2>{{ selectedMatch.away_team }}</h2>
          </div>
          <span class="modal-date">{{ formatDate(selectedMatch.commence_time) }} às {{ formatTime(selectedMatch.commence_time) }}</span>
        </div>
        
        <!-- Tabela Comparativa de Odds -->
        <div class="odds-comparison">
          <h3>📊 Comparativo de Odds</h3>
          <div class="odds-table">
            <div class="table-header">
              <span class="col-bookmaker">Casa de Aposta</span>
              <span class="col-odd">{{ selectedMatch.home_team.substring(0, 8) }}</span>
              <span class="col-odd">Empate</span>
              <span class="col-odd">{{ selectedMatch.away_team.substring(0, 8) }}</span>
            </div>
            <div 
              v-for="bm in selectedMatch.bookmakers" 
              :key="bm.key" 
              class="table-row"
            >
              <span class="col-bookmaker">
                <span class="bm-icon">{{ bm.icon }}</span>
                {{ bm.name }}
              </span>
              <span class="col-odd" :class="{ best: bm.odds?.home === selectedMatch.best_odds?.home?.value }">
                @{{ bm.odds?.home?.toFixed(2) || '-' }}
              </span>
              <span class="col-odd" :class="{ best: bm.odds?.draw === selectedMatch.best_odds?.draw?.value }">
                @{{ bm.odds?.draw?.toFixed(2) || '-' }}
              </span>
              <span class="col-odd" :class="{ best: bm.odds?.away === selectedMatch.best_odds?.away?.value }">
                @{{ bm.odds?.away?.toFixed(2) || '-' }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Estatísticas Detalhadas -->
        <div class="detailed-stats">
          <h3>📈 Estatísticas Detalhadas</h3>
          <div class="stats-grid">
            <div class="stat-box">
              <span class="stat-label">Odds Justas (Casa)</span>
              <span class="stat-value">@{{ selectedMatch.implied_probabilities?.fair_odds?.home }}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Odds Justas (Empate)</span>
              <span class="stat-value">@{{ selectedMatch.implied_probabilities?.fair_odds?.draw }}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Odds Justas (Fora)</span>
              <span class="stat-value">@{{ selectedMatch.implied_probabilities?.fair_odds?.away }}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Spread Casa</span>
              <span class="stat-value">{{ selectedMatch.stats?.spread?.home }}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Spread Empate</span>
              <span class="stat-value">{{ selectedMatch.stats?.spread?.draw }}</span>
            </div>
            <div class="stat-box">
              <span class="stat-label">Spread Fora</span>
              <span class="stat-value">{{ selectedMatch.stats?.spread?.away }}</span>
            </div>
          </div>
        </div>
        
        <!-- Value Bets Completas -->
        <div v-if="selectedMatch.value_bets?.length > 0" class="all-value-bets">
          <h3>🔥 Todas as Value Bets</h3>
          <div class="value-bets-full">
            <div 
              v-for="(vb, idx) in selectedMatch.value_bets" 
              :key="idx" 
              class="value-bet-full"
              :class="getValueClass(vb.value_percentage)"
            >
              <div class="vb-header">
                <span class="vb-icon-big">{{ vb.icon }}</span>
                <span class="vb-name">{{ vb.bookmaker }}</span>
              </div>
              <div class="vb-details">
                <div class="vb-outcome-info">
                  <span class="vb-outcome-label">Resultado:</span>
                  <span class="vb-outcome-value">{{ vb.outcome === 'home' ? selectedMatch.home_team : vb.outcome === 'away' ? selectedMatch.away_team : 'Empate' }}</span>
                </div>
                <div class="vb-numbers">
                  <div class="vb-num">
                    <span class="label">Odd</span>
                    <span class="value">@{{ vb.odds?.toFixed(2) }}</span>
                  </div>
                  <div class="vb-num">
                    <span class="label">Prob. Implícita</span>
                    <span class="value">{{ vb.implied_prob }}%</span>
                  </div>
                  <div class="vb-num">
                    <span class="label">Prob. Justa</span>
                    <span class="value">{{ vb.fair_prob }}%</span>
                  </div>
                  <div class="vb-num value">
                    <span class="label">Value</span>
                    <span class="value">+{{ vb.value_percentage }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Análise e Explicações -->
        <div class="analise-explicativa">
          <h3>🧠 Por Que Esta Análise?</h3>
          <div class="explicacoes-grid">
            <div v-for="(exp, idx) in gerarExplicacoesOdds(selectedMatch)" :key="idx" class="explicacao-item" :class="exp.tipo">
              <span class="exp-icon">{{ exp.icon }}</span>
              <div class="exp-content">
                <span class="exp-titulo">{{ exp.titulo }}</span>
                <p class="exp-descricao">{{ exp.descricao }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Aviso -->
        <div class="modal-disclaimer">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p>Odds podem variar. Sempre confira na casa de apostas antes de apostar. Jogue com responsabilidade. 18+</p>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<style scoped>
.odds-page {
  min-height: 100vh;
  background: #000;
  color: #fff;
  padding-bottom: 50px;
}

/* Bloqueio para Free Users */
.bloqueio-overlay {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
}

.bloqueio-modal {
  background: rgba(20, 20, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  max-width: 700px;
  width: 100%;
  text-align: center;
}

.bloqueio-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.bloqueio-modal h2 {
  font-size: 1.8rem;
  margin-bottom: 15px;
  background: linear-gradient(135deg, #ffc107, #ff9800);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.bloqueio-desc {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  line-height: 1.6;
  margin-bottom: 30px;
}

.bloqueio-features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 30px;
  text-align: left;
}

.feature-item {
  display: flex;
  gap: 12px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.feature-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.feature-item strong {
  display: block;
  font-size: 0.9rem;
  color: #fff;
  margin-bottom: 4px;
}

.feature-item p {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.bloqueio-planos {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.plano-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  text-align: center;
  position: relative;
}

.plano-card.pro {
  border-color: rgba(76, 175, 80, 0.5);
  background: rgba(76, 175, 80, 0.05);
}

.plano-card.elite {
  border-color: rgba(255, 193, 7, 0.5);
  background: rgba(255, 193, 7, 0.05);
}

.plano-tag {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}

.plano-card h3 {
  font-size: 1.3rem;
  margin-bottom: 10px;
}

.plano-preco {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 15px;
}

.plano-preco span {
  font-size: 0.9rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
}

.plano-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}

.plano-card li {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  padding: 6px 0;
}

.bloqueio-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.btn-upgrade {
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: #fff;
  font-size: 1.1rem;
  font-weight: 700;
  padding: 16px 40px;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
}

.btn-upgrade:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(76, 175, 80, 0.4);
}

.btn-palpites {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  text-decoration: none;
  transition: color 0.3s ease;
}

.btn-palpites:hover {
  color: #fff;
}

.bloqueio-hint {
  margin-top: 25px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  padding: 15px;
  background: rgba(255, 193, 7, 0.1);
  border-radius: 10px;
  border: 1px solid rgba(255, 193, 7, 0.2);
}

/* Premium Active Banner */
.premium-active-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 30px;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.15), rgba(46, 125, 50, 0.1));
  border-bottom: 1px solid rgba(76, 175, 80, 0.3);
}

.premium-active-banner span { font-size: 1.2rem; }
.premium-active-banner p { font-size: 0.85rem; color: #4caf50; margin: 0; }

/* Header */
.odds-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(20px);
  z-index: 100;
}

.logo-link { display: flex; }
.logo { height: 35px; }

.header-center { text-align: center; }
.header-center h1 { font-size: 1.3rem; margin: 0; }
.header-center p { font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); margin: 4px 0 0; }

.header-right { display: flex; gap: 10px; }

.btn-header {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
}
.btn-header.outline { color: #fff; border: 1px solid rgba(255, 255, 255, 0.3); }
.btn-header.primary { background: #fff; color: #000; }

/* Demo Banner */
.demo-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 30px;
  background: linear-gradient(90deg, rgba(255, 193, 7, 0.15), rgba(255, 152, 0, 0.1));
  border-bottom: 1px solid rgba(255, 193, 7, 0.3);
}
.demo-banner span { font-size: 1.2rem; }
.demo-banner p { font-size: 0.85rem; color: #ffc107; }

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
}
.btn-atualizar svg { width: 16px; height: 16px; }

.filtros-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.partidas-count { font-size: 0.85rem; color: rgba(255, 255, 255, 0.7); }

.upgrade-badge {
  font-size: 0.75rem;
  color: #ffc107;
  background: rgba(255, 193, 7, 0.1);
  padding: 6px 12px;
  border-radius: 50px;
}

.premium-badge {
  font-size: 0.75rem;
  color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
  padding: 6px 12px;
  border-radius: 50px;
}

/* Loading & Error */
.loading-state, .error-state {
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

@keyframes spin { to { transform: rotate(360deg); } }

/* Grid */
.odds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  padding: 30px;
  max-width: 1600px;
  margin: 0 auto;
}

/* Card */
.odds-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.odds-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.odds-card.has-value {
  border-color: rgba(76, 175, 80, 0.3);
  background: rgba(76, 175, 80, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.liga-badge {
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 10px;
  border-radius: 20px;
}

.data-hora {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Times */
.times-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.time { flex: 1; text-align: center; }
.time-nome { font-size: 1rem; font-weight: 700; }
.vs { color: rgba(255, 255, 255, 0.3); font-size: 0.8rem; padding: 0 15px; }

/* Best Odds */
.best-odds-section {
  margin-bottom: 20px;
}

.best-odds-section h4, 
.probabilities-section h4,
.value-bets-section h4 {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 10px;
}

.best-odds-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.best-odd {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}

.best-odd .outcome {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.best-odd .odd-value {
  display: block;
  font-size: 1.2rem;
  font-weight: 800;
  color: #ffc107;
}

.best-odd .bookmaker {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 4px;
}

/* Probabilities */
.probabilities-section {
  margin-bottom: 20px;
}

.prob-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prob-bar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prob-bar-item .label {
  width: 80px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.prob-bar-item .bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.prob-bar-item .fill {
  height: 100%;
  border-radius: 4px;
}

.prob-bar-item .fill.home { background: linear-gradient(90deg, #2196f3, #64b5f6); }
.prob-bar-item .fill.draw { background: linear-gradient(90deg, #9e9e9e, #bdbdbd); }
.prob-bar-item .fill.away { background: linear-gradient(90deg, #ff5722, #ff8a65); }

.prob-bar-item .value {
  width: 40px;
  font-size: 0.8rem;
  font-weight: 700;
  text-align: right;
}

.overround {
  margin-top: 10px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

/* Value Bets */
.value-bets-section {
  margin-bottom: 15px;
}

.value-bets-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.value-bet-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.2);
  border-radius: 10px;
  padding: 10px 12px;
}

.value-bet-item.value-hot {
  background: rgba(255, 87, 34, 0.15);
  border-color: rgba(255, 87, 34, 0.3);
}

.value-bet-item.value-good {
  background: rgba(76, 175, 80, 0.15);
  border-color: rgba(76, 175, 80, 0.3);
}

.vb-icon { font-size: 1.2rem; }

.vb-info { flex: 1; }
.vb-bookmaker { display: block; font-size: 0.8rem; font-weight: 600; }
.vb-outcome { display: block; font-size: 0.7rem; color: rgba(255, 255, 255, 0.6); }

.vb-stats { text-align: right; }
.vb-odd { display: block; font-size: 1rem; font-weight: 700; color: #ffc107; }
.vb-value { display: block; font-size: 0.75rem; color: #4caf50; font-weight: 600; }

.value-bet-item.value-hot .vb-value { color: #ff5722; }

/* Análise Rápida no Card */
.analise-rapida {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(103, 58, 183, 0.1));
  border-radius: 10px;
  border: 1px solid rgba(156, 39, 176, 0.2);
}

.analise-resumo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.analise-icon {
  font-size: 1.1rem;
}

.analise-texto {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.analise-dica {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

/* CTA */
.card-cta {
  text-align: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-odds {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  width: 100%;
  max-width: 700px;
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
  margin-bottom: 30px;
}

.modal-liga {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.modal-times {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin: 15px 0;
}

.modal-times h2 { font-size: 1.3rem; }
.modal-vs { color: rgba(255, 255, 255, 0.3); }
.modal-date { font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); }

/* Odds Comparison Table */
.odds-comparison {
  margin-bottom: 25px;
}

.odds-comparison h3,
.detailed-stats h3,
.all-value-bets h3 {
  font-size: 0.9rem;
  margin-bottom: 15px;
}

.odds-table {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 1.5fr repeat(3, 1fr);
  gap: 10px;
  padding: 12px 15px;
  background: rgba(255, 255, 255, 0.05);
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
}

.table-row {
  display: grid;
  grid-template-columns: 1.5fr repeat(3, 1fr);
  gap: 10px;
  padding: 12px 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.2s;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.col-bookmaker {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.bm-icon { font-size: 1rem; }

.col-odd {
  text-align: center;
  font-size: 0.9rem;
  font-weight: 600;
}

.col-odd.best {
  color: #4caf50;
  font-weight: 800;
}

/* Detailed Stats */
.detailed-stats {
  margin-bottom: 25px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.stat-box {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}

.stat-box .stat-label {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.stat-box .stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffc107;
}

/* All Value Bets */
.all-value-bets {
  margin-bottom: 20px;
}

.value-bets-full {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.value-bet-full {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.2);
  border-radius: 12px;
  padding: 15px;
}

.value-bet-full.value-hot {
  background: rgba(255, 87, 34, 0.1);
  border-color: rgba(255, 87, 34, 0.2);
}

.vb-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.vb-icon-big { font-size: 1.5rem; }
.vb-name { font-size: 1rem; font-weight: 700; }

.vb-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vb-outcome-info {
  font-size: 0.85rem;
}

.vb-outcome-label { color: rgba(255, 255, 255, 0.6); }
.vb-outcome-value { font-weight: 600; margin-left: 8px; }

.vb-numbers {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.vb-num {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.vb-num .label {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.vb-num .value {
  font-size: 1rem;
  font-weight: 700;
}

.vb-num.value .value {
  color: #4caf50;
}

.value-bet-full.value-hot .vb-num.value .value {
  color: #ff5722;
}

/* Análise Explicativa */
.analise-explicativa {
  margin-top: 20px;
}

.analise-explicativa h3 {
  font-size: 1rem;
  margin-bottom: 15px;
  color: rgba(255, 255, 255, 0.9);
}

.explicacoes-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.explicacao-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border-left: 3px solid transparent;
}

.explicacao-item.positivo {
  border-left-color: #4caf50;
  background: rgba(76, 175, 80, 0.08);
}

.explicacao-item.negativo {
  border-left-color: #f44336;
  background: rgba(244, 67, 54, 0.08);
}

.explicacao-item.neutro {
  border-left-color: #2196f3;
  background: rgba(33, 150, 243, 0.08);
}

.explicacao-item.alerta {
  border-left-color: #ff9800;
  background: rgba(255, 152, 0, 0.08);
}

.explicacao-item.dica {
  border-left-color: #9c27b0;
  background: rgba(156, 39, 176, 0.08);
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
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.exp-descricao {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin: 0;
}

/* Disclaimer */
.modal-disclaimer {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: 10px;
}

.modal-disclaimer svg { flex-shrink: 0; color: #ffc107; }
.modal-disclaimer p { font-size: 0.75rem; color: rgba(255, 255, 255, 0.7); line-height: 1.5; }

/* Responsive */
@media (max-width: 768px) {
  .odds-header {
    flex-direction: column;
    gap: 15px;
    padding: 15px;
  }
  
  .filtros { flex-direction: column; }
  .filtro-group { width: 100%; }
  .filtro-group select { width: 100%; font-size: 16px; padding: 14px; }
  .btn-atualizar { width: 100%; justify-content: center; }
  
  .odds-grid {
    grid-template-columns: 1fr;
    padding: 15px;
  }
  
  .best-odds-grid { grid-template-columns: 1fr; }
  
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  
  .vb-numbers { grid-template-columns: repeat(2, 1fr); }
  
  .table-header, .table-row {
    grid-template-columns: 1.2fr repeat(3, 0.8fr);
    font-size: 0.75rem;
  }
  
  .modal-times { flex-direction: column; gap: 10px; }
  .modal-times h2 { font-size: 1.1rem; }
}
</style>
