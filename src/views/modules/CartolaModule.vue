<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'

const router = useRouter()
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

// Força dos times (histórico)
const FORCA_TIMES = {
  262: { nome: 'Flamengo', ataque: 88, defesa: 75 },
  263: { nome: 'Botafogo', ataque: 82, defesa: 78 },
  264: { nome: 'Fluminense', ataque: 72, defesa: 70 },
  275: { nome: 'Palmeiras', ataque: 90, defesa: 85 },
  276: { nome: 'São Paulo', ataque: 78, defesa: 80 },
  277: { nome: 'Santos', ataque: 70, defesa: 65 },
  282: { nome: 'Atlético-MG', ataque: 80, defesa: 72 },
  283: { nome: 'Cruzeiro', ataque: 75, defesa: 70 },
  284: { nome: 'Grêmio', ataque: 76, defesa: 74 },
  285: { nome: 'Internacional', ataque: 78, defesa: 76 },
  286: { nome: 'Vasco', ataque: 68, defesa: 65 },
  287: { nome: 'Bahia', ataque: 74, defesa: 68 },
  290: { nome: 'Corinthians', ataque: 75, defesa: 70 },
  293: { nome: 'Fortaleza', ataque: 76, defesa: 78 },
  356: { nome: 'Athletico-PR', ataque: 74, defesa: 72 },
  315: { nome: 'RB Bragantino', ataque: 72, defesa: 70 }
}

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

