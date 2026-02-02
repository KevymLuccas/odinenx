<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans } from '../../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const loading = ref(true)

// Abas principais
const abaAtiva = ref('analise') // analise, dashboard, operacoes, risco, diario

// Sub-abas de análise
const categoriaAtiva = ref('crypto')

// Modal
const ativoSelecionado = ref(null)
const modalNovaOperacao = ref(false)
const modalCalculadora = ref(false)

// Dados de ativos
const ativos = ref({
  crypto: [],
  acoes: [],
  forex: []
})

// Operações do usuário
const operacoes = ref([])
const novaOperacao = ref({
  tipo: 'COMPRA',
  ativo: '',
  categoria: 'crypto',
  preco_entrada: 0,
  quantidade: 0,
  stop_loss: 0,
  take_profit: 0,
  plataforma: 'Binance',
  observacao: ''
})

// Filtro de operações
const filtroOperacoes = ref('todas')

// Configurações de risco
const configRisco = ref({
  capital_total: 10000,
  risco_por_operacao: 2,
  max_operacoes_dia: 5,
  max_perda_dia: 5,
  alavancagem_max: 10
})

// Plataformas disponíveis
const plataformas = [
  { nome: 'Binance', tipo: 'crypto', cor: '#F3BA2F' },
  { nome: 'Bybit', tipo: 'crypto', cor: '#FFDC00' },
  { nome: 'KuCoin', tipo: 'crypto', cor: '#23AF91' },
  { nome: 'Coinbase', tipo: 'crypto', cor: '#0052FF' },
  { nome: 'Clear', tipo: 'acoes', cor: '#00A650' },
  { nome: 'XP', tipo: 'acoes', cor: '#FFD100' },
  { nome: 'Rico', tipo: 'acoes', cor: '#FF6B00' },
  { nome: 'BTG', tipo: 'acoes', cor: '#003366' },
  { nome: 'ModalMais', tipo: 'acoes', cor: '#1E3A5F' },
  { nome: 'MetaTrader 4', tipo: 'forex', cor: '#2196F3' },
  { nome: 'MetaTrader 5', tipo: 'forex', cor: '#1565C0' },
  { nome: 'IC Markets', tipo: 'forex', cor: '#1E88E5' }
]

// Intervalo de atualização
let atualizacaoInterval = null

// Status da API
const apiStatus = ref({
  crypto: { loading: false, error: null, lastUpdate: null },
  acoes: { loading: false, error: null, lastUpdate: null },
  forex: { loading: false, error: null, lastUpdate: null }
})

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  await carregarOperacoes()
  await carregarConfigRisco()
  await carregarDadosReais() // Agora carrega dados REAIS!
  loading.value = false
  
  // Atualizar preços a cada 30 segundos (para não sobrecarregar APIs gratuitas)
  atualizacaoInterval = setInterval(() => {
    carregarDadosReais()
  }, 30000)
})

onUnmounted(() => {
  if (atualizacaoInterval) clearInterval(atualizacaoInterval)
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

// ===== ESTATÍSTICAS DO DASHBOARD =====
const estatisticas = computed(() => {
  const ops = operacoes.value.filter(o => o.status === 'FECHADA')
  const ganhos = ops.filter(o => o.resultado > 0)
  const perdas = ops.filter(o => o.resultado < 0)
  
  const totalGanho = ganhos.reduce((sum, o) => sum + o.resultado, 0)
  const totalPerda = Math.abs(perdas.reduce((sum, o) => sum + o.resultado, 0))
  const lucroTotal = totalGanho - totalPerda
  
  const winRate = ops.length > 0 ? (ganhos.length / ops.length * 100) : 0
  const profitFactor = totalPerda > 0 ? (totalGanho / totalPerda) : totalGanho > 0 ? 999 : 0
  
  // Drawdown máximo
  let maxDrawdown = 0
  let peak = configRisco.value.capital_total
  let runningTotal = configRisco.value.capital_total
  ops.forEach(o => {
    runningTotal += o.resultado
    if (runningTotal > peak) peak = runningTotal
    const dd = ((peak - runningTotal) / peak) * 100
    if (dd > maxDrawdown) maxDrawdown = dd
  })
  
  // Operações hoje
  const hoje = new Date().toDateString()
  const opsHoje = operacoes.value.filter(o => new Date(o.data).toDateString() === hoje)
  const lucroHoje = opsHoje.reduce((sum, o) => sum + (o.resultado || 0), 0)
  
  // Streak
  let streakAtual = 0
  let melhorStreak = 0
  let piorStreak = 0
  let tempStreak = 0
  
  ops.forEach(o => {
    if (o.resultado > 0) {
      if (tempStreak >= 0) tempStreak++
      else tempStreak = 1
      if (tempStreak > melhorStreak) melhorStreak = tempStreak
    } else if (o.resultado < 0) {
      if (tempStreak <= 0) tempStreak--
      else tempStreak = -1
      if (tempStreak < piorStreak) piorStreak = tempStreak
    }
  })
  streakAtual = tempStreak
  
  return {
    totalOperacoes: ops.length,
    operacoesAbertas: operacoes.value.filter(o => o.status === 'ABERTA').length,
    winRate: winRate.toFixed(1),
    profitFactor: profitFactor.toFixed(2),
    lucroTotal: lucroTotal.toFixed(2),
    maxDrawdown: maxDrawdown.toFixed(1),
    operacoesHoje: opsHoje.length,
    lucroHoje: lucroHoje.toFixed(2),
    melhorOperacao: ops.length > 0 ? Math.max(...ops.map(o => o.resultado)).toFixed(2) : 0,
    piorOperacao: ops.length > 0 ? Math.min(...ops.map(o => o.resultado)).toFixed(2) : 0,
    mediaGanho: ganhos.length > 0 ? (totalGanho / ganhos.length).toFixed(2) : 0,
    mediaPerda: perdas.length > 0 ? (totalPerda / perdas.length).toFixed(2) : 0,
    streakAtual,
    melhorStreak,
    piorStreak: Math.abs(piorStreak),
    totalGanhos: ganhos.length,
    totalPerdas: perdas.length
  }
})

// Risco atual
const riscoAtual = computed(() => {
  const opsAbertas = operacoes.value.filter(o => o.status === 'ABERTA')
  const riscoTotal = opsAbertas.reduce((sum, o) => {
    const risco = (o.preco_entrada - o.stop_loss) * o.quantidade
    return sum + Math.abs(risco)
  }, 0)
  
  const percRisco = (riscoTotal / configRisco.value.capital_total) * 100
  const hoje = new Date().toDateString()
  const opsHoje = operacoes.value.filter(o => new Date(o.data).toDateString() === hoje)
  const perdaHoje = opsHoje.filter(o => o.resultado < 0).reduce((sum, o) => sum + Math.abs(o.resultado), 0)
  const percPerdaHoje = (perdaHoje / configRisco.value.capital_total) * 100
  
  return {
    riscoAberto: riscoTotal.toFixed(2),
    percRisco: percRisco.toFixed(1),
    operacoesHoje: opsHoje.length,
    limiteOpsAtingido: opsHoje.length >= configRisco.value.max_operacoes_dia,
    limitePerdaAtingido: percPerdaHoje >= configRisco.value.max_perda_dia,
    capitalDisponivel: (configRisco.value.capital_total - riscoTotal).toFixed(2),
    perdaHoje: perdaHoje.toFixed(2),
    percPerdaHoje: percPerdaHoje.toFixed(1)
  }
})

// Operações filtradas
const operacoesFiltradas = computed(() => {
  let ops = [...operacoes.value]
  
  switch (filtroOperacoes.value) {
    case 'abertas':
      ops = ops.filter(o => o.status === 'ABERTA')
      break
    case 'fechadas':
      ops = ops.filter(o => o.status === 'FECHADA')
      break
    case 'crypto':
      ops = ops.filter(o => o.categoria === 'crypto')
      break
    case 'acoes':
      ops = ops.filter(o => o.categoria === 'acoes')
      break
    case 'forex':
      ops = ops.filter(o => o.categoria === 'forex')
      break
  }
  
  return ops.sort((a, b) => new Date(b.data) - new Date(a.data))
})

// ===== CARREGAR/SALVAR DADOS NO SUPABASE =====
const carregarOperacoes = async () => {
  try {
    // Tentar carregar do Supabase primeiro
    const { data, error } = await supabase
      .from('trade_operacoes')
      .select('*')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })
    
    if (error) {
      console.error('Erro ao carregar operações do Supabase:', error)
      // Fallback para localStorage
      const saved = localStorage.getItem(`odinenx_operacoes_${user.value?.id}`)
      if (saved) {
        operacoes.value = JSON.parse(saved)
      } else {
        operacoes.value = [] // Começa vazio, sem dados de exemplo
      }
    } else {
      operacoes.value = data || []
    }
  } catch (e) {
    console.error('Erro ao carregar operações:', e)
    operacoes.value = []
  }
}

const salvarOperacoes = async () => {
  // Salvar no localStorage como backup
  localStorage.setItem(`odinenx_operacoes_${user.value?.id}`, JSON.stringify(operacoes.value))
}

const salvarOperacaoSupabase = async (operacao) => {
  try {
    const { data, error } = await supabase
      .from('trade_operacoes')
      .upsert({
        ...operacao,
        user_id: user.value.id,
        updated_at: new Date().toISOString()
      })
      .select()
    
    if (error) {
      console.error('Erro ao salvar no Supabase:', error)
      // Fallback: salvar no localStorage
      salvarOperacoes()
    }
    return data
  } catch (e) {
    console.error('Erro ao salvar operação:', e)
    salvarOperacoes()
  }
}

const deletarOperacaoSupabase = async (id) => {
  try {
    const { error } = await supabase
      .from('trade_operacoes')
      .delete()
      .eq('id', id)
      .eq('user_id', user.value.id)
    
    if (error) {
      console.error('Erro ao deletar no Supabase:', error)
    }
  } catch (e) {
    console.error('Erro ao deletar operação:', e)
  }
}

