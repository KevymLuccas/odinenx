<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans, getTrialStatus } from '../../lib/stripe'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const loading = ref(true)
const activeTab = ref('escalacao')
const atletas = ref([])
const clubes = ref({})
const partidas = ref([])
const escalacao = ref([])
const reservas = ref([])
const capitao = ref(null)
const cartoletas = ref(100)
const filtroPos = ref('todas')
const filtroBusca = ref('')
const statusMercado = ref({})
const analisando = ref(false)
const mobileMenuOpen = ref(false)
const modalJogador = ref(null)
const modalPosicao = ref(null)
const jogadoresFixados = ref(new Set()) // Jogadores já escalados no Cartola real

// Funções para o modal de jogador
const abrirModalJogador = (atleta, origem = 'campo') => {
  modalJogador.value = { ...atleta, origem }
}

const fixarJogador = (atletaId) => {
  if (jogadoresFixados.value.has(atletaId)) {
    jogadoresFixados.value.delete(atletaId)
  } else {
    jogadoresFixados.value.add(atletaId)
  }
  // Força reatividade
  jogadoresFixados.value = new Set(jogadoresFixados.value)
}

const isFixado = (atletaId) => {
  return jogadoresFixados.value.has(atletaId)
}

// Posições
const POSICOES = {
  1: { nome: 'Goleiro', abrev: 'GOL', cor: '#f59e0b', icon: '🧤' },
  2: { nome: 'Lateral', abrev: 'LAT', cor: '#3b82f6', icon: '🏃' },
  3: { nome: 'Zagueiro', abrev: 'ZAG', cor: '#10b981', icon: '🛡️' },
  4: { nome: 'Meia', abrev: 'MEI', cor: '#8b5cf6', icon: '⚙️' },
  5: { nome: 'Atacante', abrev: 'ATA', cor: '#ef4444', icon: '⚽' },
  6: { nome: 'Técnico', abrev: 'TEC', cor: '#6b7280', icon: '📋' }
}

// Esquema tático fixo: 1 GOL, 2 LAT, 2 ZAG, 4 MEI, 2 ATA, 1 TEC
const ESQUEMA = { 1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1 }

// Status dos atletas
const STATUS = {
  2: { nome: 'Dúvida', emoji: '⚠️', cor: '#ffaa00' },
  3: { nome: 'Suspenso', emoji: '🟡', cor: '#ffff00' },
  5: { nome: 'Contundido', emoji: '🏥', cor: '#ff6666' },
  6: { nome: 'Nulo', emoji: '❓', cor: '#888888' },
  7: { nome: 'Provável', emoji: '✅', cor: '#00ff88' }
}

// Força dos times
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

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

// Computed - Atletas por posição para o mercado
const atletasFiltrados = computed(() => {
  let lista = atletas.value
  
  if (filtroPos.value !== 'todas') {
    lista = lista.filter(a => a.posicao_id == filtroPos.value)
  }
  
  if (filtroBusca.value) {
    const busca = filtroBusca.value.toLowerCase()
    lista = lista.filter(a => 
      a.apelido?.toLowerCase().includes(busca) ||
      clubes.value[a.clube_id]?.nome_fantasia?.toLowerCase().includes(busca)
    )
  }
  
  return lista.sort((a, b) => (b.score || 0) - (a.score || 0))
})

// Escalação organizada por posição
const escalacaoPorPosicao = computed(() => {
  const org = {}
  for (const posId in POSICOES) {
    org[posId] = escalacao.value.filter(a => a.posicao_id == posId)
  }
  return org
})

// Slots vazios
const slotsVazios = computed(() => {
  const slots = {}
  for (const [posId, qtd] of Object.entries(ESQUEMA)) {
    const atual = escalacao.value.filter(a => a.posicao_id == posId).length
    slots[posId] = qtd - atual
  }
  return slots
})

const gastoTotal = computed(() => {
  return escalacao.value.reduce((sum, a) => sum + (a.preco_num || 0), 0)
})

const saldoRestante = computed(() => {
  return cartoletas.value - gastoTotal.value
})

const pontuacaoEstimada = computed(() => {
  let total = escalacao.value.reduce((sum, a) => sum + (a.score || 0), 0)
  // Capitão dobra pontos
  if (capitao.value) {
    const cap = escalacao.value.find(a => a.atleta_id === capitao.value)
    if (cap) total += cap.score || 0
  }
  return total
})

const timeCompleto = computed(() => {
  return escalacao.value.length === 12
})

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    router.push('/login')
    return
  }
  
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  // Verificar se trial expirou para usuários free
  if (!subscription.value?.plan || subscription.value.plan === 'free') {
    const trialStatus = await getTrialStatus(session.user.id)
    if (trialStatus?.expired) {
      router.push('/trial-expired')
      return
    }
  }
  
  await carregarDados()
})

