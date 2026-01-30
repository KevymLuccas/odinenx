<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans } from '../../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const activeTab = ref('mercado')
const atletas = ref([])
const clubes = ref({})
const partidas = ref([])
const escalacao = ref([])
const reservas = ref([])
const cartoletas = ref(100)
const filtroPos = ref('todas')
const filtroBusca = ref('')
const statusMercado = ref({})
const analisando = ref(false)

// Posições
const POSICOES = {
  1: { nome: 'Goleiro', abrev: 'GOL', cor: '#f59e0b' },
  2: { nome: 'Lateral', abrev: 'LAT', cor: '#3b82f6' },
  3: { nome: 'Zagueiro', abrev: 'ZAG', cor: '#10b981' },
  4: { nome: 'Meia', abrev: 'MEI', cor: '#8b5cf6' },
  5: { nome: 'Atacante', abrev: 'ATA', cor: '#ef4444' },
  6: { nome: 'Técnico', abrev: 'TEC', cor: '#6b7280' }
}

// Esquema tático fixo
const ESQUEMA = { 1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1 }

// Status dos atletas
const STATUS = {
  2: { nome: 'Dúvida', emoji: '⚠️', cor: '#ffaa00' },
  3: { nome: 'Suspenso', emoji: '🟡', cor: '#ffff00' },
  5: { nome: 'Contundido', emoji: '🏥', cor: '#ff6666' },
  6: { nome: 'Nulo', emoji: '❓', cor: '#888888' },
  7: { nome: 'Provável', emoji: '✅', cor: '#00ff88' }
}

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

// Computed
const atletasFiltrados = computed(() => {
  let lista = atletas.value
  
  if (filtroPos.value !== 'todas') {
    lista = lista.filter(a => a.posicao_id == filtroPos.value)
  }
  
  if (filtroBusca.value) {
    const busca = filtroBusca.value.toLowerCase()
    lista = lista.filter(a => 
      a.apelido?.toLowerCase().includes(busca) ||
      clubes.value[a.clube_id]?.nome?.toLowerCase().includes(busca)
    )
  }
  
  return lista.sort((a, b) => (b.media_num || 0) - (a.media_num || 0))
})

const gastoTotal = computed(() => {
  return escalacao.value.reduce((sum, a) => sum + (a.preco_num || 0), 0)
})

const saldoRestante = computed(() => {
  return cartoletas.value - gastoTotal.value
})

const pontuacaoEstimada = computed(() => {
  return escalacao.value.reduce((sum, a) => sum + (a.score || 0), 0)
})

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  await carregarDados()
})

// Carregar dados da API
const carregarDados = async () => {
  loading.value = true
  
  try {
    const resMercado = await fetch('https://api.cartola.globo.com/atletas/mercado')
    const dataMercado = await resMercado.json()
    
    atletas.value = dataMercado.atletas?.map(a => ({
      ...a,
      score: calcularScore(a)
    })) || []
    clubes.value = dataMercado.clubes || {}
    
    const resStatus = await fetch('https://api.cartola.globo.com/mercado/status')
    statusMercado.value = await resStatus.json()
    
    const resPartidas = await fetch('https://api.cartola.globo.com/partidas')
    const dataPartidas = await resPartidas.json()
    partidas.value = dataPartidas.partidas || []
    
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loading.value = false
  }
}

// Calcular score do atleta
const calcularScore = (atleta) => {
  const media = atleta.media_num || 0
  const preco = Math.max(atleta.preco_num || 1, 0.1)
  const variacao = atleta.variacao_num || 0
  const jogos = atleta.jogos_num || 0
  const status = atleta.status_id || 0
  
  const custoBeneficio = (media / preco) * 2
  const momentum = variacao > 0 ? 1 + (variacao * 0.1) : 1 - (Math.abs(variacao) * 0.05)
  const exp = Math.min(jogos / 3, 1.5)
  
  let score = (media * 1.5 + custoBeneficio * 2) * momentum * (0.7 + exp * 0.3)
  
  if (status === 2) score *= 0.7
  else if (status !== 7) score *= 0.5
  
  return Math.round(score * 100) / 100
}

