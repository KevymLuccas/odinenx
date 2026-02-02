<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans } from '../../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const loading = ref(true)
const ativoSelecionado = ref(null)
const categoriaAtiva = ref('crypto')

// Dados de ativos
const ativos = ref([])
const intervalo = ref(null)

// Base de ativos com dados simulados
const ATIVOS_BASE = {
  crypto: [
    { simbolo: 'BTC', nome: 'Bitcoin', preco: 67500, logo: '₿' },
    { simbolo: 'ETH', nome: 'Ethereum', preco: 3420, logo: 'Ξ' },
    { simbolo: 'BNB', nome: 'Binance Coin', preco: 605, logo: 'B' },
    { simbolo: 'SOL', nome: 'Solana', preco: 178, logo: 'S' },
    { simbolo: 'XRP', nome: 'Ripple', preco: 0.52, logo: 'X' },
    { simbolo: 'ADA', nome: 'Cardano', preco: 0.45, logo: 'A' },
    { simbolo: 'DOGE', nome: 'Dogecoin', preco: 0.12, logo: 'D' },
    { simbolo: 'DOT', nome: 'Polkadot', preco: 7.2, logo: 'P' }
  ],
  acoes: [
    { simbolo: 'PETR4', nome: 'Petrobras', preco: 38.50, logo: 'P' },
    { simbolo: 'VALE3', nome: 'Vale', preco: 62.80, logo: 'V' },
    { simbolo: 'ITUB4', nome: 'Itaú Unibanco', preco: 34.20, logo: 'I' },
    { simbolo: 'BBDC4', nome: 'Bradesco', preco: 14.80, logo: 'B' },
    { simbolo: 'ABEV3', nome: 'Ambev', preco: 12.30, logo: 'A' },
    { simbolo: 'WEGE3', nome: 'Weg', preco: 52.40, logo: 'W' },
    { simbolo: 'MGLU3', nome: 'Magazine Luiza', preco: 11.50, logo: 'M' },
    { simbolo: 'BBAS3', nome: 'Banco do Brasil', preco: 56.90, logo: 'BB' }
  ],
  forex: [
    { simbolo: 'USD/BRL', nome: 'Dólar/Real', preco: 5.15, logo: '$' },
    { simbolo: 'EUR/BRL', nome: 'Euro/Real', preco: 5.62, logo: '€' },
    { simbolo: 'GBP/BRL', nome: 'Libra/Real', preco: 6.58, logo: '£' },
    { simbolo: 'EUR/USD', nome: 'Euro/Dólar', preco: 1.09, logo: '€' },
    { simbolo: 'BTC/USD', nome: 'Bitcoin/Dólar', preco: 67500, logo: '₿' },
    { simbolo: 'JPY/BRL', nome: 'Yen/Real', preco: 0.033, logo: '¥' }
  ]
}

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  carregarAtivos()
  loading.value = false
  
  // Atualizar preços a cada 5 segundos
  intervalo.value = setInterval(atualizarPrecos, 5000)
})