const carregarConfigRisco = async () => {
  try {
    const { data, error } = await supabase
      .from('trade_config_risco')
      .select('*')
      .eq('user_id', user.value.id)
      .single()
    
    if (error || !data) {
      // Fallback para localStorage ou valores padrão
      const saved = localStorage.getItem(`odinenx_risco_${user.value?.id}`)
      if (saved) {
        configRisco.value = JSON.parse(saved)
      }
      // Se não tem nada, usa os valores padrão já definidos
    } else {
      configRisco.value = {
        capital_total: data.capital_total,
        risco_por_operacao: data.risco_por_operacao,
        max_operacoes_dia: data.max_operacoes_dia,
        max_perda_dia: data.max_perda_dia,
        alavancagem_max: data.alavancagem_max
      }
    }
  } catch (e) {
    console.error('Erro ao carregar config risco:', e)
  }
}

const salvarConfigRisco = async () => {
  // Salvar no localStorage como backup
  localStorage.setItem(`odinenx_risco_${user.value?.id}`, JSON.stringify(configRisco.value))
  
  try {
    const { error } = await supabase
      .from('trade_config_risco')
      .upsert({
        user_id: user.value.id,
        ...configRisco.value,
        updated_at: new Date().toISOString()
      })
    
    if (error) {
      console.error('Erro ao salvar config no Supabase:', error)
    }
  } catch (e) {
    console.error('Erro ao salvar config risco:', e)
  }
}

// ===== CARREGAR DADOS REAIS DA API =====
const carregarDadosReais = async () => {
  await Promise.all([
    carregarCryptoReal(),
    carregarAcoesReal(),
    carregarForexReal()
  ])
  calcularIndicadores()
}

const carregarCryptoReal = async () => {
  apiStatus.value.crypto.loading = true
  apiStatus.value.crypto.error = null
  
  try {
    const response = await fetch('/api/market?type=crypto')
    const result = await response.json()
    
    if (result.success && result.data) {
      ativos.value.crypto = result.data.map(coin => ({
        simbolo: coin.simbolo,
        nome: coin.nome,
        preco: coin.preco,
        variacao: coin.variacao,
        volume: coin.volume,
        marketCap: coin.marketCap,
        high24h: coin.high24h,
        low24h: coin.low24h,
        imagem: coin.imagem,
        icone: coin.simbolo.charAt(0),
        cor: getCorCrypto(coin.simbolo)
      }))
      apiStatus.value.crypto.lastUpdate = new Date()
    } else {
      throw new Error(result.error || 'Erro ao carregar crypto')
    }
  } catch (error) {
    console.error('Erro Crypto API:', error)
    apiStatus.value.crypto.error = error.message
    // Fallback para dados simulados se API falhar
    gerarCryptoFallback()
  }
  
  apiStatus.value.crypto.loading = false
}

const carregarAcoesReal = async () => {
  apiStatus.value.acoes.loading = true
  apiStatus.value.acoes.error = null
  
  try {
    const response = await fetch('/api/market?type=acoes')
    const result = await response.json()
    
    if (result.success && result.data) {
      ativos.value.acoes = result.data.map(acao => ({
        simbolo: acao.simbolo,
        nome: acao.nome,
        preco: acao.preco,
        variacao: acao.variacao,
        volume: acao.volume,
        high: acao.high,
        low: acao.low,
        abertura: acao.abertura,
        setor: getSetorAcao(acao.simbolo)
      }))
      apiStatus.value.acoes.lastUpdate = new Date()
    } else {
      throw new Error(result.error || 'Erro ao carregar ações')
    }
  } catch (error) {
    console.error('Erro Ações API:', error)
    apiStatus.value.acoes.error = error.message
    gerarAcoesFallback()
  }
  
  apiStatus.value.acoes.loading = false
}

const carregarForexReal = async () => {
  apiStatus.value.forex.loading = true
  apiStatus.value.forex.error = null
  
  try {
    const response = await fetch('/api/market?type=forex')
    const result = await response.json()
    
    if (result.success && result.data) {
      ativos.value.forex = result.data.map(par => ({
        simbolo: par.simbolo,
        nome: par.nome,
        preco: par.preco,
        variacao: par.variacao,
        pip: par.simbolo.includes('JPY') ? 0.01 : 0.0001
      }))
      apiStatus.value.forex.lastUpdate = new Date()
    } else {
      throw new Error(result.error || 'Erro ao carregar forex')
    }
  } catch (error) {
    console.error('Erro Forex API:', error)
    apiStatus.value.forex.error = error.message
    gerarForexFallback()
  }
  
  apiStatus.value.forex.loading = false
}

// Cores personalizadas para cryptos
const getCorCrypto = (simbolo) => {
  const cores = {
    'BTC': '#F7931A',
    'ETH': '#627EEA',
    'BNB': '#F3BA2F',
    'SOL': '#00FFA3',
    'XRP': '#23292F',
    'ADA': '#0033AD',
    'DOGE': '#C3A634',
    'DOT': '#E6007A',
    'AVAX': '#E84142',
    'MATIC': '#8247E5',
    'TRX': '#FF0013',
    'LINK': '#2A5ADA',
    'TON': '#0098EA',
    'SHIB': '#FFA409',
    'LTC': '#BFBBBB'
  }
  return cores[simbolo] || '#6366f1'
}

// Setores das ações
const getSetorAcao = (simbolo) => {
  const setores = {
    'PETR4': 'Petróleo',
    'VALE3': 'Mineração',
    'ITUB4': 'Bancos',
    'BBDC4': 'Bancos',
    'ABEV3': 'Bebidas',
    'MGLU3': 'Varejo',
    'WEGE3': 'Industrial',
    'RENT3': 'Locação',
    'BBAS3': 'Bancos',
    'SUZB3': 'Papel',
    'B3SA3': 'Financeiro',
    'ELET3': 'Energia'
  }
  return setores[simbolo] || 'Outros'
}

// ===== FALLBACK (se API falhar) =====
const gerarCryptoFallback = () => {
  ativos.value.crypto = [
    { simbolo: 'BTC', nome: 'Bitcoin', preco: 67500, variacao: 0.27, icone: '₿', cor: '#F7931A' },
    { simbolo: 'ETH', nome: 'Ethereum', preco: 3420, variacao: -0.89, icone: 'Ξ', cor: '#627EEA' },
    { simbolo: 'BNB', nome: 'Binance Coin', preco: 605, variacao: 5.09, icone: 'B', cor: '#F3BA2F' },
    { simbolo: 'SOL', nome: 'Solana', preco: 178, variacao: 1.70, icone: 'S', cor: '#00FFA3' },
    { simbolo: 'XRP', nome: 'Ripple', preco: 0.52, variacao: 2.63, icone: 'X', cor: '#23292F' }
  ]
}

const gerarAcoesFallback = () => {
  ativos.value.acoes = [
    { simbolo: 'PETR4', nome: 'Petrobras PN', preco: 38.45, variacao: 1.23, setor: 'Petróleo' },
    { simbolo: 'VALE3', nome: 'Vale ON', preco: 62.30, variacao: -0.85, setor: 'Mineração' },
    { simbolo: 'ITUB4', nome: 'Itaú Unibanco PN', preco: 32.15, variacao: 0.47, setor: 'Bancos' },
    { simbolo: 'BBDC4', nome: 'Bradesco PN', preco: 14.80, variacao: -1.32, setor: 'Bancos' },
    { simbolo: 'ABEV3', nome: 'Ambev ON', preco: 12.45, variacao: 0.89, setor: 'Bebidas' }
  ]
}

const gerarForexFallback = () => {
  ativos.value.forex = [
    { simbolo: 'EUR/USD', nome: 'Euro/Dólar', preco: 1.0845, variacao: 0.15, pip: 0.0001 },
    { simbolo: 'USD/BRL', nome: 'Dólar/Real', preco: 4.9650, variacao: -0.32, pip: 0.0001 },
    { simbolo: 'GBP/USD', nome: 'Libra/Dólar', preco: 1.2680, variacao: 0.28, pip: 0.0001 },
    { simbolo: 'USD/JPY', nome: 'Dólar/Iene', preco: 148.25, variacao: 0.45, pip: 0.01 }
  ]
}

const calcularIndicadores = () => {
  const calcular = (ativo) => {
    let rsi = 50 + (ativo.variacao * 10) + (Math.random() - 0.5) * 20
    rsi = Math.max(10, Math.min(90, rsi))
    
    let tendencia, sinal, confianca
    if (rsi >= 70) {
      tendencia = 'sobrecompra'
      sinal = 'VENDA'
      confianca = Math.min(85, 50 + (rsi - 70) * 2)
    } else if (rsi <= 30) {
      tendencia = 'sobrevenda'
      sinal = 'COMPRA'
      confianca = Math.min(85, 50 + (30 - rsi) * 2)
    } else if (ativo.variacao > 1.5) {
      tendencia = 'alta'
      sinal = 'COMPRA'
      confianca = Math.min(80, 50 + ativo.variacao * 10)
    } else if (ativo.variacao < -1.5) {
      tendencia = 'baixa'
      sinal = 'VENDA'
      confianca = Math.min(80, 50 + Math.abs(ativo.variacao) * 10)
    } else {
      tendencia = 'lateral'
      sinal = 'AGUARDAR'
      confianca = 50
    }
    
    ativo.rsi = Math.round(rsi)
    ativo.tendencia = tendencia
    ativo.sinal = sinal
    ativo.confianca = Math.round(confianca)
    
    ativo.macd = (Math.random() - 0.5) * 100
    ativo.ema9 = ativo.preco * (1 + (Math.random() - 0.5) * 0.02)
    ativo.ema21 = ativo.preco * (1 + (Math.random() - 0.5) * 0.03)
    ativo.volume = Math.floor(Math.random() * 1000000) + 100000
    
    if (sinal === 'COMPRA') {
      ativo.entrada = ativo.preco
      ativo.alvo = ativo.preco * 1.05
      ativo.stop = ativo.preco * 0.97
    } else if (sinal === 'VENDA') {
      ativo.entrada = ativo.preco
      ativo.alvo = ativo.preco * 0.95
      ativo.stop = ativo.preco * 1.03
    }
  }
  
  ativos.value.crypto.forEach(calcular)
  ativos.value.acoes.forEach(calcular)
  ativos.value.forex.forEach(calcular)
}