// Escalar automaticamente com IA
const escalarAutomatico = () => {
  analisando.value = true
  escalacao.value = []
  reservas.value = []
  
  setTimeout(() => {
    const atletasValidos = atletas.value.filter(a => 
      a.status_id === 7 && 
      (a.preco_num || 0) <= saldoRestante.value + gastoTotal.value
    )
    
    const porPosicao = {}
    for (const pos in POSICOES) {
      porPosicao[pos] = atletasValidos
        .filter(a => a.posicao_id == pos)
        .sort((a, b) => (b.score || 0) - (a.score || 0))
    }
    
    const novaEscalacao = []
    let gastoAtual = 0
    
    for (const [posId, qtd] of Object.entries(ESQUEMA)) {
      const disponiveis = porPosicao[posId] || []
      let adicionados = 0
      
      for (const atleta of disponiveis) {
        if (adicionados >= qtd) break
        if (gastoAtual + atleta.preco_num <= cartoletas.value) {
          novaEscalacao.push(atleta)
          gastoAtual += atleta.preco_num
          adicionados++
        }
      }
    }
    
    escalacao.value = novaEscalacao
    
    const reservasTemp = []
    const idsEscalados = new Set(novaEscalacao.map(a => a.atleta_id))
    
    for (const posId of [1, 2, 3, 4, 5]) {
      const disponiveis = porPosicao[posId]?.filter(a => !idsEscalados.has(a.atleta_id)) || []
      if (disponiveis.length > 0) {
        reservasTemp.push(disponiveis[0])
      }
    }
    
    reservas.value = reservasTemp
    analisando.value = false
  }, 1500)
}

// Adicionar atleta à escalação
const adicionarAtleta = (atleta) => {
  const posId = atleta.posicao_id
  const qtdPos = escalacao.value.filter(a => a.posicao_id === posId).length
  const maxPos = ESQUEMA[posId] || 0
  
  if (qtdPos >= maxPos) {
    alert(`Já tem ${maxPos} ${POSICOES[posId]?.nome}(s) na escalação!`)
    return
  }
  
  if (gastoTotal.value + atleta.preco_num > cartoletas.value) {
    alert('Cartoletas insuficientes!')
    return
  }
  
  if (escalacao.value.find(a => a.atleta_id === atleta.atleta_id)) {
    alert('Atleta já está na escalação!')
    return
  }
  
  escalacao.value.push(atleta)
}

// Remover atleta da escalação
const removerAtleta = (index) => {
  escalacao.value.splice(index, 1)
}

// Limpar escalação
const limparEscalacao = () => {
  escalacao.value = []
  reservas.value = []
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}
</script>