// Carregar dados da API
const carregarDados = async () => {
  loading.value = true
  
  try {
    const resMercado = await fetch('/api/cartola/mercado')
    const dataMercado = await resMercado.json()
    
    atletas.value = dataMercado.atletas?.map(a => ({
      ...a,
      score: calcularScore(a)
    })) || []
    clubes.value = dataMercado.clubes || {}
    
    const resStatus = await fetch('/api/cartola/status')
    statusMercado.value = await resStatus.json()
    
    const resPartidas = await fetch('/api/cartola/partidas')
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
  const status = atleta.status_id
  
  const custoBeneficio = (media / preco) * 2
  const momentum = variacao > 0 ? 1 + (variacao * 0.1) : 1 - (Math.abs(variacao) * 0.05)
  const exp = Math.min(jogos / 3, 1.5)
  
  let score = (media * 1.5 + custoBeneficio * 2) * momentum * (0.7 + exp * 0.3)
  
  // Penalização por status
  if (status === 3 || status === 5) score *= 0.2  // Suspenso ou Contundido
  else if (status === 6) score *= 0.3             // Nulo
  else if (status === 2) score *= 0.75            // Dúvida
  // status 7 (Provável) ou undefined: sem penalização
  
  return Math.round(score * 100) / 100
}

// Escalar automaticamente com IA
const escalarAutomatico = () => {
  analisando.value = true
  
  // PRESERVAR jogadores fixados
  const fixados = escalacao.value.filter(a => jogadoresFixados.value.has(a.atleta_id))
  const idsFixados = new Set(fixados.map(a => a.atleta_id))
  
  // Calcular quantos slots ainda precisa preencher por posição
  const slotsPreenchidosPorFixados = {}
  const gastoFixados = fixados.reduce((sum, a) => sum + (a.preco_num || 0), 0)
  
  for (const pos in POSICOES) {
    slotsPreenchidosPorFixados[pos] = fixados.filter(a => a.posicao_id == pos).length
  }
  
  reservas.value = []
  
  setTimeout(() => {
    // Aceitar atletas: Provável (7), Dúvida (2), ou sem status definido
    // Excluir apenas: Suspenso (3), Contundido (5), Nulo (6)
    const atletasValidos = atletas.value.filter(a => {
      const status = a.status_id
      if (status === 3 || status === 5 || status === 6) return false
      if (idsFixados.has(a.atleta_id)) return false // Já está fixado
      return true
    })
    
    // Organizar por posição
    const porPosicao = {}
    for (const pos in POSICOES) {
      porPosicao[pos] = atletasValidos
        .filter(a => a.posicao_id == pos)
        .sort((a, b) => (b.score || 0) - (a.score || 0))
    }
    
    // PASSO 1: Primeiro garantir o time mínimo com os mais baratos (respeitando fixados)
    const novaEscalacao = [...fixados] // Começa com os fixados
    const idsUsados = new Set(idsFixados)
    let gastoMinimo = gastoFixados
    
    // Pegar o mais barato de cada posição primeiro para garantir time completo
    for (const [posId, qtd] of Object.entries(ESQUEMA)) {
      const jaPreenchidos = slotsPreenchidosPorFixados[posId] || 0
      const faltam = qtd - jaPreenchidos
      
      if (faltam <= 0) continue // Posição já completa com fixados
      
      const disponiveis = (porPosicao[posId] || [])
        .filter(a => !idsUsados.has(a.atleta_id))
        .sort((a, b) => (a.preco_num || 0) - (b.preco_num || 0)) // Mais baratos
      
      for (let i = 0; i < faltam && i < disponiveis.length; i++) {
        const atleta = disponiveis[i]
        novaEscalacao.push(atleta)
        idsUsados.add(atleta.atleta_id)
        gastoMinimo += atleta.preco_num || 0
      }
    }
    
    // PASSO 2: Se sobrou cartoletas, fazer upgrades (NÃO mexer nos fixados!)
    let orcamentoRestante = cartoletas.value - gastoMinimo
    
    if (orcamentoRestante > 0) {
      // Para cada posição, tentar trocar por jogadores melhores (exceto fixados)
      for (const [posId, qtd] of Object.entries(ESQUEMA)) {
        const escaladosPosicao = novaEscalacao
          .filter(a => a.posicao_id == posId && !jogadoresFixados.value.has(a.atleta_id)) // NÃO MEXER EM FIXADOS
        const melhoresDisponiveis = (porPosicao[posId] || [])
          .filter(a => !idsUsados.has(a.atleta_id))
          .sort((a, b) => (b.score || 0) - (a.score || 0)) // Melhores primeiro
        
        for (const melhor of melhoresDisponiveis) {
          // Encontrar o pior escalado dessa posição (que NÃO seja fixado)
          const pior = escaladosPosicao
            .sort((a, b) => (a.score || 0) - (b.score || 0))[0]
          
          if (!pior) break
          
          const custoDiferenca = (melhor.preco_num || 0) - (pior.preco_num || 0)
          
          // Se o melhor tem score maior e cabe no orçamento
          if ((melhor.score || 0) > (pior.score || 0) && custoDiferenca <= orcamentoRestante) {
            // Trocar
            const idx = novaEscalacao.findIndex(a => a.atleta_id === pior.atleta_id)
            if (idx > -1) {
              novaEscalacao[idx] = melhor
              idsUsados.delete(pior.atleta_id)
              idsUsados.add(melhor.atleta_id)
              orcamentoRestante -= custoDiferenca
              
              // Atualizar lista de escalados da posição
              const idxPos = escaladosPosicao.findIndex(a => a.atleta_id === pior.atleta_id)
              if (idxPos > -1) escaladosPosicao[idxPos] = melhor
            }
          }
        }
      }
    }
    
    escalacao.value = novaEscalacao
    
    // Selecionar capitão (maior score)
    if (novaEscalacao.length > 0) {
      const melhor = novaEscalacao.reduce((a, b) => (a.score > b.score ? a : b))
      capitao.value = melhor.atleta_id
    }
    
    // Reservas (5 posições: GOL, LAT, ZAG, MEI, ATA - sem TEC)
    const reservasTemp = []
    for (const posId of [1, 2, 3, 4, 5]) {
      const disponiveis = (porPosicao[posId] || [])
        .filter(a => !idsUsados.has(a.atleta_id))
        .sort((a, b) => (b.score || 0) - (a.score || 0))
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
    alert(`Limite de ${maxPos} ${POSICOES[posId]?.nome}(s) atingido!`)
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
  modalJogador.value = null
}

// Remover atleta da escalação
const removerAtleta = (atletaId) => {
  const index = escalacao.value.findIndex(a => a.atleta_id === atletaId)
  if (index > -1) {
    escalacao.value.splice(index, 1)
    if (capitao.value === atletaId) {
      capitao.value = null
    }
  }
}

// Definir capitão
const definirCapitao = (atletaId) => {
  capitao.value = atletaId
}

// Trocar jogador
const abrirModalTroca = (posicao) => {
  modalPosicao.value = posicao
  filtroPos.value = posicao.toString()
}

const fecharModal = () => {
  modalPosicao.value = null
  modalJogador.value = null
}

// Promover reserva
const promoverReserva = (atleta) => {
  // Verificar se pode adicionar
  const posId = atleta.posicao_id
  const qtdPos = escalacao.value.filter(a => a.posicao_id === posId).length
  const maxPos = ESQUEMA[posId] || 0
  
  if (qtdPos >= maxPos) {
    alert(`Remova um ${POSICOES[posId]?.nome} antes!`)
    return
  }
  
  if (gastoTotal.value + atleta.preco_num > cartoletas.value) {
    alert('Cartoletas insuficientes!')
    return
  }
  
  // Adicionar à escalação
  escalacao.value.push(atleta)
  
  // Remover das reservas
  const idx = reservas.value.findIndex(r => r.atleta_id === atleta.atleta_id)
  if (idx > -1) reservas.value.splice(idx, 1)
}

// Limpar escalação
const limparEscalacao = () => {
  escalacao.value = []
  reservas.value = []
  capitao.value = null
}

// Trocar titular por reserva
const trocarPorReserva = (titular, reserva) => {
  // Remover titular da escalação
  const idxTitular = escalacao.value.findIndex(a => a.atleta_id === titular.atleta_id)
  if (idxTitular > -1) {
    escalacao.value.splice(idxTitular, 1)
  }
  
  // Remover reserva da lista
  const idxReserva = reservas.value.findIndex(a => a.atleta_id === reserva.atleta_id)
  if (idxReserva > -1) {
    reservas.value.splice(idxReserva, 1)
  }
  
  // Adicionar reserva à escalação
  escalacao.value.push(reserva)
  
  // Adicionar titular às reservas
  reservas.value.push(titular)
  
  // Se o titular era capitão, transferir para o novo
  if (capitao.value === titular.atleta_id) {
    capitao.value = reserva.atleta_id
  }
}

// Encontrar reserva da mesma posição
const encontrarReserva = (posicaoId) => {
  return reservas.value.find(r => r.posicao_id == posicaoId)
}

// Computed reservas por posição (cacheado para evitar re-render loops)
const reservaGol = computed(() => reservas.value.find(r => r.posicao_id == 1))
const reservaLat = computed(() => reservas.value.find(r => r.posicao_id == 2))
const reservaZag = computed(() => reservas.value.find(r => r.posicao_id == 3))
const reservaMei = computed(() => reservas.value.find(r => r.posicao_id == 4))
const reservaAta = computed(() => reservas.value.find(r => r.posicao_id == 5))

// Gastos das reservas
const gastoReservas = computed(() => {
  return reservas.value.reduce((sum, a) => sum + (a.preco_num || 0), 0)
})

// Media das reservas
const mediaReservas = computed(() => {
  if (reservas.value.length === 0) return 0
  const total = reservas.value.reduce((sum, a) => sum + (a.media_num || 0), 0)
  return total / reservas.value.length
})

// Obter foto do atleta
const getFoto = (atleta) => {
  if (atleta.foto) {
    return atleta.foto.replace('FORMATO', '100x100')
  }
  return '/icone.webp'
}

// Analisar confronto
const analisarConfronto = (partida) => {
  const casaId = partida.clube_casa_id
  const foraId = partida.clube_visitante_id
  
  const forcaCasa = FORCA_TIMES[casaId] || { ataque: 70, defesa: 70 }
  const forcaFora = FORCA_TIMES[foraId] || { ataque: 70, defesa: 70 }
  
  const potGolsCasa = ((forcaCasa.ataque - forcaFora.defesa + 100) / 200 * 10).toFixed(1)
  const potGolsFora = ((forcaFora.ataque - forcaCasa.defesa + 100) / 200 * 10).toFixed(1)
  
  return { potGolsCasa, potGolsFora }
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}

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
    <!-- Sidebar Desktop -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/">
          <img src="/logo.webp" alt="ODINENX" class="sidebar-logo" />
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-category">Principal</div>
        <router-link to="/dashboard" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          Dashboard
        </router-link>

        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
          </svg>
          BET
        </router-link>
        <router-link to="/trade" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>
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
            <path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>
          </svg>
          Histórico
        </router-link>

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
        <div class="plan-badge-sidebar">{{ currentPlan.name }}</div>
        <button @click="logout" class="logout-btn">
          <svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
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
        <button @click="navigateTo('/dashboard')" class="mobile-nav-item">Dashboard</button>
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</button>
        <button @click="navigateTo('/cartola')" class="mobile-nav-item active">Cartola FC</button>
        <button @click="navigateTo('/alerts')" class="mobile-nav-item">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item">Configurações</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

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
            Cartola FC Pro
          </h1>
          <p>Sistema Inteligente de Escalação</p>
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
        <p>Carregando dados do Cartola...</p>
      </div>

      <!-- Content -->
      <div v-else class="dashboard-content">
        <!-- Tabs -->
        <div class="cartola-tabs">
          <button @click="activeTab = 'escalacao'" :class="{ active: activeTab === 'escalacao' }" class="tab-btn">
            <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Escalação
          </button>
          <button @click="activeTab = 'mercado'" :class="{ active: activeTab === 'mercado' }" class="tab-btn">
            <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
            </svg>
            Mercado
          </button>
          <button @click="activeTab = 'confrontos'" :class="{ active: activeTab === 'confrontos' }" class="tab-btn">
            <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            Confrontos
          </button>
        </div>

        <!-- Tab: Escalação -->
        <div v-if="activeTab === 'escalacao'" class="tab-content">
          <!-- Orçamento Header -->
          <div class="orcamento-bar">
            <div class="orcamento-item">
              <span class="label">Cartoletas</span>
              <input type="number" v-model.number="cartoletas" min="0" max="999" step="5" class="cartoletas-input">
            </div>
            <div class="orcamento-item">
              <span class="label">Gasto</span>
              <span class="value red">C$ {{ gastoTotal.toFixed(2) }}</span>
            </div>
            <div class="orcamento-item">
              <span class="label">Saldo</span>
              <span class="value" :class="saldoRestante >= 0 ? 'green' : 'red'">C$ {{ saldoRestante.toFixed(2) }}</span>
            </div>
            <div class="orcamento-item">
              <span class="label">Pontuação Est.</span>
              <span class="value blue">{{ pontuacaoEstimada.toFixed(1) }} pts</span>
            </div>
            <div class="orcamento-actions">
              <button @click="escalarAutomatico" class="btn-ia" :disabled="analisando">
                <svg v-if="!analisando" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                <div v-else class="mini-spinner"></div>
                {{ analisando ? 'Analisando...' : 'Escalar com IA' }}
              </button>
              <button @click="limparEscalacao" class="btn-limpar">Limpar</button>
            </div>
          </div>

          <!-- Campo de Futebol Visual -->
          <div class="campo-container">
            <div class="campo">
              <!-- Técnico -->
              <div class="campo-row tecnico-row">
                <div class="campo-titulo">Técnico</div>
                <div class="slots-row">
                  <template v-for="i in ESQUEMA[6]" :key="'tec-'+i">
                    <div v-if="escalacaoPorPosicao[6]?.[i-1]" class="jogador-slot filled" :class="{ fixado: isFixado(escalacaoPorPosicao[6][i-1].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[6][i-1], 'campo')">
                      <div v-if="isFixado(escalacaoPorPosicao[6][i-1].atleta_id)" class="fixado-badge">📌</div>
                      <img :src="getFoto(escalacaoPorPosicao[6][i-1])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                      <span class="jogador-nome">{{ escalacaoPorPosicao[6][i-1].apelido }}</span>
                      <span class="jogador-time">{{ clubes[escalacaoPorPosicao[6][i-1].clube_id]?.nome_fantasia || 'Time' }}</span>
                      <span class="jogador-score">{{ escalacaoPorPosicao[6][i-1].score }}</span>
                      <button v-if="capitao !== escalacaoPorPosicao[6][i-1].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[6][i-1].atleta_id)" class="btn-capitao">C</button>
                      <span v-else class="capitao-badge">C</span>
                    </div>
                    <div v-else class="jogador-slot empty" @click="abrirModalTroca(6)">
                      <span class="slot-icon">📋</span>
                      <span class="slot-text">TEC</span>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Atacantes -->
              <div class="campo-row atacantes-row">
                <div class="campo-titulo">Atacantes</div>
                <div class="slots-row">
                  <template v-for="i in ESQUEMA[5]" :key="'ata-'+i">
                    <div v-if="escalacaoPorPosicao[5]?.[i-1]" class="jogador-slot filled" :class="{ fixado: isFixado(escalacaoPorPosicao[5][i-1].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[5][i-1], 'campo')">
                      <div v-if="isFixado(escalacaoPorPosicao[5][i-1].atleta_id)" class="fixado-badge">📌</div>
                      <img :src="getFoto(escalacaoPorPosicao[5][i-1])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                      <span class="jogador-nome">{{ escalacaoPorPosicao[5][i-1].apelido }}</span>
                      <span class="jogador-time">{{ clubes[escalacaoPorPosicao[5][i-1].clube_id]?.nome_fantasia || 'Time' }}</span>
                      <span class="jogador-score">{{ escalacaoPorPosicao[5][i-1].score }}</span>
                      <button v-if="capitao !== escalacaoPorPosicao[5][i-1].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[5][i-1].atleta_id)" class="btn-capitao">C</button>
                      <span v-else class="capitao-badge">C</span>
                    </div>
                    <div v-else class="jogador-slot empty" @click="abrirModalTroca(5)">
                      <span class="slot-icon">⚽</span>
                      <span class="slot-text">ATA</span>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Meias -->
              <div class="campo-row meias-row">
                <div class="campo-titulo">Meias</div>
                <div class="slots-row">
                  <template v-for="i in ESQUEMA[4]" :key="'mei-'+i">
                    <div v-if="escalacaoPorPosicao[4]?.[i-1]" class="jogador-slot filled" :class="{ fixado: isFixado(escalacaoPorPosicao[4][i-1].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[4][i-1], 'campo')">
                      <div v-if="isFixado(escalacaoPorPosicao[4][i-1].atleta_id)" class="fixado-badge">📌</div>
                      <img :src="getFoto(escalacaoPorPosicao[4][i-1])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                      <span class="jogador-nome">{{ escalacaoPorPosicao[4][i-1].apelido }}</span>
                      <span class="jogador-time">{{ clubes[escalacaoPorPosicao[4][i-1].clube_id]?.nome_fantasia || 'Time' }}</span>
                      <span class="jogador-score">{{ escalacaoPorPosicao[4][i-1].score }}</span>
                      <button v-if="capitao !== escalacaoPorPosicao[4][i-1].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[4][i-1].atleta_id)" class="btn-capitao">C</button>
                      <span v-else class="capitao-badge">C</span>
                    </div>
                    <div v-else class="jogador-slot empty" @click="abrirModalTroca(4)">
                      <span class="slot-icon">⚙️</span>
                      <span class="slot-text">MEI</span>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Defesa (Laterais + Zagueiros) -->
              <div class="campo-row defesa-row">
                <div class="campo-titulo">Defesa</div>
                <div class="slots-row">
                  <!-- Lateral Esquerdo -->
                  <div v-if="escalacaoPorPosicao[2]?.[0]" class="jogador-slot filled" :class="{ fixado: isFixado(escalacaoPorPosicao[2][0].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[2][0], 'campo')">
                    <div v-if="isFixado(escalacaoPorPosicao[2][0].atleta_id)" class="fixado-badge">📌</div>
                    <img :src="getFoto(escalacaoPorPosicao[2][0])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                    <span class="jogador-nome">{{ escalacaoPorPosicao[2][0].apelido }}</span>
                    <span class="jogador-time">{{ clubes[escalacaoPorPosicao[2][0].clube_id]?.nome_fantasia || 'Time' }}</span>
                    <span class="jogador-score">{{ escalacaoPorPosicao[2][0].score }}</span>
                    <button v-if="capitao !== escalacaoPorPosicao[2][0].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[2][0].atleta_id)" class="btn-capitao">C</button>
                    <span v-else class="capitao-badge">C</span>
                  </div>
                  <div v-else class="jogador-slot empty" @click="abrirModalTroca(2)">
                    <span class="slot-icon">🏃</span>
                    <span class="slot-text">LAT</span>
                  </div>

                  <!-- Zagueiros -->
                  <template v-for="i in ESQUEMA[3]" :key="'zag-'+i">
                    <div v-if="escalacaoPorPosicao[3]?.[i-1]" class="jogador-slot filled" :class="{ fixado: isFixado(escalacaoPorPosicao[3][i-1].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[3][i-1], 'campo')">
                      <div v-if="isFixado(escalacaoPorPosicao[3][i-1].atleta_id)" class="fixado-badge">📌</div>
                      <img :src="getFoto(escalacaoPorPosicao[3][i-1])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                      <span class="jogador-nome">{{ escalacaoPorPosicao[3][i-1].apelido }}</span>
                      <span class="jogador-time">{{ clubes[escalacaoPorPosicao[3][i-1].clube_id]?.nome_fantasia || 'Time' }}</span>
                      <span class="jogador-score">{{ escalacaoPorPosicao[3][i-1].score }}</span>
                      <button v-if="capitao !== escalacaoPorPosicao[3][i-1].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[3][i-1].atleta_id)" class="btn-capitao">C</button>
                      <span v-else class="capitao-badge">C</span>
                    </div>
                    <div v-else class="jogador-slot empty" @click="abrirModalTroca(3)">
                      <span class="slot-icon">🛡️</span>
                      <span class="slot-text">ZAG</span>
                    </div>
                  </template>

                  <!-- Lateral Direito -->
                  <div v-if="escalacaoPorPosicao[2]?.[1]" class="jogador-slot filled" :class="{ fixado: isFixado(escalacaoPorPosicao[2][1].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[2][1], 'campo')">
                    <div v-if="isFixado(escalacaoPorPosicao[2][1].atleta_id)" class="fixado-badge">📌</div>
                    <img :src="getFoto(escalacaoPorPosicao[2][1])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                    <span class="jogador-nome">{{ escalacaoPorPosicao[2][1].apelido }}</span>
                    <span class="jogador-time">{{ clubes[escalacaoPorPosicao[2][1].clube_id]?.nome_fantasia || 'Time' }}</span>
                    <span class="jogador-score">{{ escalacaoPorPosicao[2][1].score }}</span>
                    <button v-if="capitao !== escalacaoPorPosicao[2][1].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[2][1].atleta_id)" class="btn-capitao">C</button>
                    <span v-else class="capitao-badge">C</span>
                  </div>
                  <div v-else class="jogador-slot empty" @click="abrirModalTroca(2)">
                    <span class="slot-icon">🏃</span>
                    <span class="slot-text">LAT</span>
                  </div>
                </div>
              </div>

              <!-- Goleiro -->
              <div class="campo-row goleiro-row">
                <div class="campo-titulo">Goleiro</div>
                <div class="slots-row">
                  <template v-for="i in ESQUEMA[1]" :key="'gol-'+i">
                    <div v-if="escalacaoPorPosicao[1]?.[i-1]" class="jogador-slot filled gol" :class="{ fixado: isFixado(escalacaoPorPosicao[1][i-1].atleta_id) }" @click="abrirModalJogador(escalacaoPorPosicao[1][i-1], 'campo')">
                      <div v-if="isFixado(escalacaoPorPosicao[1][i-1].atleta_id)" class="fixado-badge">📌</div>
                      <img :src="getFoto(escalacaoPorPosicao[1][i-1])" @error="$event.target.src = '/icone.webp'" class="jogador-foto">
                      <span class="jogador-nome">{{ escalacaoPorPosicao[1][i-1].apelido }}</span>
                      <span class="jogador-time">{{ clubes[escalacaoPorPosicao[1][i-1].clube_id]?.nome_fantasia || 'Time' }}</span>
                      <span class="jogador-score">{{ escalacaoPorPosicao[1][i-1].score }}</span>
                      <button v-if="capitao !== escalacaoPorPosicao[1][i-1].atleta_id" @click.stop="definirCapitao(escalacaoPorPosicao[1][i-1].atleta_id)" class="btn-capitao">C</button>
                      <span v-else class="capitao-badge">C</span>
                    </div>
                    <div v-else class="jogador-slot empty gol" @click="abrirModalTroca(1)">
                      <span class="slot-icon">🧤</span>
                      <span class="slot-text">GOL</span>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- Reservas de Luxo -->
          <div class="reservas-section">
            <div class="reservas-header">
              <h3>🏆 BANCO DE RESERVAS DE LUXO</h3>
              <div class="reservas-stats">
                <span class="stat">💎 {{ reservas.length }} jogadores</span>
                <span class="stat">💰 C$ {{ gastoReservas.toFixed(2) }}</span>
                <span class="stat">📊 Média: {{ mediaReservas.toFixed(1) }} pts</span>
              </div>
            </div>
            <p class="reservas-desc">Reservas mais baratas que titulares | Prontas para entrar!</p>
            
            <div class="reservas-grid-luxo">
              <!-- GOL Reserva -->
              <div class="reserva-card-luxo" :class="{ vazio: !reservaGol }" @click="reservaGol && abrirModalJogador(reservaGol, 'reserva')">
                <div class="reserva-pos" style="background: #f59e0b;">GOL</div>
                <template v-if="reservaGol">
                  <img :src="getFoto(reservaGol)" @error="$event.target.src = '/icone.webp'" class="reserva-foto-luxo">
                  <span class="reserva-nome-luxo">{{ reservaGol.apelido }}</span>
                  <span class="reserva-preco">C$ {{ reservaGol.preco_num?.toFixed(1) }}</span>
                  <span class="reserva-media">{{ reservaGol.media_num?.toFixed(1) }} pts</span>
                  <button class="btn-trocar" @click.stop="promoverReserva(reservaGol)">↑ Escalar</button>
                </template>
                <template v-else>
                  <span class="reserva-vazio">🧤</span>
                  <span class="reserva-texto">Sem reserva</span>
                </template>
              </div>

              <!-- LAT Reserva -->
              <div class="reserva-card-luxo" :class="{ vazio: !reservaLat }" @click="reservaLat && abrirModalJogador(reservaLat, 'reserva')">
                <div class="reserva-pos" style="background: #3b82f6;">LAT</div>
                <template v-if="reservaLat">
                  <img :src="getFoto(reservaLat)" @error="$event.target.src = '/icone.webp'" class="reserva-foto-luxo">
                  <span class="reserva-nome-luxo">{{ reservaLat.apelido }}</span>
                  <span class="reserva-preco">C$ {{ reservaLat.preco_num?.toFixed(1) }}</span>
                  <span class="reserva-media">{{ reservaLat.media_num?.toFixed(1) }} pts</span>
                  <button class="btn-trocar" @click.stop="promoverReserva(reservaLat)">↑ Escalar</button>
                </template>
                <template v-else>
                  <span class="reserva-vazio">🏃</span>
                  <span class="reserva-texto">Sem reserva</span>
                </template>
              </div>

              <!-- ZAG Reserva -->
              <div class="reserva-card-luxo" :class="{ vazio: !reservaZag }" @click="reservaZag && abrirModalJogador(reservaZag, 'reserva')">
                <div class="reserva-pos" style="background: #10b981;">ZAG</div>
                <template v-if="reservaZag">
                  <img :src="getFoto(reservaZag)" @error="$event.target.src = '/icone.webp'" class="reserva-foto-luxo">
                  <span class="reserva-nome-luxo">{{ reservaZag.apelido }}</span>
                  <span class="reserva-preco">C$ {{ reservaZag.preco_num?.toFixed(1) }}</span>
                  <span class="reserva-media">{{ reservaZag.media_num?.toFixed(1) }} pts</span>
                  <button class="btn-trocar" @click.stop="promoverReserva(reservaZag)">↑ Escalar</button>
                </template>
                <template v-else>
                  <span class="reserva-vazio">🛡️</span>
                  <span class="reserva-texto">Sem reserva</span>
                </template>
              </div>

              <!-- MEI Reserva -->
              <div class="reserva-card-luxo" :class="{ vazio: !reservaMei }" @click="reservaMei && abrirModalJogador(reservaMei, 'reserva')">
                <div class="reserva-pos" style="background: #8b5cf6;">MEI</div>
                <template v-if="reservaMei">
                  <img :src="getFoto(reservaMei)" @error="$event.target.src = '/icone.webp'" class="reserva-foto-luxo">
                  <span class="reserva-nome-luxo">{{ reservaMei.apelido }}</span>
                  <span class="reserva-preco">C$ {{ reservaMei.preco_num?.toFixed(1) }}</span>
                  <span class="reserva-media">{{ reservaMei.media_num?.toFixed(1) }} pts</span>
                  <button class="btn-trocar" @click.stop="promoverReserva(reservaMei)">↑ Escalar</button>
                </template>
                <template v-else>
                  <span class="reserva-vazio">⚙️</span>
                  <span class="reserva-texto">Sem reserva</span>
                </template>
              </div>

              <!-- ATA Reserva -->
              <div class="reserva-card-luxo" :class="{ vazio: !reservaAta }" @click="reservaAta && abrirModalJogador(reservaAta, 'reserva')">
                <div class="reserva-pos" style="background: #ef4444;">ATA</div>
                <template v-if="reservaAta">
                  <img :src="getFoto(reservaAta)" @error="$event.target.src = '/icone.webp'" class="reserva-foto-luxo">
                  <span class="reserva-nome-luxo">{{ reservaAta.apelido }}</span>
                  <span class="reserva-preco">C$ {{ reservaAta.preco_num?.toFixed(1) }}</span>
                  <span class="reserva-media">{{ reservaAta.media_num?.toFixed(1) }} pts</span>
                  <button class="btn-trocar" @click.stop="promoverReserva(reservaAta)">↑ Escalar</button>
                </template>
                <template v-else>
                  <span class="reserva-vazio">⚽</span>
                  <span class="reserva-texto">Sem reserva</span>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Mercado -->
        <div v-if="activeTab === 'mercado'" class="tab-content">
          <div class="mercado-header">
            <div class="filtros">
              <div class="filtro-group">
                <label>Posição</label>
                <select v-model="filtroPos">
                  <option value="todas">Todas</option>
                  <option v-for="(pos, id) in POSICOES" :key="id" :value="id">{{ pos.nome }}</option>
                </select>
              </div>
              <div class="filtro-group">
                <label>Buscar</label>
                <input type="text" v-model="filtroBusca" placeholder="Nome ou time...">
              </div>
            </div>
            <div class="mercado-info">
              <span>{{ atletasFiltrados.length }} atletas</span>
            </div>
          </div>

          <div class="atletas-grid">
            <div v-for="atleta in atletasFiltrados.slice(0, 60)" :key="atleta.atleta_id" class="atleta-card" @click="adicionarAtleta(atleta)">
              <div class="atleta-header">
                <div class="pos-badge" :style="{ background: POSICOES[atleta.posicao_id]?.cor }">
                  {{ POSICOES[atleta.posicao_id]?.abrev }}
                </div>
                <div class="status-badge" :style="{ color: STATUS[atleta.status_id]?.cor }">
                  {{ STATUS[atleta.status_id]?.emoji || '❓' }}
                </div>
              </div>
              <div class="atleta-foto">
                <img :src="getFoto(atleta)" @error="$event.target.src = '/icone.webp'" :alt="atleta.apelido">
              </div>
              <div class="atleta-info">
                <h4>{{ atleta.apelido }}</h4>
                <p>{{ clubes[atleta.clube_id]?.nome_fantasia || 'Time' }}</p>
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

        <!-- Tab: Confrontos -->
        <div v-if="activeTab === 'confrontos'" class="tab-content">
          <div class="confrontos-grid">
            <div v-for="partida in partidas" :key="partida.partida_id" class="confronto-card">
              <div class="confronto-header">
                <span>Rodada {{ statusMercado.rodada_atual }}</span>
              </div>
              <div class="confronto-times">
                <div class="time casa">
                  <img :src="clubes[partida.clube_casa_id]?.escudos?.['60x60']" @error="$event.target.src = '/icone.webp'">
                  <span class="nome">{{ clubes[partida.clube_casa_id]?.nome_fantasia || 'Casa' }}</span>
                  <span class="potencial">{{ analisarConfronto(partida).potGolsCasa }} gols</span>
                </div>
                <div class="versus">VS</div>
                <div class="time fora">
                  <img :src="clubes[partida.clube_visitante_id]?.escudos?.['60x60']" @error="$event.target.src = '/icone.webp'">
                  <span class="nome">{{ clubes[partida.clube_visitante_id]?.nome_fantasia || 'Fora' }}</span>
                  <span class="potencial">{{ analisarConfronto(partida).potGolsFora }} gols</span>
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

      <!-- Modal de Seleção de Jogador -->
      <div v-if="modalPosicao" class="modal-overlay" @click="fecharModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Escolher {{ POSICOES[modalPosicao]?.nome }}</h3>
            <button @click="fecharModal" class="modal-close">&times;</button>
          </div>
          <div class="modal-body">
            <input type="text" v-model="filtroBusca" placeholder="Buscar jogador..." class="modal-search">
            <div class="modal-lista">
              <div v-for="atleta in atletasFiltrados.slice(0, 30)" :key="atleta.atleta_id" class="modal-jogador" @click="adicionarAtleta(atleta)">
                <img :src="getFoto(atleta)" @error="$event.target.src = '/icone.webp'" class="modal-foto">
                <div class="modal-info">
                  <span class="nome">{{ atleta.apelido }}</span>
                  <span class="time">{{ clubes[atleta.clube_id]?.nome_fantasia }}</span>
                </div>
                <div class="modal-stats">
                  <span class="score">{{ atleta.score }}</span>
                  <span class="preco">C$ {{ (atleta.preco_num || 0).toFixed(1) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal de Detalhes do Jogador -->
      <div v-if="modalJogador" class="modal-overlay" @click="fecharModal">
        <div class="modal-jogador-detalhes" @click.stop>
          <button @click="fecharModal" class="modal-close-x">&times;</button>
          
          <!-- Header com foto e info básica -->
          <div class="jogador-header">
            <img :src="getFoto(modalJogador)" @error="$event.target.src = '/icone.webp'" class="jogador-foto-grande">
            <div class="jogador-info-principal">
              <h2>{{ modalJogador.apelido }}</h2>
              <div class="jogador-clube">{{ clubes[modalJogador.clube_id]?.nome_fantasia || 'Time' }}</div>
              <div class="jogador-posicao" :style="{ background: POSICOES[modalJogador.posicao_id]?.cor }">
                {{ POSICOES[modalJogador.posicao_id]?.icon }} {{ POSICOES[modalJogador.posicao_id]?.nome }}
              </div>
            </div>
          </div>

          <!-- Status do jogador -->
          <div v-if="modalJogador.status_id && STATUS[modalJogador.status_id]" class="jogador-status" :style="{ borderColor: STATUS[modalJogador.status_id]?.cor }">
            <span class="status-emoji">{{ STATUS[modalJogador.status_id]?.emoji }}</span>
            <span class="status-texto">{{ STATUS[modalJogador.status_id]?.nome }}</span>
          </div>

          <!-- Estatísticas -->
          <div class="jogador-stats-grid">
            <div class="stat-item">
              <span class="stat-label">Score IA</span>
              <span class="stat-value verde">{{ (modalJogador.score || 0).toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Preço</span>
              <span class="stat-value">C$ {{ (modalJogador.preco_num || 0).toFixed(1) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Média</span>
              <span class="stat-value">{{ (modalJogador.media_num || 0).toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Variação</span>
              <span class="stat-value" :class="{ verde: modalJogador.variacao_num > 0, vermelho: modalJogador.variacao_num < 0 }">
                {{ modalJogador.variacao_num > 0 ? '+' : '' }}{{ (modalJogador.variacao_num || 0).toFixed(1) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Jogos</span>
              <span class="stat-value">{{ modalJogador.jogos_num || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Última</span>
              <span class="stat-value">{{ (modalJogador.pontos_num || 0).toFixed(1) }}</span>
            </div>
          </div>

          <!-- Mínimo/Máximo -->
          <div class="jogador-minmax">
            <div class="minmax-item">
              <span class="minmax-label">📉 Mínimo</span>
              <span class="minmax-value vermelho">{{ (modalJogador.minimo_num || 0).toFixed(1) }}</span>
            </div>
            <div class="minmax-item">
              <span class="minmax-label">📈 Máximo</span>
              <span class="minmax-value verde">{{ (modalJogador.maximo_num || 0).toFixed(1) }}</span>
            </div>
          </div>

          <!-- Ações -->
          <div class="jogador-acoes">
            <!-- Se está no campo (escalado) -->
            <template v-if="modalJogador.origem === 'campo'">
              <button 
                @click="fixarJogador(modalJogador.atleta_id)" 
                class="btn-acao" 
                :class="{ ativo: isFixado(modalJogador.atleta_id) }"
              >
                📌 {{ isFixado(modalJogador.atleta_id) ? 'Desfixar' : 'Fixar Jogador' }}
              </button>
              <p class="dica-fixar" v-if="!isFixado(modalJogador.atleta_id)">
                💡 Fixe se você já escalou no Cartola. A IA não vai mexer nele!
              </p>
              <p class="dica-fixar fixado" v-else>
                ✅ Jogador fixado! Não será alterado ao gerar nova escalação.
              </p>
              <button @click="removerAtleta(modalJogador.atleta_id); fecharModal()" class="btn-acao vermelho">
                🗑️ Remover da Escalação
              </button>
            </template>

            <!-- Se está nas reservas -->
            <template v-else-if="modalJogador.origem === 'reserva'">
              <button @click="promoverReserva(modalJogador); fecharModal()" class="btn-acao verde">
                ↑ Escalar como Titular
              </button>
            </template>

            <!-- Se está no mercado -->
            <template v-else>
              <button @click="adicionarAtleta(modalJogador); fecharModal()" class="btn-acao verde">
                ➕ Adicionar à Escalação
              </button>
            </template>
          </div>

          <!-- Sugestão de substituição (só para quem está escalado) -->
          <div v-if="modalJogador.origem === 'campo' && encontrarReserva(modalJogador.posicao_id)" class="sugestao-troca">
            <h4>💡 Sugestão de Substituição</h4>
            <div class="troca-info">
              <span>{{ encontrarReserva(modalJogador.posicao_id)?.apelido }}</span>
              <span class="troca-score">Score: {{ encontrarReserva(modalJogador.posicao_id)?.score }}</span>
              <span class="troca-preco">C$ {{ (encontrarReserva(modalJogador.posicao_id)?.preco_num || 0).toFixed(1) }}</span>
            </div>
            <button @click="trocarPorReserva(modalJogador, encontrarReserva(modalJogador.posicao_id)); fecharModal()" class="btn-trocar">
              🔄 Trocar
            </button>
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
  overflow-y: auto;
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

/* ===== MOBILE MENU ===== */
.mobile-menu-btn {
  display: none;
  position: fixed;
  top: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  box-shadow: 0 5px 30px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  cursor: pointer;
  align-items: center;
  justify-content: center;
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
  z-index: 999;
  transform: translateY(100%);
  transition: transform 0.3s ease;
}

.mobile-menu.open {
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
  display: flex;
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
  transition: all 0.3s;
  text-align: left;
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
  flex-wrap: wrap;
  gap: 15px;
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  gap: 20px;
}

.loading-container p {
  color: rgba(255, 255, 255, 0.5);
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
  flex-wrap: wrap;
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

/* ===== ORÇAMENTO BAR ===== */
.orcamento-bar {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 20px 25px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  margin-bottom: 25px;
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

.orcamento-item .value {
  font-size: 1.3rem;
  font-weight: 700;
}

.orcamento-item .value.red { color: #ef4444; }
.orcamento-item .value.green { color: #22c55e; }
.orcamento-item .value.blue { color: #3b82f6; }

.cartoletas-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 10px 14px;
  border-radius: 10px;
  width: 110px;
  font-weight: 700;
  font-size: 1.1rem;
}

.orcamento-actions {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.btn-ia {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  color: #fff;
  padding: 14px 28px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-ia:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);
}

.btn-ia:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-ia svg {
  width: 18px;
  height: 18px;
}

.mini-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.btn-limpar {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 14px 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-limpar:hover {
  border-color: #ef4444;
  color: #ef4444;
}

/* ===== CAMPO DE FUTEBOL ===== */
.campo-container {
  margin-bottom: 30px;
}

.campo {
  background: linear-gradient(180deg, #1a472a 0%, #0f2d1a 100%);
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 30px;
  position: relative;
  overflow: hidden;
}

.campo::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.15);
}

.campo::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100px;
  height: 100px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
}

.campo-row {
  position: relative;
  z-index: 1;
  margin-bottom: 20px;
}

.campo-titulo {
  text-align: center;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 12px;
}

.slots-row {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.jogador-slot {
  width: 90px;
  height: 110px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.jogador-slot.empty {
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.2);
}

.jogador-slot.empty:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.4);
}

.jogador-slot.filled {
  background: rgba(0, 0, 0, 0.6);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.jogador-slot.filled:hover {
  transform: scale(1.05);
  border-color: #ef4444;
}

.slot-icon {
  font-size: 1.5rem;
  margin-bottom: 5px;
}

.slot-text {
  font-size: 0.7rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.5);
}

.jogador-foto {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.3);
  margin-bottom: 5px;
}

.jogador-nome {
  font-size: 0.65rem;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.jogador-time {
  font-size: 0.55rem;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  font-weight: 500;
  margin-top: -2px;
}

.jogador-score {
  font-size: 0.7rem;
  color: #22c55e;
  font-weight: 700;
}

.btn-capitao {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-capitao:hover {
  background: #f59e0b;
  border-color: #f59e0b;
}

.capitao-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f59e0b;
  color: #000;
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== RESERVAS DE LUXO ===== */
.reservas-section {
  margin-top: 30px;
  padding: 25px;
  background: linear-gradient(135deg, rgba(162, 155, 254, 0.1), rgba(26, 26, 26, 0.9));
  border: 2px solid #a29bfe;
  border-radius: 20px;
}

.reservas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 10px;
}

.reservas-section h3 {
  font-size: 1.2rem;
  color: #a29bfe;
  margin: 0;
}

.reservas-stats {
  display: flex;
  gap: 20px;
}

.reservas-stats .stat {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.reservas-desc {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 20px;
}

.reservas-grid-luxo {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.reserva-card-luxo {
  width: 130px;
  background: linear-gradient(180deg, #2d1f3d, #1a1a1a);
  border: 2px solid #a29bfe;
  border-radius: 15px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.reserva-card-luxo:hover {
  border-color: #bb86fc;
  transform: translateY(-5px);
}

.reserva-card-luxo.vazio {
  opacity: 0.5;
  border-style: dashed;
}

.reserva-pos {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
}

.reserva-foto-luxo {
  width: 55px;
  height: 55px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.reserva-nome-luxo {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.reserva-preco {
  font-size: 0.7rem;
  color: #a29bfe;
}

.reserva-media {
  font-size: 0.7rem;
  color: #00d9ff;
}

.reserva-vazio {
  font-size: 2rem;
  opacity: 0.5;
}

.reserva-texto {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.3);
}

.btn-trocar {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border: none;
  color: #fff;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 5px;
}

.btn-trocar:hover {
  background: linear-gradient(135deg, #16a34a, #15803d);
  transform: scale(1.05);
}

.pos-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #fff;
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
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
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

.atleta-foto {
  text-align: center;
  margin-bottom: 12px;
}

.atleta-foto img {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.atleta-info {
  text-align: center;
  margin-bottom: 15px;
}

.atleta-info h4 {
  font-size: 0.9rem;
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
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 3px;
}

.atleta-stats .value {
  font-weight: 700;
  font-size: 0.85rem;
}

.atleta-stats .value.price { color: #22c55e; }
.atleta-stats .value.score { color: #3b82f6; }

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
  gap: 8px;
  flex: 1;
}

.confronto-times .time img {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.confronto-times .time .nome {
  font-weight: 600;
  text-align: center;
  font-size: 0.9rem;
}

.confronto-times .time .potencial {
  font-size: 0.75rem;
  color: #22c55e;
}

.versus {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 700;
  padding: 0 15px;
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

/* ===== MODAL ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #0a0a0a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  font-size: 1.2rem;
}

.modal-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 2rem;
  cursor: pointer;
  line-height: 1;
}

.modal-close:hover {
  color: #fff;
}

.modal-body {
  padding: 20px 25px;
}

.modal-search {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 14px 18px;
  border-radius: 12px;
  margin-bottom: 15px;
  font-size: 1rem;
}

.modal-lista {
  max-height: 400px;
  overflow-y: auto;
}

.modal-jogador {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 15px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-jogador:hover {
  background: rgba(255, 255, 255, 0.08);
}

.modal-foto {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  object-fit: cover;
}

.modal-info {
  flex: 1;
}

.modal-info .nome {
  display: block;
  font-weight: 600;
}

.modal-info .time {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.modal-stats {
  text-align: right;
}

.modal-stats .score {
  display: block;
  font-weight: 700;
  color: #3b82f6;
}

.modal-stats .preco {
  font-size: 0.8rem;
  color: #22c55e;
}

/* ===== MODAL DETALHES JOGADOR ===== */
.modal-jogador-detalhes {
  background: linear-gradient(145deg, #0a0a0a 0%, #111 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  width: 100%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 25px;
  position: relative;
}

.modal-close-x {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  font-size: 1.5rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close-x:hover {
  background: rgba(255, 255, 255, 0.2);
}

.jogador-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.jogador-foto-grande {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(255, 255, 255, 0.2);
}

.jogador-info-principal h2 {
  font-size: 1.4rem;
  margin: 0 0 5px 0;
}

.jogador-clube {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.jogador-posicao {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.jogador-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border-left: 4px solid;
  margin-bottom: 20px;
}

.status-emoji {
  font-size: 1.3rem;
}

.status-texto {
  font-weight: 500;
}

.jogador-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 14px;
  border-radius: 12px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
}

.stat-value {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
}

.stat-value.verde { color: #22c55e; }
.stat-value.vermelho { color: #ef4444; }

.jogador-minmax {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.minmax-item {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  padding: 14px;
  border-radius: 12px;
  text-align: center;
}

.minmax-label {
  display: block;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
}

.minmax-value {
  font-size: 1.2rem;
  font-weight: 700;
}

.minmax-value.verde { color: #22c55e; }
.minmax-value.vermelho { color: #ef4444; }

.jogador-acoes {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.btn-acao {
  width: 100%;
  padding: 14px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-acao:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.btn-acao.ativo {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #3b82f6;
}

.btn-acao.verde {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-color: #22c55e;
}

.btn-acao.vermelho {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.btn-acao.vermelho:hover {
  background: rgba(239, 68, 68, 0.3);
}

.dica-fixar {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  margin: 0;
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.dica-fixar.fixado {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.sugestao-troca {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 16px;
  padding: 16px;
}

.sugestao-troca h4 {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
}

.troca-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
}

.troca-score {
  color: #3b82f6;
  font-weight: 600;
}

.troca-preco {
  color: #22c55e;
  font-weight: 600;
}

.btn-trocar {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-trocar:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

/* ===== INDICADOR DE FIXADO ===== */
.jogador-slot.fixado {
  border: 2px solid #3b82f6 !important;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}

.fixado-badge {
  position: absolute;
  top: -5px;
  left: -5px;
  font-size: 0.8rem;
  background: #3b82f6;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
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
  
  .nav-item span,
  .nav-category {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 15px;
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
  
  .mobile-menu-btn {
    display: flex;
  }
  
  .mobile-overlay {
    display: block;
  }
  
  .mobile-menu {
    display: block;
  }
  
  .main-content {
    margin-left: 0;
    padding: 20px;
    padding-bottom: 100px;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-left h1 {
    font-size: 1.4rem;
  }
  
  .orcamento-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .orcamento-actions {
    margin-left: 0;
    flex-direction: column;
  }
  
  .btn-ia, .btn-limpar {
    width: 100%;
    justify-content: center;
  }
  
  .jogador-slot {
    width: 70px;
    height: 90px;
  }
  
  .jogador-foto {
    width: 40px;
    height: 40px;
  }
  
  .jogador-nome {
    font-size: 0.55rem;
    max-width: 60px;
  }
  
  .slots-row {
    gap: 8px;
  }
  
  .atletas-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
  
  .confrontos-grid {
    grid-template-columns: 1fr;
  }
  
  .reservas-grid-luxo {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .reserva-card-luxo {
    padding: 15px 10px;
  }
  
  .reserva-nome-luxo {
    font-size: 0.75rem;
  }
  
  .tabs {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .tab-btn {
    padding: 10px 15px;
    font-size: 0.85rem;
    flex: 1;
    min-width: 80px;
    text-align: center;
  }
  
  .modal-detalhes {
    padding: 20px;
    max-height: 85vh;
  }
  
  .modal-header-jogador h2 {
    font-size: 1.3rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}

@media (max-width: 480px) {
  .jogador-slot {
    width: 60px;
    height: 80px;
  }
  
  .jogador-foto {
    width: 35px;
    height: 35px;
  }
  
  .jogador-nome {
    font-size: 0.5rem;
    max-width: 55px;
  }
  
  .jogador-time {
    font-size: 0.45rem;
  }
  
  .jogador-preco {
    font-size: 0.5rem;
    padding: 2px 5px;
  }
  
  .slots-row {
    gap: 5px;
  }
  
  .campo-container {
    min-height: 500px;
    padding: 10px;
  }
  
  .reservas-grid-luxo {
    grid-template-columns: 1fr;
  }
  
  .orcamento-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .atletas-grid {
    grid-template-columns: 1fr;
  }
  
  .mercado-filtros {
    flex-direction: column;
  }
  
  .filtro-posicao, .filtro-busca {
    width: 100%;
  }
  
  .header-left h1 {
    font-size: 1.2rem;
  }
  
  .header-left p {
    font-size: 0.8rem;
  }
}
</style>