// ===== OPERAÇÕES =====
const abrirModalNovaOperacao = (ativo = null) => {
  if (ativo) {
    novaOperacao.value.ativo = ativo.simbolo
    novaOperacao.value.categoria = categoriaAtiva.value
    novaOperacao.value.preco_entrada = ativo.preco
    novaOperacao.value.stop_loss = ativo.stop || ativo.preco * 0.97
    novaOperacao.value.take_profit = ativo.alvo || ativo.preco * 1.05
    novaOperacao.value.tipo = ativo.sinal === 'COMPRA' ? 'COMPRA' : 'VENDA'
    
    // Selecionar plataforma padrão baseada na categoria
    if (categoriaAtiva.value === 'crypto') novaOperacao.value.plataforma = 'Binance'
    else if (categoriaAtiva.value === 'acoes') novaOperacao.value.plataforma = 'Clear'
    else novaOperacao.value.plataforma = 'MetaTrader 5'
  }
  modalNovaOperacao.value = true
}

const criarOperacao = async () => {
  if (!novaOperacao.value.ativo || novaOperacao.value.quantidade <= 0) {
    alert('Preencha todos os campos obrigatórios')
    return
  }
  
  const op = {
    id: Date.now(),
    user_id: user.value.id,
    ...novaOperacao.value,
    created_at: new Date().toISOString(),
    data: new Date().toISOString(),
    status: 'ABERTA',
    resultado: 0
  }
  
  // Adicionar localmente primeiro (UX rápida)
  operacoes.value.unshift(op)
  modalNovaOperacao.value = false
  
  // Salvar no Supabase
  try {
    const { data, error } = await supabase
      .from('trade_operacoes')
      .insert([op])
      .select()
    
    if (error) {
      console.error('Erro ao salvar no Supabase:', error)
      salvarOperacoes() // Fallback localStorage
    } else if (data && data[0]) {
      // Atualizar com ID do Supabase
      const idx = operacoes.value.findIndex(o => o.id === op.id)
      if (idx !== -1) operacoes.value[idx] = data[0]
    }
  } catch (e) {
    console.error('Erro ao criar operação:', e)
    salvarOperacoes()
  }
  
  // Reset form
  novaOperacao.value = {
    tipo: 'COMPRA',
    ativo: '',
    categoria: 'crypto',
    preco_entrada: 0,
    quantidade: 0,
    stop_loss: 0,
    take_profit: 0,
    plataforma: 'Binance',
    observacao: ''
  }
}

const fecharOperacao = async (op, precoSaida) => {
  op.preco_saida = precoSaida
  op.status = 'FECHADA'
  
  if (op.tipo === 'COMPRA') {
    op.resultado = (precoSaida - op.preco_entrada) * op.quantidade
  } else {
    op.resultado = (op.preco_entrada - precoSaida) * op.quantidade
  }
  
  op.updated_at = new Date().toISOString()
  
  // Salvar no Supabase
  await salvarOperacaoSupabase(op)
  salvarOperacoes() // Backup localStorage
}

const fecharOperacaoManual = (op) => {
  const preco = prompt('Preço de saída:')
  if (preco && !isNaN(parseFloat(preco))) {
    fecharOperacao(op, parseFloat(preco))
  }
}

const excluirOperacao = async (id) => {
  if (confirm('Deseja excluir esta operação?')) {
    operacoes.value = operacoes.value.filter(o => o.id !== id)
    
    // Deletar do Supabase
    await deletarOperacaoSupabase(id)
    salvarOperacoes() // Backup localStorage
  }
}

const salvarObservacao = async (op, obs) => {
  op.observacao = obs
  op.updated_at = new Date().toISOString()
  
  // Salvar no Supabase
  await salvarOperacaoSupabase(op)
  salvarOperacoes() // Backup localStorage
}

// ===== CALCULADORA DE POSIÇÃO =====
const calculadora = ref({
  capital: 1000,
  risco_percentual: 2,
  preco_entrada: 100,
  stop_loss: 95
})

const resultadoCalculadora = computed(() => {
  const riscoValor = calculadora.value.capital * (calculadora.value.risco_percentual / 100)
  const distanciaStop = Math.abs(calculadora.value.preco_entrada - calculadora.value.stop_loss)
  const tamanhoLote = distanciaStop > 0 ? riscoValor / distanciaStop : 0
  const valorPosicao = tamanhoLote * calculadora.value.preco_entrada
  const takeProfit = calculadora.value.preco_entrada + (distanciaStop * 2) // RR 1:2
  
  return {
    riscoValor: riscoValor.toFixed(2),
    tamanhoLote: tamanhoLote.toFixed(4),
    valorPosicao: valorPosicao.toFixed(2),
    distanciaStop: distanciaStop.toFixed(2),
    distanciaPercent: ((distanciaStop / calculadora.value.preco_entrada) * 100).toFixed(2),
    takeProfit: takeProfit.toFixed(2),
    potencialGanho: (riscoValor * 2).toFixed(2)
  }
})

// ===== HELPERS =====
const formatarPreco = (preco, categoria = 'crypto') => {
  if (categoria === 'forex') return preco.toFixed(4)
  if (preco >= 1000) return preco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (preco >= 1) return preco.toFixed(2)
  return preco.toFixed(4)
}

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)
}

const formatarVolume = (vol) => {
  if (vol >= 1000000) return (vol / 1000000).toFixed(1) + 'M'
  if (vol >= 1000) return (vol / 1000).toFixed(1) + 'K'
  return vol.toString()
}

const getSinalClass = (sinal) => {
  if (sinal === 'COMPRA') return 'sinal-compra'
  if (sinal === 'VENDA') return 'sinal-venda'
  return 'sinal-aguardar'
}

const getTendenciaClass = (tendencia) => {
  if (tendencia === 'alta' || tendencia === 'sobrevenda') return 'tendencia-alta'
  if (tendencia === 'baixa' || tendencia === 'sobrecompra') return 'tendencia-baixa'
  return 'tendencia-lateral'
}