<template>
  <div class="dashboard">
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
        <router-link to="/dashboard" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          Dashboard
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
        <router-link to="/cartola" class="nav-item active">
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

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-left">
          <h1>
            <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2a10 10 0 0 0-7.07 17.07M12 2a10 10 0 0 1 7.07 17.07"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            Cartola FC
          </h1>
          <p>Análise inteligente para o Brasileirão</p>
        </div>
        <div class="header-right">
          <div class="header-stats" v-if="!loading">
            <div class="stat-pill">
              <span class="label">Rodada</span>
              <span class="value">{{ statusMercado.rodada_atual || '--' }}</span>
            </div>
            <div class="stat-pill" :class="{ 'aberto': statusMercado.status_mercado === 1 }">
              <span class="label">Mercado</span>
              <span class="value">{{ statusMercado.status_mercado === 1 ? 'Aberto' : 'Fechado' }}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Loading -->
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
      </div>

      <!-- Content -->
      <div v-else class="dashboard-content">
        <!-- Tabs -->
        <div class="cartola-tabs">
          <button 
            v-for="tab in [{id: 'mercado', icon: 'grid', label: 'Mercado'}, {id: 'escalacao', icon: 'users', label: 'Escalação IA'}, {id: 'confrontos', icon: 'zap', label: 'Confrontos'}]" 
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="{ active: activeTab === tab.id }"
            class="tab-btn"
          >
            <svg v-if="tab.icon === 'grid'" class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
            </svg>
            <svg v-if="tab.icon === 'users'" class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <svg v-if="tab.icon === 'zap'" class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab: Mercado -->
        <div v-if="activeTab === 'mercado'" class="tab-content">
          <div class="mercado-header">
            <div class="filtros">
              <div class="filtro-group">
                <label>Posição</label>
                <select v-model="filtroPos">
                  <option value="todas">Todas</option>
                  <option v-for="(pos, id) in POSICOES" :key="id" :value="id">
                    {{ pos.nome }}
                  </option>
                </select>
              </div>
              <div class="filtro-group">
                <label>Buscar</label>
                <input type="text" v-model="filtroBusca" placeholder="Nome ou time...">
              </div>
            </div>
            <div class="mercado-info">
              <span>{{ atletasFiltrados.length }} atletas encontrados</span>
            </div>
          </div>

          <div class="atletas-grid">
            <div 
              v-for="atleta in atletasFiltrados.slice(0, 50)" 
              :key="atleta.atleta_id"
              class="atleta-card"
              @click="adicionarAtleta(atleta)"
            >
              <div class="atleta-header">
                <div class="pos-badge" :style="{ background: POSICOES[atleta.posicao_id]?.cor }">
                  {{ POSICOES[atleta.posicao_id]?.abrev }}
                </div>
                <div class="status-badge" :style="{ color: STATUS[atleta.status_id]?.cor }">
                  {{ STATUS[atleta.status_id]?.emoji || '❓' }}
                </div>
              </div>
              <div class="atleta-foto">
                <img :src="`https://s.sde.globo.com/media/pessoa_cartolafc/foto/${atleta.atleta_id}/100x100`" 
                     @error="$event.target.src = '/icone.webp'"
                     :alt="atleta.apelido">
              </div>
              <div class="atleta-info">
                <h4>{{ atleta.apelido }}</h4>
                <p>{{ clubes[atleta.clube_id]?.nome || 'Time' }}</p>
              </div>
              <div class="atleta-stats">
                <div class="stat">
                  <span class="label">Média</span>
                  <span class="value">{{ (atleta.media_num || 0).toFixed(1) }}</span>
                </div>
                <div class="stat">
                  <span class="label">Preço</span>
                  <span class="value price">C$ {{ (atleta.preco_num || 0).toFixed(1) }}</span>
                </div>
                <div class="stat">
                  <span class="label">Score</span>
                  <span class="value score">{{ atleta.score || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Escalação -->
        <div v-if="activeTab === 'escalacao'" class="tab-content">
          <div class="escalacao-header">
            <div class="orcamento">
              <div class="orcamento-item">
                <span class="label">Cartoletas</span>
                <input type="number" v-model.number="cartoletas" min="0" max="999" step="5">
              </div>
              <div class="orcamento-item">
                <span class="label">Gasto</span>
                <span class="value gasto">C$ {{ gastoTotal.toFixed(2) }}</span>
              </div>
              <div class="orcamento-item">
                <span class="label">Saldo</span>
                <span class="value saldo" :class="{ negativo: saldoRestante < 0 }">
                  C$ {{ saldoRestante.toFixed(2) }}
                </span>
              </div>
              <div class="orcamento-item">
                <span class="label">Pts Estimados</span>
                <span class="value pontos">{{ pontuacaoEstimada.toFixed(1) }}</span>
              </div>
            </div>
            <div class="escalacao-actions">
              <button @click="escalarAutomatico" class="btn-primary" :disabled="analisando">
                <svg v-if="!analisando" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                <div v-else class="mini-spinner"></div>
                {{ analisando ? 'Analisando...' : 'Escalar com IA' }}
              </button>
              <button @click="limparEscalacao" class="btn-secondary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                Limpar
              </button>
            </div>
          </div>

          <!-- Escalação Grid -->
          <div class="escalacao-grid">
            <div v-for="atleta in escalacao" :key="atleta.atleta_id" class="escalacao-card">
              <div class="pos-badge" :style="{ background: POSICOES[atleta.posicao_id]?.cor }">
                {{ POSICOES[atleta.posicao_id]?.abrev }}
              </div>
              <img :src="`https://s.sde.globo.com/media/pessoa_cartolafc/foto/${atleta.atleta_id}/100x100`" 
                   @error="$event.target.src = '/icone.webp'"
                   class="foto">
              <div class="info">
                <span class="nome">{{ atleta.apelido }}</span>
                <span class="time">{{ clubes[atleta.clube_id]?.nome }}</span>
              </div>
              <div class="stats">
                <span class="score">{{ atleta.score }} pts</span>
                <span class="preco">C$ {{ atleta.preco_num?.toFixed(1) }}</span>
              </div>
              <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="escalacao.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="11" x2="19" y2="17"/>
              <line x1="16" y1="14" x2="22" y2="14"/>
            </svg>
            <h4>Nenhum atleta escalado</h4>
            <p>Clique em "Escalar com IA" ou adicione atletas manualmente no Mercado.</p>
          </div>

          <!-- Reservas -->
          <div v-if="reservas.length > 0" class="reservas-section">
            <h3>Banco de Reservas</h3>
            <div class="reservas-grid">
              <div v-for="atleta in reservas" :key="atleta.atleta_id" class="reserva-card">
                <div class="pos-badge small" :style="{ background: POSICOES[atleta.posicao_id]?.cor }">
                  {{ POSICOES[atleta.posicao_id]?.abrev }}
                </div>
                <span class="nome">{{ atleta.apelido }}</span>
                <span class="score">{{ atleta.score }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Confrontos -->
        <div v-if="activeTab === 'confrontos'" class="tab-content">
          <div class="confrontos-grid">
            <div v-for="partida in partidas" :key="partida.partida_id" class="confronto-card">
              <div class="confronto-header">
                <span>Rodada {{ statusMercado.rodada_atual }}</span>
              </div>
              <div class="confronto-times">
                <div class="time">
                  <img :src="clubes[partida.clube_casa_id]?.escudos?.['60x60']" 
                       @error="$event.target.src = '/icone.webp'">
                  <span>{{ clubes[partida.clube_casa_id]?.nome || 'Casa' }}</span>
                </div>
                <div class="versus">VS</div>
                <div class="time">
                  <img :src="clubes[partida.clube_visitante_id]?.escudos?.['60x60']" 
                       @error="$event.target.src = '/icone.webp'">
                  <span>{{ clubes[partida.clube_visitante_id]?.nome || 'Fora' }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="partidas.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            <h4>Nenhum confronto disponível</h4>
            <p>Os jogos da rodada aparecerão aqui quando o mercado abrir.</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ===== LAYOUT PRINCIPAL ===== */
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #000;
  color: #fff;
}

/* ===== SIDEBAR ===== */
.sidebar {
  width: 260px;
  background: rgba(10, 10, 10, 0.95);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  z-index: 100;
}

.sidebar-header {
  padding: 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  height: 40px;
  width: auto;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 15px;
  display: flex;
  flex-direction: column;
  gap: 5px;
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
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  transition: all 0.3s;
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.plan-badge-sidebar {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 8px;
  text-align: center;
  font-weight: 600;
  margin-bottom: 15px;
  font-size: 0.9rem;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.logout-icon {
  width: 18px;
  height: 18px;
}

/* ===== MAIN CONTENT ===== */
.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 30px;
}

/* ===== HEADER ===== */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.8rem;
  font-weight: 800;
}

.title-icon {
  width: 32px;
  height: 32px;
}

.header-left p {
  color: rgba(255, 255, 255, 0.5);
  margin-top: 5px;
}

.header-stats {
  display: flex;
  gap: 15px;
}

.stat-pill {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px 18px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.stat-pill.aberto {
  border-color: rgba(34, 197, 94, 0.5);
  background: rgba(34, 197, 94, 0.1);
}

.stat-pill .label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.stat-pill .value {
  font-weight: 700;
}

.stat-pill.aberto .value {
  color: #22c55e;
}

/* ===== LOADING ===== */
.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50vh;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== TABS ===== */
.cartola-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.tab-btn.active {
  background: #fff;
  border-color: #fff;
  color: #000;
}

.tab-icon {
  width: 18px;
  height: 18px;
}

/* ===== MERCADO ===== */
.mercado-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 15px;
}

.filtros {
  display: flex;
  gap: 15px;
}

.filtro-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filtro-group label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.filtro-group select,
.filtro-group input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 12px 16px;
  border-radius: 10px;
  min-width: 180px;
}

.filtro-group select:focus,
.filtro-group input:focus {
  outline: none;
  border-color: #fff;
}

.mercado-info {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

/* ===== ATLETAS GRID ===== */
.atletas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.atleta-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 18px;
  cursor: pointer;
  transition: all 0.3s;
}

.atleta-card:hover {
  border-color: #fff;
  transform: translateY(-3px);
}

.atleta-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.pos-badge {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
}

.atleta-foto {
  text-align: center;
  margin-bottom: 12px;
}

.atleta-foto img {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.atleta-info {
  text-align: center;
  margin-bottom: 15px;
}

.atleta-info h4 {
  font-size: 0.95rem;
  margin-bottom: 4px;
}

.atleta-info p {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.atleta-stats {
  display: flex;
  justify-content: space-between;
}

.atleta-stats .stat {
  text-align: center;
}

.atleta-stats .label {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 3px;
}

.atleta-stats .value {
  font-weight: 700;
  font-size: 0.9rem;
}

.atleta-stats .value.price {
  color: #22c55e;
}

.atleta-stats .value.score {
  color: #3b82f6;
}

/* ===== ESCALAÇÃO ===== */
.escalacao-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 20px;
}

.orcamento {
  display: flex;
  gap: 25px;
  flex-wrap: wrap;
}

.orcamento-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.orcamento-item .label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.orcamento-item input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 10px 14px;
  border-radius: 10px;
  width: 110px;
  font-weight: 700;
}

.orcamento-item .value {
  font-size: 1.3rem;
  font-weight: 700;
}

.orcamento-item .gasto { color: #ef4444; }
.orcamento-item .saldo { color: #22c55e; }
.orcamento-item .saldo.negativo { color: #ef4444; }
.orcamento-item .pontos { color: #3b82f6; }

.escalacao-actions {
  display: flex;
  gap: 12px;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: none;
  color: #000;
  padding: 14px 28px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.mini-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 14px 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.btn-secondary svg {
  width: 16px;
  height: 16px;
}

/* ===== ESCALAÇÃO GRID ===== */
.escalacao-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.escalacao-card {
  display: flex;
  align-items: center;
  gap: 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 15px;
  position: relative;
}

.escalacao-card .foto {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}

.escalacao-card .info {
  flex: 1;
}

.escalacao-card .nome {
  display: block;
  font-weight: 600;
}

.escalacao-card .time {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.escalacao-card .stats {
  text-align: right;
}

.escalacao-card .score {
  display: block;
  font-weight: 700;
  color: #3b82f6;
}

.escalacao-card .preco {
  font-size: 0.8rem;
  color: #22c55e;
}

.escalacao-card .remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(239, 68, 68, 0.2);
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.escalacao-card:hover .remove-btn {
  opacity: 1;
}

.escalacao-card .remove-btn svg {
  width: 14px;
  height: 14px;
  stroke: #ef4444;
}

/* ===== EMPTY STATE ===== */
.empty-state {
  text-align: center;
  padding: 60px 40px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.empty-state svg {
  width: 60px;
  height: 60px;
  stroke: rgba(255, 255, 255, 0.3);
  margin-bottom: 20px;
}

.empty-state h4 {
  margin-bottom: 10px;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.5);
}

/* ===== RESERVAS ===== */
.reservas-section {
  margin-top: 30px;
  padding-top: 25px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.reservas-section h3 {
  font-size: 1.1rem;
  margin-bottom: 15px;
  color: rgba(255, 255, 255, 0.7);
}

.reservas-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.reserva-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 18px;
  border-radius: 12px;
}

.reserva-card .pos-badge.small {
  padding: 4px 10px;
  font-size: 0.65rem;
}

.reserva-card .nome {
  font-weight: 600;
}

.reserva-card .score {
  color: #3b82f6;
  font-weight: 700;
}

/* ===== CONFRONTOS ===== */
.confrontos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.confronto-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  overflow: hidden;
}

.confronto-header {
  padding: 12px 18px;
  background: rgba(255, 255, 255, 0.03);
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.confronto-times {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 25px;
}

.confronto-times .time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.confronto-times .time img {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.confronto-times .time span {
  font-weight: 600;
  text-align: center;
  font-size: 0.9rem;
}

.versus {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 700;
  padding: 0 15px;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {
  .sidebar {
    width: 80px;
  }
  
  .sidebar-header {
    padding: 15px;
    text-align: center;
  }
  
  .sidebar-logo {
    height: 30px;
  }
  
  .nav-item {
    justify-content: center;
    padding: 15px;
  }
  
  .nav-item span,
  .sidebar-nav .nav-item:not(.nav-icon) {
    display: none;
  }
  
  .plan-badge-sidebar,
  .logout-btn span {
    display: none;
  }
  
  .logout-btn {
    justify-content: center;
  }
  
  .main-content {
    margin-left: 80px;
  }
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  
  .main-content {
    margin-left: 0;
    padding: 20px;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .cartola-tabs {
    flex-wrap: wrap;
  }
  
  .tab-btn {
    flex: 1;
    justify-content: center;
    min-width: 100px;
  }
  
  .atletas-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
  
  .escalacao-grid {
    grid-template-columns: 1fr;
  }
}
</style>