// Carregar dados da API
const carregarDados = async () => {
  loading.value = true
  
  try {
    // Mercado
    const resMercado = await fetch('https://api.cartola.globo.com/atletas/mercado')
    const dataMercado = await resMercado.json()
    
    atletas.value = dataMercado.atletas?.map(a => ({
      ...a,
      score: calcularScore(a)
    })) || []
    clubes.value = dataMercado.clubes || {}
    
    // Status do mercado
    const resStatus = await fetch('https://api.cartola.globo.com/mercado/status')
    statusMercado.value = await resStatus.json()
    
    // Partidas
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
  
  // Custo-benefício
  const custoBeneficio = (media / preco) * 2
  
  // Momentum (variação positiva = boa fase)
  const momentum = variacao > 0 ? 1 + (variacao * 0.1) : 1 - (Math.abs(variacao) * 0.05)
  
  // Experiência
  const exp = Math.min(jogos / 3, 1.5)
  
  // Score base
  let score = (media * 1.5 + custoBeneficio * 2) * momentum * (0.7 + exp * 0.3)
  
  // Penalidade por status
  if (status === 2) score *= 0.7  // Dúvida
  else if (status !== 7) score *= 0.5  // Não provável
  
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
    
    // Separar por posição e ordenar por score
    const porPosicao = {}
    for (const pos in POSICOES) {
      porPosicao[pos] = atletasValidos
        .filter(a => a.posicao_id == pos)
        .sort((a, b) => (b.score || 0) - (a.score || 0))
    }
    
    // Montar escalação respeitando esquema e orçamento
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
    
    // Gerar reservas (1 de cada posição principal)
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

// Analisar confronto
const analisarConfronto = (partida) => {
  const mandante = FORCA_TIMES[partida.clube_casa_id] || { ataque: 60, defesa: 60 }
  const visitante = FORCA_TIMES[partida.clube_visitante_id] || { ataque: 60, defesa: 60 }
  
  const forcaMandante = (mandante.ataque * 1.1 + (100 - visitante.defesa)) / 2
  const forcaVisitante = (visitante.ataque * 0.9 + (100 - mandante.defesa)) / 2
  
  return {
    favorito: forcaMandante > forcaVisitante ? 'casa' : 'fora',
    probabilidade: Math.round(Math.max(forcaMandante, forcaVisitante))
  }
}

onMounted(() => {
  carregarDados()
})
</script>

<template>
  <div class="cartola-module">
    <!-- Header -->
    <div class="module-header">
      <button @click="router.push('/dashboard')" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Voltar
      </button>
      <div class="header-info">
        <h1>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="title-icon">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2a10 10 0 0 0-7.07 17.07M12 2a10 10 0 0 1 7.07 17.07"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          Módulo Cartola FC
        </h1>
        <p>Análise inteligente para o Brasileirão</p>
      </div>
      <div class="header-stats" v-if="!loading">
        <div class="stat-pill">
          <span class="label">Rodada</span>
          <span class="value">{{ statusMercado.rodada_atual || '--' }}</span>
        </div>
        <div class="stat-pill" :class="{ 'aberto': statusMercado.status_mercado === 1 }">
          <span class="label">Mercado</span>
          <span class="value">{{ statusMercado.status_mercado === 1 ? 'Aberto' : 'Fechado' }}</span>
        </div>
        <div class="stat-pill">
          <span class="label">Atletas</span>
          <span class="value">{{ atletas.length }}</span>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="loader"></div>
      <p>Carregando dados do Cartola FC...</p>
    </div>

    <!-- Content -->
    <div v-else class="module-content">
      <!-- Tabs -->
      <div class="tabs">
        <button 
          v-for="tab in ['mercado', 'escalacao', 'confrontos']" 
          :key="tab"
          @click="activeTab = tab"
          :class="{ active: activeTab === tab }"
          class="tab-btn"
        >
          <svg v-if="tab === 'mercado'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3h18v18H3zM21 9H3M9 21V9"/>
          </svg>
          <svg v-if="tab === 'escalacao'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <svg v-if="tab === 'confrontos'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          {{ tab === 'mercado' ? 'Mercado' : tab === 'escalacao' ? 'Escalação IA' : 'Confrontos' }}
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
            <div class="filtro-group search">
              <label>Buscar</label>
              <input type="text" v-model="filtroBusca" placeholder="Nome ou time...">
            </div>
          </div>
          <div class="mercado-stats">
            <span>{{ atletasFiltrados.length }} atletas</span>
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
                <span class="label">Score IA</span>
                <span class="value score">{{ atleta.score || 0 }}</span>
              </div>
            </div>
            <button class="add-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </button>
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
            <button @click="escalarAutomatico" class="btn-escalar" :disabled="analisando">
              <svg v-if="!analisando" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <div v-else class="mini-loader"></div>
              {{ analisando ? 'Analisando...' : 'Escalar com IA' }}
            </button>
            <button @click="limparEscalacao" class="btn-limpar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              Limpar
            </button>
          </div>
        </div>

        <!-- Campo Visual -->
        <div class="campo-container">
          <div class="campo">
            <!-- Técnico -->
            <div class="linha tecnico">
              <div 
                v-for="(atleta, i) in escalacao.filter(a => a.posicao_id === 6)" 
                :key="i"
                class="jogador-slot tecnico"
              >
                <div class="jogador-card filled">
                  <span class="pos">TEC</span>
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="pts">{{ atleta.score }}</span>
                  <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">×</button>
                </div>
              </div>
              <div v-if="escalacao.filter(a => a.posicao_id === 6).length === 0" class="jogador-slot empty">
                <span class="pos">TEC</span>
              </div>
            </div>
            
            <!-- Atacantes -->
            <div class="linha atacantes">
              <div 
                v-for="(atleta, i) in escalacao.filter(a => a.posicao_id === 5)" 
                :key="i"
                class="jogador-slot"
              >
                <div class="jogador-card filled ata">
                  <span class="pos">ATA</span>
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="pts">{{ atleta.score }}</span>
                  <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">×</button>
                </div>
              </div>
              <div v-for="i in Math.max(0, 2 - escalacao.filter(a => a.posicao_id === 5).length)" :key="'e-ata-'+i" class="jogador-slot empty">
                <span class="pos">ATA</span>
              </div>
            </div>
            
            <!-- Meias -->
            <div class="linha meias">
              <div 
                v-for="(atleta, i) in escalacao.filter(a => a.posicao_id === 4)" 
                :key="i"
                class="jogador-slot"
              >
                <div class="jogador-card filled mei">
                  <span class="pos">MEI</span>
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="pts">{{ atleta.score }}</span>
                  <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">×</button>
                </div>
              </div>
              <div v-for="i in Math.max(0, 4 - escalacao.filter(a => a.posicao_id === 4).length)" :key="'e-mei-'+i" class="jogador-slot empty">
                <span class="pos">MEI</span>
              </div>
            </div>
            
            <!-- Zagueiros -->
            <div class="linha zagueiros">
              <div 
                v-for="(atleta, i) in escalacao.filter(a => a.posicao_id === 3)" 
                :key="i"
                class="jogador-slot"
              >
                <div class="jogador-card filled zag">
                  <span class="pos">ZAG</span>
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="pts">{{ atleta.score }}</span>
                  <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">×</button>
                </div>
              </div>
              <div v-for="i in Math.max(0, 2 - escalacao.filter(a => a.posicao_id === 3).length)" :key="'e-zag-'+i" class="jogador-slot empty">
                <span class="pos">ZAG</span>
              </div>
            </div>
            
            <!-- Laterais -->
            <div class="linha laterais">
              <div 
                v-for="(atleta, i) in escalacao.filter(a => a.posicao_id === 2)" 
                :key="i"
                class="jogador-slot"
              >
                <div class="jogador-card filled lat">
                  <span class="pos">LAT</span>
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="pts">{{ atleta.score }}</span>
                  <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">×</button>
                </div>
              </div>
              <div v-for="i in Math.max(0, 2 - escalacao.filter(a => a.posicao_id === 2).length)" :key="'e-lat-'+i" class="jogador-slot empty">
                <span class="pos">LAT</span>
              </div>
            </div>
            
            <!-- Goleiro -->
            <div class="linha goleiro">
              <div 
                v-for="(atleta, i) in escalacao.filter(a => a.posicao_id === 1)" 
                :key="i"
                class="jogador-slot"
              >
                <div class="jogador-card filled gol">
                  <span class="pos">GOL</span>
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="pts">{{ atleta.score }}</span>
                  <button @click="removerAtleta(escalacao.indexOf(atleta))" class="remove-btn">×</button>
                </div>
              </div>
              <div v-if="escalacao.filter(a => a.posicao_id === 1).length === 0" class="jogador-slot empty">
                <span class="pos">GOL</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Reservas -->
        <div v-if="reservas.length > 0" class="reservas-section">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
            </svg>
            Banco de Reservas
          </h3>
          <div class="reservas-grid">
            <div v-for="atleta in reservas" :key="atleta.atleta_id" class="reserva-card">
              <span class="pos" :style="{ background: POSICOES[atleta.posicao_id]?.cor }">
                {{ POSICOES[atleta.posicao_id]?.abrev }}
              </span>
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
              <span class="rodada">Rodada {{ statusMercado.rodada_atual }}</span>
              <span class="local">{{ partida.local }}</span>
            </div>
            <div class="confronto-times">
              <div class="time casa">
                <img :src="clubes[partida.clube_casa_id]?.escudos?.['60x60']" 
                     @error="$event.target.src = '/icone.webp'"
                     :alt="clubes[partida.clube_casa_id]?.nome">
                <span>{{ clubes[partida.clube_casa_id]?.nome || 'Casa' }}</span>
              </div>
              <div class="versus">
                <span class="vs">VS</span>
                <div class="analise" :class="analisarConfronto(partida).favorito">
                  {{ analisarConfronto(partida).probabilidade }}%
                </div>
              </div>
              <div class="time fora">
                <img :src="clubes[partida.clube_visitante_id]?.escudos?.['60x60']" 
                     @error="$event.target.src = '/icone.webp'"
                     :alt="clubes[partida.clube_visitante_id]?.nome">
                <span>{{ clubes[partida.clube_visitante_id]?.nome || 'Fora' }}</span>
              </div>
            </div>
            <div class="confronto-footer">
              <span class="data">{{ partida.partida_data }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cartola-module {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 100%);
  color: #fff;
  padding: 20px;
}

/* Header */
.module-header {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid rgba(155, 89, 182, 0.3);
  color: rgba(255, 255, 255, 0.7);
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  border-color: #9b59b6;
  color: #fff;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.header-info h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(90deg, #9b59b6, #bb86fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-icon {
  width: 32px;
  height: 32px;
  stroke: #9b59b6;
}

.header-info p {
  color: rgba(255, 255, 255, 0.5);
  margin-top: 5px;
}

.header-stats {
  display: flex;
  gap: 15px;
  margin-left: auto;
}

.stat-pill {
  background: rgba(155, 89, 182, 0.1);
  border: 1px solid rgba(155, 89, 182, 0.3);
  padding: 8px 16px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-pill.aberto {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.stat-pill .label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.stat-pill .value {
  font-weight: 700;
  color: #bb86fc;
}

.stat-pill.aberto .value {
  color: #22c55e;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  gap: 20px;
}

.loader {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(155, 89, 182, 0.2);
  border-top-color: #9b59b6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Tabs */
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
  border-bottom: 1px solid rgba(155, 89, 182, 0.2);
  padding-bottom: 15px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid rgba(155, 89, 182, 0.2);
  color: rgba(255, 255, 255, 0.6);
  padding: 12px 24px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
  text-transform: capitalize;
}

.tab-btn svg {
  width: 18px;
  height: 18px;
}

.tab-btn:hover {
  border-color: #9b59b6;
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  border-color: transparent;
  color: #fff;
}

/* Mercado */
.mercado-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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
  gap: 5px;
}

.filtro-group label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.filtro-group select,
.filtro-group input {
  background: rgba(26, 26, 26, 0.8);
  border: 1px solid rgba(155, 89, 182, 0.3);
  color: #fff;
  padding: 10px 15px;
  border-radius: 8px;
  min-width: 150px;
}

.filtro-group.search input {
  min-width: 250px;
}

.mercado-stats {
  color: rgba(255, 255, 255, 0.5);
}

/* Atletas Grid */
.atletas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.atleta-card {
  background: rgba(26, 26, 26, 0.8);
  border: 1px solid rgba(155, 89, 182, 0.2);
  border-radius: 15px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.atleta-card:hover {
  border-color: #9b59b6;
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(155, 89, 182, 0.2);
}

.atleta-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.pos-badge {
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
}

.atleta-foto {
  text-align: center;
  margin-bottom: 10px;
}

.atleta-foto img {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(155, 89, 182, 0.3);
}

.atleta-info {
  text-align: center;
  margin-bottom: 10px;
}

.atleta-info h4 {
  font-size: 0.95rem;
  margin-bottom: 3px;
}

.atleta-info p {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.atleta-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.atleta-stats .stat {
  text-align: center;
}

.atleta-stats .label {
  display: block;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 2px;
}

.atleta-stats .value {
  font-weight: 700;
}

.atleta-stats .value.price {
  color: #22c55e;
}

.atleta-stats .value.score {
  color: #bb86fc;
}

.add-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(155, 89, 182, 0.2);
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s;
}

.atleta-card:hover .add-btn {
  opacity: 1;
}

.add-btn svg {
  width: 14px;
  height: 14px;
  stroke: #fff;
}

.add-btn:hover {
  background: #9b59b6;
}

/* Escalação */
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
  gap: 20px;
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
  background: rgba(26, 26, 26, 0.8);
  border: 1px solid rgba(155, 89, 182, 0.3);
  color: #fff;
  padding: 8px 12px;
  border-radius: 8px;
  width: 100px;
  font-weight: 700;
}

.orcamento-item .value {
  font-size: 1.2rem;
  font-weight: 700;
}

.orcamento-item .gasto {
  color: #ef4444;
}

.orcamento-item .saldo {
  color: #22c55e;
}

.orcamento-item .saldo.negativo {
  color: #ef4444;
}

.orcamento-item .pontos {
  color: #bb86fc;
}

.escalacao-actions {
  display: flex;
  gap: 10px;
}

.btn-escalar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  border: none;
  color: #fff;
  padding: 12px 25px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-escalar:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(155, 89, 182, 0.4);
}

.btn-escalar:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-escalar svg {
  width: 18px;
  height: 18px;
}

.mini-loader {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.btn-limpar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  padding: 12px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-limpar:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
}

.btn-limpar svg {
  width: 16px;
  height: 16px;
}

/* Campo */
.campo-container {
  background: linear-gradient(180deg, #1a472a 0%, #2d5a3f 50%, #1a472a 100%);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 25px;
  position: relative;
  overflow: hidden;
}

.campo-container::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 150px;
  height: 150px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.campo-container::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.1);
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.linha {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.jogador-slot {
  width: 90px;
}

.jogador-card {
  background: rgba(0, 0, 0, 0.6);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 10px;
  text-align: center;
  position: relative;
}

.jogador-card.filled {
  border-color: #9b59b6;
}

.jogador-card.filled.gol { border-color: #f59e0b; }
.jogador-card.filled.lat { border-color: #3b82f6; }
.jogador-card.filled.zag { border-color: #10b981; }
.jogador-card.filled.mei { border-color: #8b5cf6; }
.jogador-card.filled.ata { border-color: #ef4444; }

.jogador-card .pos {
  display: block;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 3px;
}

.jogador-card .nome {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.jogador-card .pts {
  display: block;
  font-size: 0.7rem;
  color: #bb86fc;
  margin-top: 3px;
}

.jogador-slot.empty .jogador-card,
.jogador-slot.empty {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  background: transparent;
  border-radius: 10px;
  padding: 15px 10px;
  text-align: center;
}

.jogador-slot.empty .pos {
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.75rem;
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  background: #ef4444;
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.jogador-card:hover .remove-btn {
  opacity: 1;
}

/* Reservas */
.reservas-section {
  background: rgba(26, 26, 26, 0.5);
  border: 1px solid rgba(155, 89, 182, 0.2);
  border-radius: 15px;
  padding: 20px;
}

.reservas-section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1rem;
  margin-bottom: 15px;
  color: #bb86fc;
}

.reservas-section h3 svg {
  width: 20px;
  height: 20px;
}

.reservas-grid {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.reserva-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(155, 89, 182, 0.1);
  border: 1px solid rgba(155, 89, 182, 0.2);
  padding: 10px 15px;
  border-radius: 10px;
}

.reserva-card .pos {
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 0.7rem;
  font-weight: 700;
}

.reserva-card .nome {
  font-weight: 600;
}

.reserva-card .score {
  color: #bb86fc;
  font-weight: 700;
}

/* Confrontos */
.confrontos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.confronto-card {
  background: rgba(26, 26, 26, 0.8);
  border: 1px solid rgba(155, 89, 182, 0.2);
  border-radius: 15px;
  overflow: hidden;
}

.confronto-header {
  display: flex;
  justify-content: space-between;
  padding: 12px 15px;
  background: rgba(155, 89, 182, 0.1);
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.confronto-times {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
}

.confronto-times .time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.confronto-times .time img {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.confronto-times .time span {
  font-size: 0.85rem;
  font-weight: 600;
  text-align: center;
}

.versus {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 0 15px;
}

.versus .vs {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 700;
}

.analise {
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 700;
}

.analise.casa {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.analise.fora {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.confronto-footer {
  padding: 12px 15px;
  text-align: center;
  border-top: 1px solid rgba(155, 89, 182, 0.1);
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Responsive */
@media (max-width: 768px) {
  .module-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-stats {
    margin-left: 0;
    width: 100%;
    justify-content: space-between;
  }
  
  .tabs {
    flex-wrap: wrap;
  }
  
  .tab-btn {
    flex: 1;
    justify-content: center;
  }
  
  .atletas-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
  
  .jogador-slot {
    width: 70px;
  }
  
  .jogador-card .nome {
    font-size: 0.65rem;
  }
}
</style>