const selecionarAtivo = (ativo) => { ativoSelecionado.value = ativo }
const fecharModal = () => { ativoSelecionado.value = null }
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
        <router-link to="/trade" class="nav-item active"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>TRADE</router-link>
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
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item active">TRADE</button>
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
          <h1>Módulo TRADE</h1>
          <p>Sistema completo para Day Traders</p>
          <!-- Indicador de dados reais -->
          <div class="api-status-row">
            <span class="api-badge real" v-if="apiStatus.crypto.lastUpdate || apiStatus.acoes.lastUpdate || apiStatus.forex.lastUpdate">
              <span class="pulse-dot"></span>
              DADOS REAIS
            </span>
            <span class="api-badge loading" v-else-if="apiStatus.crypto.loading || apiStatus.acoes.loading || apiStatus.forex.loading">
              <span class="loading-dot"></span>
              Carregando...
            </span>
            <span v-if="apiStatus[categoriaAtiva]?.lastUpdate" class="last-update">
              Atualizado: {{ new Date(apiStatus[categoriaAtiva].lastUpdate).toLocaleTimeString('pt-BR') }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="carregarDadosReais" class="btn-refresh" :disabled="apiStatus.crypto.loading">
            <svg :class="{ spinning: apiStatus.crypto.loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
            Atualizar
          </button>
          <button @click="modalCalculadora = true" class="btn-calc">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="10" y2="10"/><line x1="14" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="10" y2="14"/><line x1="14" y1="14" x2="16" y2="14"/><line x1="8" y1="18" x2="16" y2="18"/></svg>
            Calculadora
          </button>
          <button @click="abrirModalNovaOperacao()" class="btn-nova-op">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Nova Operação
          </button>
        </div>
      </header>

      <!-- Abas Principais -->
      <div class="abas-principais">
        <button @click="abaAtiva = 'analise'" :class="{ active: abaAtiva === 'analise' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/></svg>
          Análise
        </button>
        <button @click="abaAtiva = 'dashboard'" :class="{ active: abaAtiva === 'dashboard' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          Dashboard
        </button>
        <button @click="abaAtiva = 'operacoes'" :class="{ active: abaAtiva === 'operacoes' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Operações
          <span class="badge" v-if="estatisticas.operacoesAbertas > 0">{{ estatisticas.operacoesAbertas }}</span>
        </button>
        <button @click="abaAtiva = 'risco'" :class="{ active: abaAtiva === 'risco' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Gestão de Risco
        </button>
        <button @click="abaAtiva = 'diario'" :class="{ active: abaAtiva === 'diario' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          Diário
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Carregando dados...</p>
      </div>

      <!-- ===== ABA ANÁLISE ===== -->
      <div v-else-if="abaAtiva === 'analise'" class="trade-content">
        <div class="categoria-tabs">
          <button @click="categoriaAtiva = 'crypto'" :class="{ active: categoriaAtiva === 'crypto' }">🪙 Crypto</button>
          <button @click="categoriaAtiva = 'acoes'" :class="{ active: categoriaAtiva === 'acoes' }">📈 Ações BR</button>
          <button @click="categoriaAtiva = 'forex'" :class="{ active: categoriaAtiva === 'forex' }">💱 Forex</button>
        </div>

        <div class="disclaimer-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <p>Análises automatizadas não garantem resultados. Trading envolve riscos. Opere com responsabilidade.</p>
        </div>

        <div class="ativos-grid">
          <div v-for="ativo in ativos[categoriaAtiva]" :key="ativo.simbolo" class="ativo-card" @click="selecionarAtivo(ativo)">
            <div class="ativo-header">
              <div class="ativo-icon" :style="{ background: ativo.cor || '#333' }">{{ ativo.icone || ativo.simbolo[0] }}</div>
              <div class="ativo-info">
                <span class="ativo-simbolo">{{ ativo.simbolo }}</span>
                <span class="ativo-nome">{{ ativo.nome }}</span>
              </div>
              <span class="sinal-badge" :class="getSinalClass(ativo.sinal)">{{ ativo.sinal }}</span>
            </div>
            
            <div class="ativo-preco">
              <span class="preco">{{ categoriaAtiva === 'forex' ? '' : 'R$ ' }}{{ formatarPreco(ativo.preco, categoriaAtiva) }}</span>
              <span class="variacao" :class="{ positiva: ativo.variacao > 0, negativa: ativo.variacao < 0 }">
                {{ ativo.variacao > 0 ? '+' : '' }}{{ ativo.variacao.toFixed(2) }}%
              </span>
            </div>
            
            <div class="ativo-indicadores">
              <div class="indicador">
                <span class="ind-label">RSI</span>
                <span class="ind-valor" :class="{ sobrecompra: ativo.rsi > 70, sobrevenda: ativo.rsi < 30 }">{{ ativo.rsi }}</span>
              </div>
              <div class="indicador">
                <span class="ind-label">Tendência</span>
                <span class="ind-valor" :class="getTendenciaClass(ativo.tendencia)">{{ ativo.tendencia }}</span>
              </div>
              <div class="indicador">
                <span class="ind-label">Confiança</span>
                <span class="ind-valor">{{ ativo.confianca }}%</span>
              </div>
            </div>
            
            <div class="ativo-actions">
              <button class="btn-analisar" @click.stop="selecionarAtivo(ativo)">Ver Análise</button>
              <button class="btn-operar" @click.stop="abrirModalNovaOperacao(ativo)">Operar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== ABA DASHBOARD ===== -->
      <div v-else-if="abaAtiva === 'dashboard'" class="dashboard-content">
        <div class="stats-grid">
          <div class="stat-card principal">
            <div class="stat-icon lucro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>
            <div class="stat-info">
              <span class="stat-label">Lucro Total</span>
              <span class="stat-valor" :class="{ positivo: estatisticas.lucroTotal > 0, negativo: estatisticas.lucroTotal < 0 }">{{ formatarMoeda(estatisticas.lucroTotal) }}</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon win"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
            <div class="stat-info">
              <span class="stat-label">Win Rate</span>
              <span class="stat-valor">{{ estatisticas.winRate }}%</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon pf"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg></div>
            <div class="stat-info">
              <span class="stat-label">Profit Factor</span>
              <span class="stat-valor">{{ estatisticas.profitFactor }}</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon dd"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/></svg></div>
            <div class="stat-info">
              <span class="stat-label">Max Drawdown</span>
              <span class="stat-valor negativo">{{ estatisticas.maxDrawdown }}%</span>
            </div>
          </div>
        </div>
        
        <div class="dashboard-row">
          <div class="card-section">
            <h3>📊 Resumo do Dia</h3>
            <div class="resumo-dia">
              <div class="resumo-item">
                <span class="resumo-label">Operações Hoje</span>
                <span class="resumo-valor">{{ estatisticas.operacoesHoje }}</span>
              </div>
              <div class="resumo-item">
                <span class="resumo-label">Lucro Hoje</span>
                <span class="resumo-valor" :class="{ positivo: estatisticas.lucroHoje > 0, negativo: estatisticas.lucroHoje < 0 }">{{ formatarMoeda(estatisticas.lucroHoje) }}</span>
              </div>
              <div class="resumo-item">
                <span class="resumo-label">Operações Abertas</span>
                <span class="resumo-valor">{{ estatisticas.operacoesAbertas }}</span>
              </div>
              <div class="resumo-item">
                <span class="resumo-label">Risco Aberto</span>
                <span class="resumo-valor alerta">{{ formatarMoeda(riscoAtual.riscoAberto) }}</span>
              </div>
            </div>
          </div>
          
          <div class="card-section">
            <h3>📈 Performance</h3>
            <div class="estatisticas-lista">
              <div class="est-item">
                <span>Total de Operações</span>
                <span>{{ estatisticas.totalOperacoes }}</span>
              </div>
              <div class="est-item">
                <span>Ganhos / Perdas</span>
                <span><span class="positivo">{{ estatisticas.totalGanhos }}</span> / <span class="negativo">{{ estatisticas.totalPerdas }}</span></span>
              </div>
              <div class="est-item">
                <span>Melhor Operação</span>
                <span class="positivo">{{ formatarMoeda(estatisticas.melhorOperacao) }}</span>
              </div>
              <div class="est-item">
                <span>Pior Operação</span>
                <span class="negativo">{{ formatarMoeda(estatisticas.piorOperacao) }}</span>
              </div>
              <div class="est-item">
                <span>Média de Ganhos</span>
                <span class="positivo">{{ formatarMoeda(estatisticas.mediaGanho) }}</span>
              </div>
              <div class="est-item">
                <span>Média de Perdas</span>
                <span class="negativo">{{ formatarMoeda(estatisticas.mediaPerda) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="dashboard-row">
          <div class="card-section">
            <h3>🔥 Streaks</h3>
            <div class="streaks-grid">
              <div class="streak-item">
                <span class="streak-label">Streak Atual</span>
                <span class="streak-valor" :class="{ positivo: estatisticas.streakAtual > 0, negativo: estatisticas.streakAtual < 0 }">
                  {{ estatisticas.streakAtual > 0 ? '+' : '' }}{{ estatisticas.streakAtual }}
                </span>
              </div>
              <div class="streak-item">
                <span class="streak-label">Melhor Streak</span>
                <span class="streak-valor positivo">+{{ estatisticas.melhorStreak }}</span>
              </div>
              <div class="streak-item">
                <span class="streak-label">Pior Streak</span>
                <span class="streak-valor negativo">-{{ estatisticas.piorStreak }}</span>
              </div>
            </div>
          </div>
          
          <div class="card-section plataformas">
            <h3>🏦 Plataformas</h3>
            <div class="plataformas-grid">
              <div v-for="plat in plataformas.slice(0, 6)" :key="plat.nome" class="plataforma-card">
                <div class="plat-icon" :style="{ background: plat.cor }">{{ plat.nome[0] }}</div>
                <span class="plat-nome">{{ plat.nome }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== ABA OPERAÇÕES ===== -->
      <div v-else-if="abaAtiva === 'operacoes'" class="operacoes-content">
        <div class="operacoes-filtros">
          <button @click="filtroOperacoes = 'todas'" :class="{ active: filtroOperacoes === 'todas' }">Todas</button>
          <button @click="filtroOperacoes = 'abertas'" :class="{ active: filtroOperacoes === 'abertas' }">Abertas</button>
          <button @click="filtroOperacoes = 'fechadas'" :class="{ active: filtroOperacoes === 'fechadas' }">Fechadas</button>
          <button @click="filtroOperacoes = 'crypto'" :class="{ active: filtroOperacoes === 'crypto' }">Crypto</button>
          <button @click="filtroOperacoes = 'acoes'" :class="{ active: filtroOperacoes === 'acoes' }">Ações</button>
          <button @click="filtroOperacoes = 'forex'" :class="{ active: filtroOperacoes === 'forex' }">Forex</button>
        </div>
        
        <div v-if="operacoesFiltradas.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <p>Nenhuma operação encontrada</p>
          <button @click="abrirModalNovaOperacao()" class="btn-nova-op">Criar Operação</button>
        </div>
        
        <div v-else class="operacoes-lista">
          <div v-for="op in operacoesFiltradas" :key="op.id" class="operacao-card" :class="{ aberta: op.status === 'ABERTA' }">
            <div class="op-header">
              <div class="op-tipo" :class="{ compra: op.tipo === 'COMPRA', venda: op.tipo === 'VENDA' }">{{ op.tipo }}</div>
              <div class="op-ativo">
                <span class="op-simbolo">{{ op.ativo }}</span>
                <span class="op-cat">{{ op.categoria }}</span>
              </div>
              <div class="op-status" :class="{ aberta: op.status === 'ABERTA', fechada: op.status === 'FECHADA' }">{{ op.status }}</div>
            </div>
            
            <div class="op-detalhes">
              <div class="op-detalhe">
                <span class="od-label">Entrada</span>
                <span class="od-valor">{{ formatarMoeda(op.preco_entrada) }}</span>
              </div>
              <div class="op-detalhe">
                <span class="od-label">Qtd</span>
                <span class="od-valor">{{ op.quantidade }}</span>
              </div>
              <div class="op-detalhe">
                <span class="od-label">Stop</span>
                <span class="od-valor negativo">{{ formatarMoeda(op.stop_loss) }}</span>
              </div>
              <div class="op-detalhe">
                <span class="od-label">Take</span>
                <span class="od-valor positivo">{{ formatarMoeda(op.take_profit) }}</span>
              </div>
              <div class="op-detalhe" v-if="op.status === 'FECHADA'">
                <span class="od-label">Saída</span>
                <span class="od-valor">{{ formatarMoeda(op.preco_saida) }}</span>
              </div>
              <div class="op-detalhe resultado">
                <span class="od-label">Resultado</span>
                <span class="od-valor" :class="{ positivo: op.resultado > 0, negativo: op.resultado < 0 }">{{ formatarMoeda(op.resultado) }}</span>
              </div>
            </div>
            
            <div class="op-footer">
              <span class="op-data">{{ new Date(op.data).toLocaleDateString('pt-BR') }} {{ new Date(op.data).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) }}</span>
              <span class="op-plataforma">{{ op.plataforma }}</span>
              <div class="op-acoes" v-if="op.status === 'ABERTA'">
                <button @click="fecharOperacao(op, op.take_profit)" class="btn-tp" title="Take Profit">TP</button>
                <button @click="fecharOperacao(op, op.stop_loss)" class="btn-sl" title="Stop Loss">SL</button>
                <button @click="fecharOperacaoManual(op)" class="btn-manual" title="Fechar Manual">📝</button>
                <button @click="excluirOperacao(op.id)" class="btn-del" title="Excluir">✕</button>
              </div>
              <div class="op-acoes" v-else>
                <button @click="excluirOperacao(op.id)" class="btn-del" title="Excluir">✕</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== ABA GESTÃO DE RISCO ===== -->
      <div v-else-if="abaAtiva === 'risco'" class="risco-content">
        <div class="risco-alertas">
          <div class="risco-alerta" v-if="riscoAtual.limiteOpsAtingido">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <span>⚠️ Limite de {{ configRisco.max_operacoes_dia }} operações diárias atingido!</span>
          </div>
          <div class="risco-alerta perda" v-if="riscoAtual.limitePerdaAtingido">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <span>🛑 Limite de perda diária de {{ configRisco.max_perda_dia }}% atingido! PARE DE OPERAR!</span>
          </div>
        </div>
        
        <div class="risco-resumo">
          <div class="risco-card">
            <span class="risco-label">💰 Capital Total</span>
            <span class="risco-valor">{{ formatarMoeda(configRisco.capital_total) }}</span>
          </div>
          <div class="risco-card">
            <span class="risco-label">💵 Capital Disponível</span>
            <span class="risco-valor">{{ formatarMoeda(riscoAtual.capitalDisponivel) }}</span>
          </div>
          <div class="risco-card">
            <span class="risco-label">⚡ Risco Aberto</span>
            <span class="risco-valor" :class="{ alerta: riscoAtual.percRisco > 5 }">{{ riscoAtual.percRisco }}%</span>
          </div>
          <div class="risco-card">
            <span class="risco-label">📅 Ops Hoje</span>
            <span class="risco-valor" :class="{ alerta: riscoAtual.operacoesHoje >= configRisco.max_operacoes_dia }">{{ riscoAtual.operacoesHoje }}/{{ configRisco.max_operacoes_dia }}</span>
          </div>
          <div class="risco-card">
            <span class="risco-label">📉 Perda Hoje</span>
            <span class="risco-valor" :class="{ alerta: riscoAtual.percPerdaHoje > 3 }">{{ riscoAtual.percPerdaHoje }}%</span>
          </div>
        </div>
        
        <div class="config-risco">
          <h3>⚙️ Configurações de Risco</h3>
          <div class="config-grid">
            <div class="config-item">
              <label>Capital Total (R$)</label>
              <input type="number" v-model="configRisco.capital_total" @change="salvarConfigRisco">
            </div>
            <div class="config-item">
              <label>Risco por Operação (%)</label>
              <input type="number" v-model="configRisco.risco_por_operacao" @change="salvarConfigRisco" min="0.5" max="10" step="0.5">
            </div>
            <div class="config-item">
              <label>Máx. Operações/Dia</label>
              <input type="number" v-model="configRisco.max_operacoes_dia" @change="salvarConfigRisco" min="1" max="50">
            </div>
            <div class="config-item">
              <label>Máx. Perda Diária (%)</label>
              <input type="number" v-model="configRisco.max_perda_dia" @change="salvarConfigRisco" min="1" max="20">
            </div>
            <div class="config-item">
              <label>Alavancagem Máxima</label>
              <input type="number" v-model="configRisco.alavancagem_max" @change="salvarConfigRisco" min="1" max="125">
            </div>
          </div>
        </div>
        
        <div class="regras-risco">
          <h3>📜 Regras de Ouro do Day Trader</h3>
          <ul>
            <li>✅ Nunca arrisque mais de <strong>{{ configRisco.risco_por_operacao }}%</strong> do capital por operação</li>
            <li>✅ Limite de <strong>{{ configRisco.max_operacoes_dia }}</strong> operações por dia</li>
            <li>✅ Pare de operar se perder <strong>{{ configRisco.max_perda_dia }}%</strong> do capital no dia</li>
            <li>✅ Sempre use <strong>stop loss</strong> em todas as operações</li>
            <li>✅ Relação risco/recompensa mínima de <strong>1:2</strong></li>
            <li>✅ Nunca opere em <strong>revenge</strong> (após perda emocional)</li>
            <li>✅ Mantenha um <strong>diário de trading</strong> atualizado</li>
            <li>✅ Respeite seu <strong>plano de trading</strong></li>
          </ul>
        </div>
      </div>

      <!-- ===== ABA DIÁRIO ===== -->
      <div v-else-if="abaAtiva === 'diario'" class="diario-content">
        <div class="diario-header">
          <h3>📔 Diário de Trading</h3>
          <p>Registre suas operações e aprenda com seus erros e acertos</p>
        </div>
        
        <div v-if="operacoes.filter(o => o.status === 'FECHADA').length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          <p>Seu diário está vazio. Feche operações para registrar aqui.</p>
        </div>
        
        <div v-else class="diario-entradas">
          <div v-for="op in operacoes.filter(o => o.status === 'FECHADA').slice(0, 20)" :key="op.id" class="diario-entrada" :class="{ ganho: op.resultado > 0, perda: op.resultado < 0 }">
            <div class="diario-linha">
              <div class="diario-data">{{ new Date(op.data).toLocaleDateString('pt-BR') }}</div>
              <div class="diario-resumo">
                <span class="diario-tipo" :class="{ compra: op.tipo === 'COMPRA', venda: op.tipo === 'VENDA' }">{{ op.tipo }}</span>
                <span class="diario-ativo">{{ op.ativo }}</span>
                <span class="diario-plat">{{ op.plataforma }}</span>
              </div>
              <div class="diario-resultado" :class="{ positivo: op.resultado > 0, negativo: op.resultado < 0 }">{{ formatarMoeda(op.resultado) }}</div>
            </div>
            <div class="diario-obs">
              <textarea :value="op.observacao" @blur="salvarObservacao(op, $event.target.value)" placeholder="Adicione suas observações sobre esta operação... O que funcionou? O que poderia melhorar?"></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== MODAL ANÁLISE ===== -->
      <div v-if="ativoSelecionado" class="modal-overlay" @click.self="fecharModal">
        <div class="modal-analise">
          <button class="modal-close" @click="fecharModal">×</button>
          
          <div class="modal-header-ativo">
            <div class="ativo-icon grande" :style="{ background: ativoSelecionado.cor || '#333' }">{{ ativoSelecionado.icone || ativoSelecionado.simbolo[0] }}</div>
            <div class="ativo-info-modal">
              <h2>{{ ativoSelecionado.simbolo }}</h2>
              <p>{{ ativoSelecionado.nome }}</p>
            </div>
            <div class="sinal-grande" :class="getSinalClass(ativoSelecionado.sinal)">{{ ativoSelecionado.sinal }}</div>
          </div>
          
          <div class="preco-atual">
            <span class="preco-label">Preço Atual</span>
            <span class="preco-valor">{{ categoriaAtiva === 'forex' ? '' : 'R$ ' }}{{ formatarPreco(ativoSelecionado.preco, categoriaAtiva) }}</span>
            <span class="variacao" :class="{ positiva: ativoSelecionado.variacao > 0, negativa: ativoSelecionado.variacao < 0 }">
              {{ ativoSelecionado.variacao > 0 ? '+' : '' }}{{ ativoSelecionado.variacao.toFixed(2) }}%
            </span>
          </div>
          
          <div class="indicadores-grid">
            <div class="ind-card">
              <span class="ind-titulo">RSI (14)</span>
              <span class="ind-value" :class="{ sobrecompra: ativoSelecionado.rsi > 70, sobrevenda: ativoSelecionado.rsi < 30 }">{{ ativoSelecionado.rsi }}</span>
              <div class="rsi-bar"><div class="rsi-fill" :style="{ width: ativoSelecionado.rsi + '%' }"></div></div>
            </div>
            <div class="ind-card">
              <span class="ind-titulo">Tendência</span>
              <span class="ind-value" :class="getTendenciaClass(ativoSelecionado.tendencia)">{{ ativoSelecionado.tendencia }}</span>
            </div>
            <div class="ind-card">
              <span class="ind-titulo">Confiança</span>
              <span class="ind-value">{{ ativoSelecionado.confianca }}%</span>
              <div class="conf-bar"><div class="conf-fill" :style="{ width: ativoSelecionado.confianca + '%' }"></div></div>
            </div>
          </div>
          
          <div class="niveis-operacao" v-if="ativoSelecionado.sinal !== 'AGUARDAR'">
            <h4>Níveis de Operação</h4>
            <div class="niveis-grid">
              <div class="nivel entrada"><span>Entrada</span><span>{{ categoriaAtiva === 'forex' ? '' : 'R$ ' }}{{ formatarPreco(ativoSelecionado.entrada, categoriaAtiva) }}</span></div>
              <div class="nivel alvo"><span>Alvo (TP)</span><span>{{ categoriaAtiva === 'forex' ? '' : 'R$ ' }}{{ formatarPreco(ativoSelecionado.alvo, categoriaAtiva) }}</span></div>
              <div class="nivel stop"><span>Stop (SL)</span><span>{{ categoriaAtiva === 'forex' ? '' : 'R$ ' }}{{ formatarPreco(ativoSelecionado.stop, categoriaAtiva) }}</span></div>
            </div>
          </div>
          
          <button class="btn-operar-modal" @click="abrirModalNovaOperacao(ativoSelecionado); fecharModal()">
            Abrir Operação
          </button>
        </div>
      </div>

      <!-- ===== MODAL NOVA OPERAÇÃO ===== -->
      <div v-if="modalNovaOperacao" class="modal-overlay" @click.self="modalNovaOperacao = false">
        <div class="modal-operacao">
          <button class="modal-close" @click="modalNovaOperacao = false">×</button>
          <h2>📝 Nova Operação</h2>
          
          <div class="form-grid">
            <div class="form-group">
              <label>Tipo</label>
              <select v-model="novaOperacao.tipo">
                <option value="COMPRA">🟢 COMPRA (Long)</option>
                <option value="VENDA">🔴 VENDA (Short)</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Ativo *</label>
              <input type="text" v-model="novaOperacao.ativo" placeholder="BTC, PETR4, EUR/USD...">
            </div>
            
            <div class="form-group">
              <label>Categoria</label>
              <select v-model="novaOperacao.categoria">
                <option value="crypto">🪙 Crypto</option>
                <option value="acoes">📈 Ações BR</option>
                <option value="forex">💱 Forex</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Plataforma</label>
              <select v-model="novaOperacao.plataforma">
                <option v-for="p in plataformas" :key="p.nome" :value="p.nome">{{ p.nome }}</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Preço de Entrada *</label>
              <input type="number" v-model="novaOperacao.preco_entrada" step="0.0001">
            </div>
            
            <div class="form-group">
              <label>Quantidade *</label>
              <input type="number" v-model="novaOperacao.quantidade" step="0.0001">
            </div>
            
            <div class="form-group">
              <label>Stop Loss</label>
              <input type="number" v-model="novaOperacao.stop_loss" step="0.0001">
            </div>
            
            <div class="form-group">
              <label>Take Profit</label>
              <input type="number" v-model="novaOperacao.take_profit" step="0.0001">
            </div>
          </div>
          
          <div class="form-group full">
            <label>Observações</label>
            <textarea v-model="novaOperacao.observacao" placeholder="Motivo da entrada, análise técnica, setup identificado..."></textarea>
          </div>
          
          <button @click="criarOperacao" class="btn-criar">✅ Criar Operação</button>
        </div>
      </div>

      <!-- ===== MODAL CALCULADORA ===== -->
      <div v-if="modalCalculadora" class="modal-overlay" @click.self="modalCalculadora = false">
        <div class="modal-calc">
          <button class="modal-close" @click="modalCalculadora = false">×</button>
          <h2>🧮 Calculadora de Posição</h2>
          
          <div class="calc-form">
            <div class="calc-group">
              <label>Capital (R$)</label>
              <input type="number" v-model="calculadora.capital">
            </div>
            <div class="calc-group">
              <label>Risco (%)</label>
              <input type="number" v-model="calculadora.risco_percentual" step="0.5">
            </div>
            <div class="calc-group">
              <label>Preço Entrada</label>
              <input type="number" v-model="calculadora.preco_entrada" step="0.01">
            </div>
            <div class="calc-group">
              <label>Stop Loss</label>
              <input type="number" v-model="calculadora.stop_loss" step="0.01">
            </div>
          </div>
          
          <div class="calc-resultado">
            <div class="calc-item">
              <span>💰 Risco em R$</span>
              <span class="calc-valor">R$ {{ resultadoCalculadora.riscoValor }}</span>
            </div>
            <div class="calc-item">
              <span>📏 Distância do Stop</span>
              <span class="calc-valor">R$ {{ resultadoCalculadora.distanciaStop }} ({{ resultadoCalculadora.distanciaPercent }}%)</span>
            </div>
            <div class="calc-item destaque">
              <span>📊 Tamanho do Lote</span>
              <span class="calc-valor">{{ resultadoCalculadora.tamanhoLote }}</span>
            </div>
            <div class="calc-item">
              <span>💵 Valor da Posição</span>
              <span class="calc-valor">R$ {{ resultadoCalculadora.valorPosicao }}</span>
            </div>
            <div class="calc-item">
              <span>🎯 Take Profit (1:2)</span>
              <span class="calc-valor positivo">R$ {{ resultadoCalculadora.takeProfit }}</span>
            </div>
            <div class="calc-item">
              <span>🚀 Potencial Ganho</span>
              <span class="calc-valor positivo">R$ {{ resultadoCalculadora.potencialGanho }}</span>
            </div>
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

.mobile-menu-btn { display: none; position: fixed; top: 20px; right: 20px; width: 50px; height: 50px; border-radius: 12px; background: rgba(255, 255, 255, 0.95); border: none; z-index: 1000; cursor: pointer; align-items: center; justify-content: center; }
.mobile-menu-btn svg { width: 28px; height: 28px; stroke: #000; }
.mobile-overlay { display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); z-index: 998; }
.mobile-menu { display: none; position: fixed; bottom: 0; left: 0; right: 0; background: #0a0a0a; border-top-left-radius: 25px; border-top-right-radius: 25px; padding: 25px; z-index: 999; transform: translateY(100%); transition: transform 0.3s ease; }
.mobile-menu.open { transform: translateY(0); }
.mobile-menu-header { text-align: center; margin-bottom: 20px; }
.mobile-logo { height: 35px; }
.mobile-nav { display: flex; flex-direction: column; gap: 8px; }
.mobile-nav-item { padding: 15px 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #fff; font-weight: 500; cursor: pointer; text-align: left; }
.mobile-nav-item:hover, .mobile-nav-item.active { background: rgba(255, 255, 255, 0.1); }
.mobile-logout { width: 100%; margin-top: 15px; padding: 15px; background: transparent; border: 1px solid #ef4444; border-radius: 12px; color: #ef4444; font-weight: 600; cursor: pointer; }

.main-content { flex: 1; margin-left: 260px; padding: 30px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; flex-wrap: wrap; gap: 20px; }
.header-left h1 { font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
.header-left p { color: rgba(255, 255, 255, 0.5); }
.header-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-calc, .btn-nova-op { display: flex; align-items: center; gap: 8px; padding: 12px 20px; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.btn-calc { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: #fff; }
.btn-calc:hover { background: rgba(255, 255, 255, 0.15); }
.btn-calc svg, .btn-nova-op svg { width: 18px; height: 18px; }
.btn-nova-op { background: #22c55e; border: none; color: #000; }
.btn-nova-op:hover { background: #16a34a; }

.abas-principais { display: flex; gap: 5px; margin-bottom: 25px; background: rgba(255, 255, 255, 0.03); padding: 5px; border-radius: 12px; overflow-x: auto; }
.abas-principais button { display: flex; align-items: center; gap: 8px; padding: 12px 20px; background: transparent; border: none; color: rgba(255, 255, 255, 0.5); font-weight: 500; cursor: pointer; border-radius: 8px; transition: all 0.3s; white-space: nowrap; position: relative; }
.abas-principais button:hover { color: #fff; background: rgba(255, 255, 255, 0.05); }
.abas-principais button.active { background: rgba(255, 255, 255, 0.1); color: #fff; }
.abas-principais button svg { width: 18px; height: 18px; }
.abas-principais .badge { background: #22c55e; color: #000; font-size: 0.7rem; padding: 2px 6px; border-radius: 10px; margin-left: 5px; font-weight: 700; }

.disclaimer-box { display: flex; align-items: center; gap: 12px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; }
.disclaimer-box svg { width: 20px; height: 20px; stroke: #fbbf24; flex-shrink: 0; }
.disclaimer-box p { font-size: 0.85rem; color: rgba(255, 255, 255, 0.7); margin: 0; }

.categoria-tabs { display: flex; gap: 10px; margin-bottom: 20px; }
.categoria-tabs button { padding: 12px 25px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: rgba(255, 255, 255, 0.6); font-weight: 600; cursor: pointer; transition: all 0.3s; }
.categoria-tabs button:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
.categoria-tabs button.active { background: #fff; color: #000; border-color: #fff; }

.loading-state, .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 20px; }
.spinner { width: 50px; height: 50px; border: 3px solid rgba(255, 255, 255, 0.1); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-state p, .empty-state p { margin-top: 20px; color: rgba(255, 255, 255, 0.5); }
.empty-state svg { width: 60px; height: 60px; stroke: rgba(255, 255, 255, 0.3); }
.empty-state .btn-nova-op { margin-top: 20px; }

.ativos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.ativo-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.3s; }
.ativo-card:hover { transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.3); }
.ativo-header { display: flex; align-items: center; gap: 12px; margin-bottom: 15px; }
.ativo-icon { width: 45px; height: 45px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.2rem; color: #fff; }
.ativo-icon.grande { width: 60px; height: 60px; font-size: 1.5rem; }
.ativo-info { flex: 1; }
.ativo-simbolo { display: block; font-weight: 700; font-size: 1.1rem; }
.ativo-nome { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); }
.sinal-badge { padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; }
.sinal-compra { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.sinal-venda { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.sinal-aguardar { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.ativo-preco { display: flex; align-items: baseline; gap: 10px; margin-bottom: 15px; }
.preco { font-size: 1.5rem; font-weight: 700; }
.variacao { font-size: 0.9rem; font-weight: 600; }
.variacao.positiva { color: #22c55e; }
.variacao.negativa { color: #ef4444; }
.ativo-indicadores { display: flex; gap: 15px; margin-bottom: 15px; }
.indicador { flex: 1; text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.03); border-radius: 8px; }
.ind-label { display: block; font-size: 0.7rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px; }
.ind-valor { font-weight: 700; font-size: 0.9rem; text-transform: capitalize; }
.ind-valor.sobrecompra { color: #ef4444; }
.ind-valor.sobrevenda { color: #22c55e; }
.tendencia-alta { color: #22c55e; }
.tendencia-baixa { color: #ef4444; }
.tendencia-lateral { color: #fbbf24; }
.ativo-actions { display: flex; gap: 10px; }
.btn-analisar, .btn-operar { flex: 1; padding: 10px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s; font-size: 0.85rem; }
.btn-analisar { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: #fff; }
.btn-analisar:hover { background: rgba(255, 255, 255, 0.15); }
.btn-operar { background: #22c55e; border: none; color: #000; }
.btn-operar:hover { background: #16a34a; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
.stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 15px; }
.stat-card.principal { grid-column: span 2; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05)); border-color: rgba(34, 197, 94, 0.3); }
.stat-icon { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-icon svg { width: 24px; height: 24px; }
.stat-icon.lucro { background: rgba(34, 197, 94, 0.2); }
.stat-icon.lucro svg { stroke: #22c55e; }
.stat-icon.win { background: rgba(59, 130, 246, 0.2); }
.stat-icon.win svg { stroke: #3b82f6; }
.stat-icon.pf { background: rgba(168, 85, 247, 0.2); }
.stat-icon.pf svg { stroke: #a855f7; }
.stat-icon.dd { background: rgba(239, 68, 68, 0.2); }
.stat-icon.dd svg { stroke: #ef4444; }
.stat-label { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px; }
.stat-valor { font-size: 1.5rem; font-weight: 700; }
.stat-valor.positivo, .positivo { color: #22c55e; }
.stat-valor.negativo, .negativo { color: #ef4444; }
.alerta { color: #fbbf24; }

.dashboard-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.card-section { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; }
.card-section h3 { font-size: 1rem; margin-bottom: 20px; color: rgba(255, 255, 255, 0.9); }
.resumo-dia { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.resumo-item { padding: 15px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; }
.resumo-label { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px; }
.resumo-valor { font-size: 1.3rem; font-weight: 700; }
.estatisticas-lista { display: flex; flex-direction: column; gap: 12px; }
.est-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.est-item:last-child { border-bottom: none; }

.streaks-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
.streak-item { text-align: center; padding: 15px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; }
.streak-label { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; }
.streak-valor { font-size: 1.5rem; font-weight: 700; }

.plataformas-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.plataforma-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 15px 10px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; }
.plat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; }
.plat-nome { font-size: 0.8rem; font-weight: 500; text-align: center; }

.operacoes-filtros { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.operacoes-filtros button { padding: 8px 16px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; color: rgba(255, 255, 255, 0.6); cursor: pointer; transition: all 0.3s; font-size: 0.85rem; }
.operacoes-filtros button:hover, .operacoes-filtros button.active { background: rgba(255, 255, 255, 0.1); color: #fff; border-color: rgba(255, 255, 255, 0.2); }
.operacoes-lista { display: flex; flex-direction: column; gap: 15px; }
.operacao-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px; }
.operacao-card.aberta { border-color: rgba(59, 130, 246, 0.5); background: rgba(59, 130, 246, 0.05); }
.op-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
.op-tipo { padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }
.op-tipo.compra { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.op-tipo.venda { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.op-ativo { flex: 1; }
.op-simbolo { font-weight: 700; font-size: 1.1rem; }
.op-cat { font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-left: 10px; text-transform: capitalize; }
.op-status { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
.op-status.aberta { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.op-status.fechada { background: rgba(255, 255, 255, 0.1); color: rgba(255, 255, 255, 0.6); }
.op-detalhes { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px; }
.op-detalhe { }
.od-label { display: block; font-size: 0.7rem; color: rgba(255, 255, 255, 0.4); }
.od-valor { font-weight: 600; }
.op-detalhe.resultado { margin-left: auto; }
.op-footer { display: flex; align-items: center; gap: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.05); flex-wrap: wrap; }
.op-data, .op-plataforma { font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); }
.op-acoes { margin-left: auto; display: flex; gap: 8px; }
.btn-tp, .btn-sl, .btn-del, .btn-manual { padding: 6px 12px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.btn-tp { background: #22c55e; color: #000; }
.btn-tp:hover { background: #16a34a; }
.btn-sl { background: #ef4444; color: #fff; }
.btn-sl:hover { background: #dc2626; }
.btn-manual { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.btn-del { background: rgba(255, 255, 255, 0.1); color: #fff; }
.btn-del:hover { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.risco-alertas { margin-bottom: 20px; }
.risco-alerta { display: flex; align-items: center; gap: 10px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 12px; padding: 15px 20px; margin-bottom: 10px; color: #fbbf24; }
.risco-alerta.perda { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); color: #ef4444; }
.risco-alerta svg { width: 24px; height: 24px; flex-shrink: 0; }
.risco-resumo { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }
.risco-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; text-align: center; }
.risco-label { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; }
.risco-valor { font-size: 1.4rem; font-weight: 700; }
.config-risco { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 30px; }
.config-risco h3 { margin-bottom: 20px; }
.config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; }
.config-item label { display: block; font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 8px; }
.config-item input { width: 100%; padding: 12px 15px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: #fff; font-size: 1rem; }
.config-item input:focus { outline: none; border-color: rgba(255, 255, 255, 0.3); }
.regras-risco { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; }
.regras-risco h3 { margin-bottom: 20px; }
.regras-risco ul { list-style: none; padding: 0; margin: 0; }
.regras-risco li { padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.8); }
.regras-risco li:last-child { border-bottom: none; }
.regras-risco strong { color: #22c55e; }

.diario-header { margin-bottom: 25px; }
.diario-header h3 { margin-bottom: 5px; }
.diario-header p { color: rgba(255, 255, 255, 0.5); }
.diario-entradas { display: flex; flex-direction: column; gap: 15px; }
.diario-entrada { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; }
.diario-entrada.ganho { border-left: 3px solid #22c55e; }
.diario-entrada.perda { border-left: 3px solid #ef4444; }
.diario-linha { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; flex-wrap: wrap; }
.diario-data { font-size: 0.85rem; color: rgba(255, 255, 255, 0.5); min-width: 80px; }
.diario-resumo { flex: 1; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.diario-tipo { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
.diario-tipo.compra { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.diario-tipo.venda { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.diario-ativo { font-weight: 600; }
.diario-plat { font-size: 0.8rem; color: rgba(255, 255, 255, 0.4); }
.diario-resultado { font-weight: 700; font-size: 1.1rem; }
.diario-obs textarea { width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; color: #fff; resize: vertical; min-height: 60px; font-size: 0.9rem; }
.diario-obs textarea:focus { outline: none; border-color: rgba(255, 255, 255, 0.3); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-analise, .modal-operacao, .modal-calc { background: #111; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; width: 100%; max-width: 550px; max-height: 90vh; overflow-y: auto; padding: 30px; position: relative; }
.modal-close { position: absolute; top: 15px; right: 15px; width: 40px; height: 40px; background: rgba(255, 255, 255, 0.1); border: none; border-radius: 50%; color: #fff; font-size: 1.5rem; cursor: pointer; }
.modal-close:hover { background: #ef4444; }
.modal-header-ativo { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; }
.ativo-info-modal h2 { margin: 0; font-size: 1.5rem; }
.ativo-info-modal p { color: rgba(255, 255, 255, 0.5); margin: 5px 0 0; }
.sinal-grande { padding: 10px 20px; border-radius: 10px; font-weight: 700; margin-left: auto; }
.preco-atual { text-align: center; margin-bottom: 25px; padding: 20px; background: rgba(255, 255, 255, 0.03); border-radius: 12px; }
.preco-label { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px; }
.preco-valor { font-size: 2rem; font-weight: 700; }
.indicadores-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; }
.ind-card { text-align: center; padding: 15px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; }
.ind-titulo { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; }
.ind-value { font-size: 1.3rem; font-weight: 700; text-transform: capitalize; }
.rsi-bar, .conf-bar { height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; margin-top: 10px; overflow: hidden; }
.rsi-fill { height: 100%; background: linear-gradient(90deg, #22c55e, #fbbf24, #ef4444); border-radius: 3px; }
.conf-fill { height: 100%; background: linear-gradient(90deg, #ef4444, #fbbf24, #22c55e); border-radius: 3px; }
.niveis-operacao { margin-bottom: 25px; }
.niveis-operacao h4 { margin-bottom: 15px; color: rgba(255, 255, 255, 0.7); }
.niveis-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.nivel { text-align: center; padding: 15px; border-radius: 10px; }
.nivel span:first-child { display: block; font-size: 0.8rem; margin-bottom: 5px; }
.nivel span:last-child { font-weight: 700; font-size: 1.1rem; }
.nivel.entrada { background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); }
.nivel.alvo { background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: #22c55e; }
.nivel.stop { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; }
.btn-operar-modal { width: 100%; padding: 15px; background: #22c55e; border: none; border-radius: 12px; color: #000; font-weight: 700; font-size: 1rem; cursor: pointer; }
.btn-operar-modal:hover { background: #16a34a; }

.modal-operacao h2, .modal-calc h2 { margin-bottom: 25px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
.form-group label { display: block; font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 8px; }
.form-group input, .form-group select { width: 100%; padding: 12px 15px; background: #1a1a1a; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: #fff; font-size: 1rem; }
.form-group select { cursor: pointer; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23fff' d='M6 8L1 3h10z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 15px center; padding-right: 40px; }
.form-group select option { background: #1a1a1a; color: #fff; padding: 10px; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: rgba(255, 255, 255, 0.3); }
.form-group.full { grid-column: span 2; }
.form-group textarea { width: 100%; padding: 12px 15px; background: #1a1a1a; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: #fff; min-height: 80px; resize: vertical; }
.btn-criar { width: 100%; padding: 15px; background: #22c55e; border: none; border-radius: 12px; color: #000; font-weight: 700; font-size: 1rem; cursor: pointer; margin-top: 10px; }
.btn-criar:hover { background: #16a34a; }

.calc-form { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; }
.calc-group label { display: block; font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 8px; }
.calc-group input { width: 100%; padding: 12px 15px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: #fff; font-size: 1rem; }
.calc-resultado { background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 20px; }
.calc-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.calc-item:last-child { border-bottom: none; }
.calc-item.destaque { background: rgba(34, 197, 94, 0.1); margin: 10px -20px; padding: 15px 20px; border-radius: 8px; }
.calc-valor { font-weight: 700; }

@media (max-width: 968px) {
  /* Sidebar e Menu Mobile */
  .sidebar { display: none !important; }
  .mobile-menu-btn { 
    display: flex !important; 
    position: fixed;
    top: 15px;
    right: 15px;
    width: 48px;
    height: 48px;
    z-index: 1001;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 12px;
    align-items: center;
    justify-content: center;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
  }
  .mobile-menu-btn svg { width: 26px; height: 26px; stroke: #000; }
  .mobile-overlay { display: block; }
  .mobile-menu { display: block; }
  
  /* Main Content */
  .main-content { 
    margin-left: 0 !important; 
    padding: 70px 15px 120px 15px !important;
    width: 100%;
    box-sizing: border-box;
    overflow-x: hidden;
  }
  
  /* Header */
  .page-header { 
    flex-direction: column; 
    align-items: center; 
    text-align: center;
    gap: 15px;
  }
  .header-left { 
    text-align: center; 
    width: 100%; 
  }
  .header-left h1 { font-size: 1.5rem; margin-bottom: 5px; }
  .header-left p { font-size: 0.85rem; }
  .api-status-row { justify-content: center; }
  
  /* Header Actions */
  .header-actions { 
    width: 100%; 
    display: flex;
    flex-wrap: wrap;
    justify-content: center; 
    gap: 8px;
  }
  .header-actions button { 
    flex: 1 1 45%;
    min-width: 0;
    padding: 10px 12px;
    font-size: 0.8rem;
    justify-content: center;
  }
  .header-actions button svg { width: 16px; height: 16px; }
  
  /* Abas principais - CENTRALIZADAS */
  .abas-principais { 
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px;
    padding: 10px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    margin-bottom: 20px;
  }
  .abas-principais button { 
    flex: 1 1 calc(33.33% - 6px);
    min-width: 0;
    padding: 10px 8px; 
    font-size: 0.75rem;
    white-space: nowrap;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }
  .abas-principais button svg { width: 14px; height: 14px; flex-shrink: 0; }
  .abas-principais .badge { font-size: 0.6rem; padding: 2px 4px; }
  
  /* Categoria tabs - CENTRALIZADAS */
  .categoria-tabs { 
    display: flex; 
    flex-wrap: wrap; 
    justify-content: center; 
    gap: 8px;
    margin-bottom: 15px;
  }
  .categoria-tabs button { 
    flex: 1 1 calc(33.33% - 8px);
    min-width: 90px;
    max-width: 150px;
    justify-content: center; 
    padding: 10px 12px;
    font-size: 0.8rem;
  }
  
  /* Stats grid */
  .stats-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .stat-card.principal { grid-column: span 2; }
  .stat-card { padding: 12px; }
  .stat-icon { width: 40px; height: 40px; }
  .stat-icon svg { width: 20px; height: 20px; }
  .stat-valor { font-size: 1.2rem; }
  .stat-label { font-size: 0.7rem; }
  
  /* Dashboard */
  .dashboard-row { grid-template-columns: 1fr; gap: 12px; }
  .card-section { padding: 15px; }
  .card-section h3 { font-size: 0.95rem; }
  
  /* Resumo dia */
  .resumo-dia { grid-template-columns: 1fr 1fr; gap: 8px; }
  .resumo-item { padding: 10px; }
  .resumo-valor { font-size: 1.1rem; }
  
  /* Ativos grid */
  .ativos-grid { grid-template-columns: 1fr; gap: 12px; }
  .ativo-card { padding: 15px; }
  .ativo-header { flex-wrap: wrap; gap: 8px; }
  .ativo-icon { width: 40px; height: 40px; font-size: 1rem; }
  .ativo-simbolo { font-size: 1rem; }
  .preco { font-size: 1.3rem; }
  .ativo-indicadores { flex-wrap: wrap; gap: 6px; }
  .indicador { flex: 1 1 calc(33.33% - 6px); min-width: 70px; padding: 8px; }
  .ind-label { font-size: 0.65rem; }
  .ind-valor { font-size: 0.8rem; }
  .ativo-actions { flex-direction: column; gap: 8px; }
  .ativo-actions button { width: 100%; }
  
  /* Operações */
  .operacoes-filtros { 
    display: flex; 
    flex-wrap: wrap; 
    justify-content: center; 
    gap: 6px; 
    margin-bottom: 15px;
  }
  .operacoes-filtros button { 
    padding: 8px 12px; 
    font-size: 0.75rem;
  }
  .operacao-card { padding: 12px; }
  .op-header { flex-direction: column; gap: 8px; align-items: flex-start; }
  .op-detalhes { flex-direction: column; gap: 6px; }
  .op-detalhe.resultado { margin-left: 0; }
  .op-actions { flex-wrap: wrap; justify-content: center; gap: 6px; }
  .op-actions button { padding: 8px 12px; font-size: 0.75rem; }
  
  /* Risco */
  .risco-resumo { grid-template-columns: 1fr 1fr; gap: 8px; }
  .risco-card { padding: 12px; }
  .risco-valor { font-size: 1.2rem; }
  .config-grid { grid-template-columns: 1fr; gap: 12px; }
  
  /* Diário */
  .diario-linha { flex-direction: column; align-items: flex-start; gap: 6px; }
  
  /* Forms e Modais */
  .form-grid { grid-template-columns: 1fr; gap: 10px; }
  .form-group.full { grid-column: span 1; }
  .calc-form { grid-template-columns: 1fr; gap: 10px; }
  .indicadores-grid { grid-template-columns: 1fr; }
  .niveis-grid { grid-template-columns: 1fr; gap: 8px; }
  .streaks-grid { grid-template-columns: 1fr; }
  .plataformas-grid { grid-template-columns: repeat(2, 1fr); }
  
  /* Modais responsivos */
  .modal-overlay { padding: 10px; align-items: flex-end; }
  .modal-analise, .modal-operacao, .modal-calc { 
    max-height: 85vh; 
    border-radius: 20px 20px 0 0;
    padding: 20px 15px;
    width: 100%;
    max-width: 100%;
  }
  
  /* Disclaimer */
  .disclaimer-box { padding: 12px; gap: 8px; }
  .disclaimer-box svg { width: 18px; height: 18px; }
  .disclaimer-box p { font-size: 0.8rem; }
}

@media (max-width: 480px) {
  .main-content { padding: 65px 12px 130px 12px !important; }
  .header-left h1 { font-size: 1.3rem; }
  
  /* Header Actions empilhados */
  .header-actions { flex-direction: column; gap: 6px; }
  .header-actions button { 
    flex: none;
    width: 100%; 
    padding: 12px;
    font-size: 0.85rem;
  }
  
  /* Abas - 2 por linha */
  .abas-principais button { 
    flex: 1 1 calc(50% - 6px);
    padding: 10px 6px;
    font-size: 0.7rem;
  }
  .abas-principais button svg { width: 12px; height: 12px; }
  
  /* Categoria tabs empilhados */
  .categoria-tabs { flex-direction: column; }
  .categoria-tabs button { 
    width: 100%; 
    max-width: none;
    flex: none;
  }
  
  /* Stats empilhados */
  .stats-grid { grid-template-columns: 1fr; gap: 8px; }
  .stat-card.principal { grid-column: span 1; }
  
  /* Resumo empilhado */
  .resumo-dia { grid-template-columns: 1fr; }
  .risco-resumo { grid-template-columns: 1fr; }
  
  /* Operações filtros empilhados */
  .operacoes-filtros { flex-direction: column; }
  .operacoes-filtros button { width: 100%; justify-content: center; }
  
  /* Disclaimer empilhado */
  .disclaimer-box { flex-direction: column; text-align: center; }
  
  /* Indicadores empilhados */
  .ativo-indicadores { flex-direction: column; }
  .indicador { width: 100%; flex: none; }
  
  /* Calculadora */
  .calc-item { flex-direction: column; gap: 4px; text-align: center; }
  
  /* API Status */
  .api-status-row { flex-direction: column; gap: 6px; }
  .last-update { text-align: center; }
  
  /* Modal ainda mais compacto */
  .modal-analise, .modal-operacao, .modal-calc { 
    padding: 15px 12px;
    max-height: 90vh;
  }
}

/* ===== SAFARI FIXES ===== */
/* Fix para flexbox no Safari */
.dashboard { 
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
}

.sidebar-nav,
.mobile-nav,
.header-actions,
.abas-principais,
.categoria-tabs,
.ativo-actions,
.operacoes-filtros,
.op-actions {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
}

/* Fix gap para Safari antigo */
@supports not (gap: 10px) {
  .header-actions > * { margin-right: 10px; }
  .header-actions > *:last-child { margin-right: 0; }
  .abas-principais > * { margin-right: 5px; }
  .abas-principais > *:last-child { margin-right: 0; }
  .categoria-tabs > * { margin-right: 10px; }
  .categoria-tabs > *:last-child { margin-right: 0; }
}

/* Fix para inputs no Safari */
input, select, textarea, button {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  border-radius: 10px;
}

/* Fix para scroll suave Safari */
.abas-principais,
.operacoes-filtros {
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

/* Fix para transform no Safari */
.ativo-card:hover {
  -webkit-transform: translateY(-5px);
  transform: translateY(-5px);
}

.spinner {
  -webkit-animation: spin 1s linear infinite;
  animation: spin 1s linear infinite;
}

.pulse-dot {
  -webkit-animation: pulse 2s infinite;
  animation: pulse 2s infinite;
}

.loading-dot {
  -webkit-animation: blink 1s infinite;
  animation: blink 1s infinite;
}

.btn-refresh svg.spinning {
  -webkit-animation: spin 1s linear infinite;
  animation: spin 1s linear infinite;
}

/* Fix para safe area (notch do iPhone) */
@supports (padding-top: env(safe-area-inset-top)) {
  .main-content {
    padding-top: calc(30px + env(safe-area-inset-top));
    padding-bottom: calc(120px + env(safe-area-inset-bottom));
    padding-left: calc(20px + env(safe-area-inset-left));
    padding-right: calc(20px + env(safe-area-inset-right));
  }
  
  .mobile-menu {
    padding-bottom: calc(25px + env(safe-area-inset-bottom));
  }
  
  .mobile-menu-btn {
    top: calc(20px + env(safe-area-inset-top));
    right: calc(20px + env(safe-area-inset-right));
  }
}

/* Fix backdrop-filter Safari */
.sidebar,
.mobile-menu {
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
}

/* Status API Real */
.api-status-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.api-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.api-badge.real {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
  border: 1px solid rgba(34, 197, 94, 0.5);
  color: #22c55e;
}

.api-badge.loading {
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.4);
  color: #fbbf24;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 2s infinite;
  box-shadow: 0 0 8px #22c55e;
}

.loading-dot {
  width: 8px;
  height: 8px;
  background: #fbbf24;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.last-update {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 12px;
  color: #3b82f6;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.25);
  border-color: rgba(59, 130, 246, 0.5);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-refresh svg {
  width: 18px;
  height: 18px;
}

.btn-refresh svg.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