onUnmounted(() => {
  if (intervalo.value) clearInterval(intervalo.value)
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

const carregarAtivos = () => {
  const lista = ATIVOS_BASE[categoriaAtiva.value] || []
  ativos.value = lista.map(ativo => {
    const analise = analisarAtivo(ativo)
    return { ...ativo, ...analise }
  })
}

const atualizarPrecos = () => {
  ativos.value = ativos.value.map(ativo => {
    const variacao = (Math.random() - 0.5) * 2 // -1% a +1%
    const novoPreco = ativo.preco * (1 + variacao / 100)
    const novaVariacao = ((novoPreco - ativo.precoOriginal) / ativo.precoOriginal) * 100
    return {
      ...ativo,
      preco: novoPreco,
      variacao24h: novaVariacao
    }
  })
}

// Algoritmo de análise técnica
const analisarAtivo = (ativo) => {
  const precoBase = ativo.preco
  const variacao24h = (Math.random() - 0.4) * 10 // -4% a +6%
  
  // Simular indicadores técnicos
  const rsi = Math.floor(Math.random() * 100)
  const macd = (Math.random() - 0.5) * 2
  const ema9 = precoBase * (1 + (Math.random() - 0.5) * 0.02)
  const ema21 = precoBase * (1 + (Math.random() - 0.5) * 0.03)
  const sma50 = precoBase * (1 + (Math.random() - 0.5) * 0.05)
  
  // Determinar tendência
  let tendencia = 'lateral'
  let forca = 50
  
  if (rsi < 30) {
    tendencia = 'sobrevenda'
    forca = 30
  } else if (rsi > 70) {
    tendencia = 'sobrecompra'
    forca = 70
  } else if (ema9 > ema21 && macd > 0) {
    tendencia = 'alta'
    forca = 65 + Math.random() * 20
  } else if (ema9 < ema21 && macd < 0) {
    tendencia = 'baixa'
    forca = 35 - Math.random() * 20
  }
  
  // Sinal de trading
  let sinal = 'AGUARDAR'
  let confianca = 50
  let entrada = precoBase
  let alvo = precoBase
  let stop = precoBase
  
  if (tendencia === 'sobrevenda' && rsi < 25) {
    sinal = 'COMPRA'
    confianca = 70 + Math.random() * 15
    entrada = precoBase
    alvo = precoBase * 1.08
    stop = precoBase * 0.96
  } else if (tendencia === 'alta' && macd > 0.5 && rsi < 65) {
    sinal = 'COMPRA'
    confianca = 60 + Math.random() * 20
    entrada = precoBase
    alvo = precoBase * 1.05
    stop = precoBase * 0.97
  } else if (tendencia === 'sobrecompra' && rsi > 75) {
    sinal = 'VENDA'
    confianca = 65 + Math.random() * 15
    entrada = precoBase
    alvo = precoBase * 0.94
    stop = precoBase * 1.04
  } else if (tendencia === 'baixa' && macd < -0.5 && rsi > 35) {
    sinal = 'VENDA'
    confianca = 55 + Math.random() * 20
    entrada = precoBase
    alvo = precoBase * 0.95
    stop = precoBase * 1.03
  }
  
  // Volume relativo simulado
  const volumeRelativo = 0.5 + Math.random() * 2
  
  return {
    precoOriginal: precoBase,
    variacao24h,
    rsi: Math.round(rsi),
    macd: macd.toFixed(3),
    ema9: ema9.toFixed(2),
    ema21: ema21.toFixed(2),
    sma50: sma50.toFixed(2),
    tendencia,
    forca: Math.round(forca),
    sinal,
    confianca: Math.round(confianca),
    entrada: entrada.toFixed(2),
    alvo: alvo.toFixed(2),
    stop: stop.toFixed(2),
    volumeRelativo: volumeRelativo.toFixed(1),
    risco: sinal === 'AGUARDAR' ? 'Neutro' : ((alvo - entrada) / (entrada - stop) > 2 ? 'Baixo' : 'Médio')
  }
}

const mudarCategoria = (cat) => {
  categoriaAtiva.value = cat
  carregarAtivos()
}

const selecionarAtivo = (ativo) => { ativoSelecionado.value = ativo }
const fecharModal = () => { ativoSelecionado.value = null }

const formatarPreco = (preco) => {
  if (preco >= 1000) return preco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (preco >= 1) return preco.toFixed(2)
  return preco.toFixed(4)
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
          <p>Análise técnica com IA em tempo real</p>
        </div>
        <div class="header-right">
          <div class="categoria-tabs">
            <button @click="mudarCategoria('crypto')" :class="{ active: categoriaAtiva === 'crypto' }">🪙 Crypto</button>
            <button @click="mudarCategoria('acoes')" :class="{ active: categoriaAtiva === 'acoes' }">📈 Ações BR</button>
            <button @click="mudarCategoria('forex')" :class="{ active: categoriaAtiva === 'forex' }">💱 Forex</button>
          </div>
        </div>
      </header>

      <div v-if="loading" class="loading-state"><div class="spinner"></div><p>Carregando análises...</p></div>

      <div v-else class="trade-content">
        <div class="disclaimer-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <p><strong>Aviso:</strong> Análises automatizadas não garantem resultados. Trading envolve riscos. Opere com responsabilidade.</p>
        </div>

        <div class="ativos-grid">
          <div v-for="ativo in ativos" :key="ativo.simbolo" class="ativo-card" @click="selecionarAtivo(ativo)">
            <div class="ativo-header">
              <div class="ativo-info">
                <div class="ativo-logo">{{ ativo.logo }}</div>
                <div class="ativo-nomes">
                  <span class="ativo-simbolo">{{ ativo.simbolo }}</span>
                  <span class="ativo-nome">{{ ativo.nome }}</span>
                </div>
              </div>
              <span class="sinal-badge" :class="{ compra: ativo.sinal === 'COMPRA', venda: ativo.sinal === 'VENDA' }">{{ ativo.sinal }}</span>
            </div>
            
            <div class="ativo-preco">
              <span class="preco-atual">R$ {{ formatarPreco(ativo.preco) }}</span>
              <span class="variacao" :class="{ positiva: ativo.variacao24h >= 0, negativa: ativo.variacao24h < 0 }">
                {{ ativo.variacao24h >= 0 ? '+' : '' }}{{ ativo.variacao24h.toFixed(2) }}%
              </span>
            </div>
            
            <div class="indicadores-mini">
              <div class="indicador">
                <span class="ind-label">RSI</span>
                <span class="ind-valor" :class="{ verde: ativo.rsi < 30, vermelho: ativo.rsi > 70 }">{{ ativo.rsi }}</span>
              </div>
              <div class="indicador">
                <span class="ind-label">Tendência</span>
                <span class="ind-valor" :class="{ verde: ativo.tendencia === 'alta', vermelho: ativo.tendencia === 'baixa' }">{{ ativo.tendencia }}</span>
              </div>
              <div class="indicador">
                <span class="ind-label">Confiança</span>
                <span class="ind-valor">{{ ativo.confianca }}%</span>
              </div>
            </div>
            
            <div class="ativo-footer">
              <div class="forca-bar">
                <div class="forca-fill" :style="{ width: ativo.forca + '%', background: ativo.forca > 50 ? '#22c55e' : '#ef4444' }"></div>
              </div>
              <button class="btn-analisar">Ver Análise</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal de Análise -->
      <div v-if="ativoSelecionado" class="modal-overlay" @click.self="fecharModal">
        <div class="modal-analise">
          <button class="modal-close" @click="fecharModal">×</button>
          
          <div class="modal-header-ativo">
            <div class="ativo-logo-grande">{{ ativoSelecionado.logo }}</div>
            <div class="ativo-titulo">
              <h2>{{ ativoSelecionado.simbolo }}</h2>
              <span>{{ ativoSelecionado.nome }}</span>
            </div>
            <div class="preco-destaque">
              <span class="preco-grande">R$ {{ formatarPreco(ativoSelecionado.preco) }}</span>
              <span class="variacao-grande" :class="{ positiva: ativoSelecionado.variacao24h >= 0, negativa: ativoSelecionado.variacao24h < 0 }">
                {{ ativoSelecionado.variacao24h >= 0 ? '+' : '' }}{{ ativoSelecionado.variacao24h.toFixed(2) }}%
              </span>
            </div>
          </div>
          
          <div class="analise-secao">
            <h4>Indicadores Técnicos</h4>
            <div class="indicadores-grid">
              <div class="ind-card">
                <span class="ind-nome">RSI (14)</span>
                <span class="ind-valor-grande" :class="{ verde: ativoSelecionado.rsi < 30, vermelho: ativoSelecionado.rsi > 70 }">{{ ativoSelecionado.rsi }}</span>
                <span class="ind-status">{{ ativoSelecionado.rsi < 30 ? 'Sobrevenda' : ativoSelecionado.rsi > 70 ? 'Sobrecompra' : 'Neutro' }}</span>
              </div>
              <div class="ind-card">
                <span class="ind-nome">MACD</span>
                <span class="ind-valor-grande" :class="{ verde: parseFloat(ativoSelecionado.macd) > 0, vermelho: parseFloat(ativoSelecionado.macd) < 0 }">{{ ativoSelecionado.macd }}</span>
                <span class="ind-status">{{ parseFloat(ativoSelecionado.macd) > 0 ? 'Bullish' : 'Bearish' }}</span>
              </div>
              <div class="ind-card">
                <span class="ind-nome">Volume Rel.</span>
                <span class="ind-valor-grande">{{ ativoSelecionado.volumeRelativo }}x</span>
                <span class="ind-status">{{ parseFloat(ativoSelecionado.volumeRelativo) > 1.5 ? 'Alto' : 'Normal' }}</span>
              </div>
            </div>
          </div>
          
          <div class="analise-secao">
            <h4>Médias Móveis</h4>
            <div class="medias-grid">
              <div class="media-item">
                <span class="media-nome">EMA 9</span>
                <span class="media-valor">R$ {{ ativoSelecionado.ema9 }}</span>
              </div>
              <div class="media-item">
                <span class="media-nome">EMA 21</span>
                <span class="media-valor">R$ {{ ativoSelecionado.ema21 }}</span>
              </div>
              <div class="media-item">
                <span class="media-nome">SMA 50</span>
                <span class="media-valor">R$ {{ ativoSelecionado.sma50 }}</span>
              </div>
            </div>
          </div>
          
          <div class="sinal-box" :class="{ compra: ativoSelecionado.sinal === 'COMPRA', venda: ativoSelecionado.sinal === 'VENDA' }">
            <div class="sinal-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
              <span>Sinal IA</span>
            </div>
            <p class="sinal-texto">{{ ativoSelecionado.sinal }}</p>
            
            <div v-if="ativoSelecionado.sinal !== 'AGUARDAR'" class="trade-setup">
              <div class="setup-item entrada">
                <span class="setup-label">Entrada</span>
                <span class="setup-valor">R$ {{ ativoSelecionado.entrada }}</span>
              </div>
              <div class="setup-item alvo">
                <span class="setup-label">Alvo</span>
                <span class="setup-valor">R$ {{ ativoSelecionado.alvo }}</span>
              </div>
              <div class="setup-item stop">
                <span class="setup-label">Stop</span>
                <span class="setup-valor">R$ {{ ativoSelecionado.stop }}</span>
              </div>
            </div>
            
            <div class="confianca-meter">
              <div class="meter-fill" :style="{ width: ativoSelecionado.confianca + '%' }"></div>
            </div>
            <span class="confianca-label">{{ ativoSelecionado.confianca }}% de confiança | Risco: {{ ativoSelecionado.risco }}</span>
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
.categoria-tabs { display: flex; gap: 10px; }
.categoria-tabs button { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 10px 20px; color: rgba(255, 255, 255, 0.6); cursor: pointer; transition: all 0.3s; font-size: 0.9rem; }
.categoria-tabs button:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
.categoria-tabs button.active { background: #fff; color: #000; border-color: #fff; }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 100px 20px; }
.spinner { width: 50px; height: 50px; border: 3px solid rgba(255, 255, 255, 0.1); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-state p { margin-top: 20px; color: rgba(255, 255, 255, 0.5); }

.disclaimer-box { display: flex; align-items: center; gap: 15px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 12px; padding: 15px 20px; margin-bottom: 30px; }
.disclaimer-box svg { width: 24px; height: 24px; stroke: #fbbf24; flex-shrink: 0; }
.disclaimer-box p { font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); }

.ativos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
.ativo-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.3s; }
.ativo-card:hover { transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.05); }
.ativo-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.ativo-info { display: flex; align-items: center; gap: 12px; }
.ativo-logo { width: 45px; height: 45px; background: rgba(255, 255, 255, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: 700; }
.ativo-nomes { display: flex; flex-direction: column; }
.ativo-simbolo { font-weight: 700; font-size: 1.1rem; }
.ativo-nome { font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); }
.sinal-badge { padding: 6px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; background: rgba(255, 255, 255, 0.1); }
.sinal-badge.compra { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.sinal-badge.venda { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.ativo-preco { display: flex; align-items: baseline; gap: 12px; margin-bottom: 15px; }
.preco-atual { font-size: 1.5rem; font-weight: 700; }
.variacao { font-size: 0.9rem; font-weight: 600; }
.variacao.positiva { color: #22c55e; }
.variacao.negativa { color: #ef4444; }
.indicadores-mini { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }
.indicador { display: flex; flex-direction: column; align-items: center; flex: 1; padding: 10px; background: rgba(255, 255, 255, 0.03); border-radius: 8px; }
.ind-label { font-size: 0.7rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 4px; }
.ind-valor { font-size: 0.85rem; font-weight: 600; text-transform: capitalize; }
.ind-valor.verde { color: #22c55e; }
.ind-valor.vermelho { color: #ef4444; }
.ativo-footer { display: flex; align-items: center; gap: 15px; }
.forca-bar { flex: 1; height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; overflow: hidden; }
.forca-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.btn-analisar { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 8px 16px; color: #fff; font-size: 0.85rem; cursor: pointer; transition: all 0.3s; }
.btn-analisar:hover { background: #fff; color: #000; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-analise { background: #111; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; width: 100%; max-width: 600px; max-height: 90vh; overflow-y: auto; padding: 30px; position: relative; }
.modal-close { position: absolute; top: 15px; right: 15px; width: 40px; height: 40px; background: rgba(255, 255, 255, 0.1); border: none; border-radius: 50%; color: #fff; font-size: 1.5rem; cursor: pointer; transition: all 0.3s; }
.modal-close:hover { background: #ef4444; }
.modal-header-ativo { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
.ativo-logo-grande { width: 60px; height: 60px; background: rgba(255, 255, 255, 0.1); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 700; }
.ativo-titulo { flex: 1; }
.ativo-titulo h2 { font-size: 1.5rem; margin-bottom: 5px; }
.ativo-titulo span { color: rgba(255, 255, 255, 0.5); }
.preco-destaque { text-align: right; }
.preco-grande { display: block; font-size: 1.8rem; font-weight: 700; }
.variacao-grande { font-size: 1rem; }
.variacao-grande.positiva { color: #22c55e; }
.variacao-grande.negativa { color: #ef4444; }
.analise-secao { margin-bottom: 25px; }
.analise-secao h4 { font-size: 0.9rem; color: rgba(255, 255, 255, 0.5); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
.indicadores-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.ind-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; text-align: center; }
.ind-nome { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; }
.ind-valor-grande { display: block; font-size: 1.5rem; font-weight: 700; margin-bottom: 5px; }
.ind-valor-grande.verde { color: #22c55e; }
.ind-valor-grande.vermelho { color: #ef4444; }
.ind-status { font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); }
.medias-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.media-item { background: rgba(255, 255, 255, 0.03); border-radius: 10px; padding: 12px; text-align: center; }
.media-nome { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px; }
.media-valor { font-weight: 600; }
.sinal-box { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; text-align: center; }
.sinal-box.compra { background: rgba(34, 197, 94, 0.1); border-color: rgba(34, 197, 94, 0.3); }
.sinal-box.venda { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); }
.sinal-header { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 15px; }
.sinal-header svg { width: 24px; height: 24px; stroke: #3b82f6; }
.sinal-box.compra .sinal-header svg { stroke: #22c55e; }
.sinal-box.venda .sinal-header svg { stroke: #ef4444; }
.sinal-header span { font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; }
.sinal-texto { font-size: 2rem; font-weight: 800; margin-bottom: 20px; }
.sinal-box.compra .sinal-texto { color: #22c55e; }
.sinal-box.venda .sinal-texto { color: #ef4444; }
.trade-setup { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.setup-item { padding: 12px; border-radius: 10px; text-align: center; }
.setup-item.entrada { background: rgba(59, 130, 246, 0.1); }
.setup-item.alvo { background: rgba(34, 197, 94, 0.1); }
.setup-item.stop { background: rgba(239, 68, 68, 0.1); }
.setup-label { display: block; font-size: 0.75rem; color: rgba(255, 255, 255, 0.5); margin-bottom: 5px; }
.setup-valor { font-weight: 700; }
.setup-item.entrada .setup-valor { color: #3b82f6; }
.setup-item.alvo .setup-valor { color: #22c55e; }
.setup-item.stop .setup-valor { color: #ef4444; }
.confianca-meter { height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
.meter-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #60a5fa); border-radius: 4px; transition: width 0.5s; }
.sinal-box.compra .meter-fill { background: linear-gradient(90deg, #22c55e, #4ade80); }
.sinal-box.venda .meter-fill { background: linear-gradient(90deg, #ef4444, #f87171); }
.confianca-label { font-size: 0.9rem; color: rgba(255, 255, 255, 0.6); }

@media (max-width: 968px) {
  .sidebar { display: none; }
  .mobile-menu-btn { display: flex; }
  .mobile-overlay { display: block; }
  .mobile-menu { display: block; }
  .main-content { margin-left: 0; padding: 20px; padding-bottom: 100px; }
  .ativos-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .categoria-tabs { width: 100%; overflow-x: auto; }
}

@media (max-width: 480px) {
  .indicadores-grid { grid-template-columns: 1fr; }
  .medias-grid { grid-template-columns: 1fr; }
  .trade-setup { grid-template-columns: 1fr; }
  .modal-header-ativo { flex-direction: column; text-align: center; }
  .preco-destaque { text-align: center; }
}
</style>
