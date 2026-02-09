<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans, hasAccess, isAdmin as checkIsAdmin } from '../../lib/stripe'
import BottomNav from '../../components/BottomNav.vue'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const userIsAdmin = ref(false)
const mobileMenuOpen = ref(false)
const loading = ref(true)
const jogoSelecionado = ref(null)
const erro = ref(null)
const lastUpdate = ref(null)
const trialInfo = ref({ active: false, daysLeft: 0 })

// Football-Data.org - 100% GRÁTIS, sem limite mensal
// Registre em: https://www.football-data.org/client/register
const API_KEY = '1d1cd9e04db74a98ac8246a1668a0532'

// Ligas GRATUITAS da Football-Data.org
const LIGAS_CONFIG = {
  brasileirao: { code: 'BSA', nome: 'Brasileirão Série A', pais: '🇧🇷' },
  premier: { code: 'PL', nome: 'Premier League', pais: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  laliga: { code: 'PD', nome: 'La Liga', pais: '🇪🇸' },
  seriea: { code: 'SA', nome: 'Serie A', pais: '🇮🇹' },
  bundesliga: { code: 'BL1', nome: 'Bundesliga', pais: '🇩🇪' },
  ligue1: { code: 'FL1', nome: 'Ligue 1', pais: '🇫🇷' },
  champions: { code: 'CL', nome: 'Champions League', pais: '🏆' },
  eredivisie: { code: 'DED', nome: 'Eredivisie', pais: '🇳🇱' },
  portugal: { code: 'PPL', nome: 'Primeira Liga', pais: '🇵🇹' },
  championship: { code: 'ELC', nome: 'Championship', pais: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' }
}

const jogos = ref([])
const ligaSelecionada = ref('brasileirao')
const apiStatus = ref({ fonte: 'Football-Data.org' })

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  
  // Verificar se é admin
  userIsAdmin.value = await checkIsAdmin(session.user.id)
  
  // Calcular info do trial
  calcularTrialInfo()
  
  await carregarJogos()
})

watch(ligaSelecionada, () => carregarJogos())

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

// Verificar se trial de 3 dias está ativo
const calcularTrialInfo = () => {
  if (!user.value) return
  
  const createdAt = new Date(user.value.created_at)
  const now = new Date()
  const diffTime = now - createdAt
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 3) {
    trialInfo.value = { active: true, daysLeft: 3 - diffDays }
  } else {
    trialInfo.value = { active: false, daysLeft: 0 }
  }
}

// Verificar se usuário tem acesso completo (plano pago)
const temAcessoCompleto = computed(() => {
  const planId = subscription.value?.plan || 'free'
  // Planos pagos = acesso completo
  if (planId !== 'free') return true
  return false
})

// Sistema de análises diárias (localStorage)
const ANALISES_KEY = 'odinenx_bet_analises_vistas'
const MAX_ANALISES_FREE = 3
const analisesVistasTrigger = ref(0)

const getAnalisesVistasHoje = () => {
  try {
    const data = localStorage.getItem(ANALISES_KEY)
    if (!data) return { date: '', ids: [] }
    const parsed = JSON.parse(data)
    const hoje = new Date().toDateString()
    if (parsed.date !== hoje) {
      localStorage.setItem(ANALISES_KEY, JSON.stringify({ date: hoje, ids: [] }))
      return { date: hoje, ids: [] }
    }
    return parsed
  } catch {
    return { date: new Date().toDateString(), ids: [] }
  }
}

const salvarAnaliseVista = (jogoId) => {
  const atual = getAnalisesVistasHoje()
  if (!atual.ids.includes(jogoId)) {
    atual.ids.push(jogoId)
    atual.date = new Date().toDateString()
    localStorage.setItem(ANALISES_KEY, JSON.stringify(atual))
    analisesVistasTrigger.value++
  }
}

const analisesRestantes = computed(() => {
  const _ = analisesVistasTrigger.value
  if (temAcessoCompleto.value) return -1
  const vistas = getAnalisesVistasHoje()
  return Math.max(0, MAX_ANALISES_FREE - vistas.ids.length)
})

// Função para pegar o nível de confiança
const getNivelConfianca = (confianca) => {
  if (confianca >= 65) return { nivel: 'muito-alta', texto: '🔥 MUITO CONFIÁVEL', cor: '#00e676' }
  if (confianca >= 55) return { nivel: 'alta', texto: '✅ CONFIÁVEL', cor: '#4caf50' }
  if (confianca >= 45) return { nivel: 'media', texto: '⚠️ MODERADO', cor: '#ffc107' }
  return { nivel: 'baixa', texto: '❌ ARRISCADO', cor: '#f44336' }
}

// REMOVIDO: Agora todos os jogos são visíveis
const jogosComLimite = computed(() => {
  return jogos.value.map(j => ({ ...j, bloqueado: false }))
})

// Buscar jogos da Football-Data.org via Vercel Serverless (evita CORS)
const carregarJogos = async () => {
  loading.value = true
  erro.value = null
  jogos.value = []
  
  const liga = LIGAS_CONFIG[ligaSelecionada.value]
  
  try {
    // Buscar jogos via proxy serverless (evita CORS)
    const response = await fetch(
      `/api/football?competition=${liga.code}&status=SCHEDULED`,
      { method: 'GET' }
    )
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || `Erro HTTP: ${response.status}`)
    }
    
    const data = await response.json()
    
    if (!data.matches || data.matches.length === 0) {
      throw new Error('Nenhum jogo agendado para esta liga no momento')
    }
    
    // Processar jogos com limite baseado no plano
    const planId = subscription.value?.plan || 'free'
    let limiteJogos = 15 // Free e Basic
    
    // Admin e Elite = limite máximo
    if (userIsAdmin.value || planId === 'elite') limiteJogos = 50
    else if (planId === 'pro') limiteJogos = 30
    
    const jogosProcessados = data.matches.slice(0, limiteJogos).map(match => {
      const analise = calcularAnalise(match)
      const homeTeamName = match.homeTeam.shortName || match.homeTeam.name
      const awayTeamName = match.awayTeam.shortName || match.awayTeam.name
      
      return {
        id: match.id,
        casa: homeTeamName,
        casaLogo: getTeamLogo(homeTeamName, match.homeTeam.id) || getTeamLogo(match.homeTeam.name, match.homeTeam.id),
        fora: awayTeamName,
        foraLogo: getTeamLogo(awayTeamName, match.awayTeam.id) || getTeamLogo(match.awayTeam.name, match.awayTeam.id),
        data: formatarData(match.utcDate),
        hora: formatarHora(match.utcDate),
        estadio: match.venue || 'A definir',
        cidade: '',
        status: match.status,
        liga: data.competition?.name || liga.nome,
        ligaLogo: data.competition?.emblem || '',
        rodada: match.matchday ? `Rodada ${match.matchday}` : '',
        ...analise
      }
    })
    
    jogos.value = jogosProcessados
    lastUpdate.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    
  } catch (error) {
    console.error('Erro ao carregar jogos:', error)
    erro.value = error.message
  } finally {
    loading.value = false
  }
}

// Verificar acesso do plano a funcionalidades avançadas
const temAcessoIA = computed(() => hasAccess(subscription.value, 'iaAvancada'))

// Mapa de logos dos times via TheSportsDB (API gratuita e confiável)
const TEAM_LOGOS = {
  // Brasileirão
  'Flamengo': 'https://r2.thesportsdb.com/images/media/team/badge/syptwx1473538074.png',
  'CR Flamengo': 'https://r2.thesportsdb.com/images/media/team/badge/syptwx1473538074.png',
  'Palmeiras': 'https://r2.thesportsdb.com/images/media/team/badge/xrpupy1473538078.png',
  'SE Palmeiras': 'https://r2.thesportsdb.com/images/media/team/badge/xrpupy1473538078.png',
  'Botafogo': 'https://r2.thesportsdb.com/images/media/team/badge/p0rely1534198937.png',
  'Botafogo FR': 'https://r2.thesportsdb.com/images/media/team/badge/p0rely1534198937.png',
  'São Paulo': 'https://r2.thesportsdb.com/images/media/team/badge/xvrwus1420662838.png',
  'Corinthians': 'https://r2.thesportsdb.com/images/media/team/badge/sqrusp1424108200.png',
  'SC Corinthians Paulista': 'https://r2.thesportsdb.com/images/media/team/badge/sqrusp1424108200.png',
  'Internacional': 'https://r2.thesportsdb.com/images/media/team/badge/tyurtr1420663350.png',
  'SC Internacional': 'https://r2.thesportsdb.com/images/media/team/badge/tyurtr1420663350.png',
  'Fluminense': 'https://r2.thesportsdb.com/images/media/team/badge/yqurtu1420663337.png',
  'Fluminense FC': 'https://r2.thesportsdb.com/images/media/team/badge/yqurtu1420663337.png',
  'Atlético Mineiro': 'https://r2.thesportsdb.com/images/media/team/badge/yssqts1420662737.png',
  'Clube Atlético Mineiro': 'https://r2.thesportsdb.com/images/media/team/badge/yssqts1420662737.png',
  'Grêmio': 'https://r2.thesportsdb.com/images/media/team/badge/tsuptr1420663341.png',
  'Grêmio FBPA': 'https://r2.thesportsdb.com/images/media/team/badge/tsuptr1420663341.png',
  'Cruzeiro': 'https://r2.thesportsdb.com/images/media/team/badge/wswryq1420663320.png',
  'Cruzeiro EC': 'https://r2.thesportsdb.com/images/media/team/badge/wswryq1420663320.png',
  'Santos': 'https://r2.thesportsdb.com/images/media/team/badge/xtqtuy1420662829.png',
  'Santos FC': 'https://r2.thesportsdb.com/images/media/team/badge/xtqtuy1420662829.png',
  'Vasco da Gama': 'https://r2.thesportsdb.com/images/media/team/badge/vwvuxs1420662873.png',
  'Vasco': 'https://r2.thesportsdb.com/images/media/team/badge/vwvuxs1420662873.png',
  'CR Vasco da Gama': 'https://r2.thesportsdb.com/images/media/team/badge/vwvuxs1420662873.png',
  'Bahia': 'https://r2.thesportsdb.com/images/media/team/badge/swspws1420662759.png',
  'Fortaleza': 'https://r2.thesportsdb.com/images/media/team/badge/8t9dby1534539436.png',
  'Fortaleza EC': 'https://r2.thesportsdb.com/images/media/team/badge/8t9dby1534539436.png',
  'Athletico Paranaense': 'https://r2.thesportsdb.com/images/media/team/badge/s1c78g1634759769.png',
  'Athletico': 'https://r2.thesportsdb.com/images/media/team/badge/s1c78g1634759769.png',
  'Bragantino': 'https://r2.thesportsdb.com/images/media/team/badge/ib1dhj1598467366.png',
  'RB Bragantino': 'https://r2.thesportsdb.com/images/media/team/badge/ib1dhj1598467366.png',
  'Cuiabá': 'https://r2.thesportsdb.com/images/media/team/badge/gxrv8a1611349135.png',
  'Cuiabá EC': 'https://r2.thesportsdb.com/images/media/team/badge/gxrv8a1611349135.png',
  'Vitória': 'https://r2.thesportsdb.com/images/media/team/badge/wupttu1420662867.png',
  'EC Vitória': 'https://r2.thesportsdb.com/images/media/team/badge/wupttu1420662867.png',
  'Juventude': 'https://r2.thesportsdb.com/images/media/team/badge/wqvtrt1420663364.png',
  'Ceará': 'https://r2.thesportsdb.com/images/media/team/badge/rpyysu1420663303.png',
  'Ceará SC': 'https://r2.thesportsdb.com/images/media/team/badge/rpyysu1420663303.png',
  'Sport': 'https://r2.thesportsdb.com/images/media/team/badge/psqqxs1420662821.png',
  'Sport Recife': 'https://r2.thesportsdb.com/images/media/team/badge/psqqxs1420662821.png',
  'Coritiba': 'https://r2.thesportsdb.com/images/media/team/badge/vvqppv1420663315.png',
  'Coritiba FBC': 'https://r2.thesportsdb.com/images/media/team/badge/vvqppv1420663315.png',
  'Chapecoense': 'https://r2.thesportsdb.com/images/media/team/badge/wqqtuq1420663295.png',
  'Chapecoense AF': 'https://r2.thesportsdb.com/images/media/team/badge/wqqtuq1420663295.png',
  'Mirassol': 'https://r2.thesportsdb.com/images/media/team/badge/l2rtkl1546989207.png',
  'Mirassol FC': 'https://r2.thesportsdb.com/images/media/team/badge/l2rtkl1546989207.png',
  'Goiás': 'https://r2.thesportsdb.com/images/media/team/badge/vtxsrp1420663333.png',
  'Goiás EC': 'https://r2.thesportsdb.com/images/media/team/badge/vtxsrp1420663333.png',
  'América Mineiro': 'https://r2.thesportsdb.com/images/media/team/badge/qpvtvy1420662720.png',
  'Ponte Preta': 'https://r2.thesportsdb.com/images/media/team/badge/rqxurs1420662792.png',
  'Clube do Remo': 'https://r2.thesportsdb.com/images/media/team/badge/qypqxr1420663289.png',
  // Premier League
  'Manchester City': 'https://r2.thesportsdb.com/images/media/team/badge/vwpvry1467462651.png',
  'Arsenal': 'https://r2.thesportsdb.com/images/media/team/badge/uyhbfe1612467038.png',
  'Liverpool': 'https://r2.thesportsdb.com/images/media/team/badge/uvxuqq1448813372.png',
  'Chelsea': 'https://r2.thesportsdb.com/images/media/team/badge/yvwvtu1448813215.png',
  'Manchester United': 'https://r2.thesportsdb.com/images/media/team/badge/xzqdr11517660252.png',
  'Tottenham': 'https://r2.thesportsdb.com/images/media/team/badge/aiqiwm1534005564.png',
  'Tottenham Hotspur': 'https://r2.thesportsdb.com/images/media/team/badge/aiqiwm1534005564.png',
  'Newcastle': 'https://r2.thesportsdb.com/images/media/team/badge/qrxuxt1448813362.png',
  'Newcastle United': 'https://r2.thesportsdb.com/images/media/team/badge/qrxuxt1448813362.png',
  'Aston Villa': 'https://r2.thesportsdb.com/images/media/team/badge/qstqqr1448813518.png',
  'Brighton': 'https://r2.thesportsdb.com/images/media/team/badge/5qs0tl1500477092.png',
  'West Ham': 'https://r2.thesportsdb.com/images/media/team/badge/hpjpfy1534005566.png',
  'West Ham United': 'https://r2.thesportsdb.com/images/media/team/badge/hpjpfy1534005566.png',
  'Everton': 'https://r2.thesportsdb.com/images/media/team/badge/wqwwqx1448813200.png',
  'Fulham': 'https://r2.thesportsdb.com/images/media/team/badge/xcrqwl1510765337.png',
  'Crystal Palace': 'https://r2.thesportsdb.com/images/media/team/badge/xvtrtq1448813505.png',
  'Brentford': 'https://r2.thesportsdb.com/images/media/team/badge/rtuptr1448813157.png',
  'Wolves': 'https://r2.thesportsdb.com/images/media/team/badge/bv6dly1584379035.png',
  'Wolverhampton': 'https://r2.thesportsdb.com/images/media/team/badge/bv6dly1584379035.png',
  'Bournemouth': 'https://r2.thesportsdb.com/images/media/team/badge/y08nak1534071116.png',
  'Nottingham Forest': 'https://r2.thesportsdb.com/images/media/team/badge/rsytpy1448813382.png',
  'Ipswich': 'https://r2.thesportsdb.com/images/media/team/badge/gtjxpm1696098419.png',
  'Ipswich Town': 'https://r2.thesportsdb.com/images/media/team/badge/gtjxpm1696098419.png',
  'Leicester': 'https://r2.thesportsdb.com/images/media/team/badge/uvxrpq1448813296.png',
  'Leicester City': 'https://r2.thesportsdb.com/images/media/team/badge/uvxrpq1448813296.png',
  'Southampton': 'https://r2.thesportsdb.com/images/media/team/badge/sqprpv1448813410.png',
  // La Liga
  'Real Madrid': 'https://r2.thesportsdb.com/images/media/team/badge/vwvwvy1467542727.png',
  'Barcelona': 'https://r2.thesportsdb.com/images/media/team/badge/2ka9ef1639063236.png',
  'Atlético Madrid': 'https://r2.thesportsdb.com/images/media/team/badge/fzwqrb1668718418.png',
  'Atlético de Madrid': 'https://r2.thesportsdb.com/images/media/team/badge/fzwqrb1668718418.png',
  'Real Sociedad': 'https://r2.thesportsdb.com/images/media/team/badge/vwxysp1467542159.png',
  'Villarreal': 'https://r2.thesportsdb.com/images/media/team/badge/wxvxss1467541084.png',
  'Athletic Club': 'https://r2.thesportsdb.com/images/media/team/badge/stpswr1420227041.png',
  'Athletic Bilbao': 'https://r2.thesportsdb.com/images/media/team/badge/stpswr1420227041.png',
  'Real Betis': 'https://r2.thesportsdb.com/images/media/team/badge/srvpwy1467541128.png',
  'Sevilla': 'https://r2.thesportsdb.com/images/media/team/badge/xswrpw1467541102.png',
  'Valencia': 'https://r2.thesportsdb.com/images/media/team/badge/xpuqpv1467541247.png',
  'Girona': 'https://r2.thesportsdb.com/images/media/team/badge/5iwbzk1528108258.png',
  'Osasuna': 'https://r2.thesportsdb.com/images/media/team/badge/vxxrsw1467541283.png',
  // Serie A (Italia)
  'Inter': 'https://r2.thesportsdb.com/images/media/team/badge/ttpuwu1612467414.png',
  'Inter Milan': 'https://r2.thesportsdb.com/images/media/team/badge/ttpuwu1612467414.png',
  'Juventus': 'https://r2.thesportsdb.com/images/media/team/badge/dd4b8n1625747498.png',
  'Milan': 'https://r2.thesportsdb.com/images/media/team/badge/p68cqq1509020448.png',
  'AC Milan': 'https://r2.thesportsdb.com/images/media/team/badge/p68cqq1509020448.png',
  'Napoli': 'https://r2.thesportsdb.com/images/media/team/badge/txypvy1420231429.png',
  'Roma': 'https://r2.thesportsdb.com/images/media/team/badge/xsrxsp1467544461.png',
  'AS Roma': 'https://r2.thesportsdb.com/images/media/team/badge/xsrxsp1467544461.png',
  'Lazio': 'https://r2.thesportsdb.com/images/media/team/badge/qwtuyp1467285412.png',
  'Atalanta': 'https://r2.thesportsdb.com/images/media/team/badge/rvyxwu1448808872.png',
  'Fiorentina': 'https://r2.thesportsdb.com/images/media/team/badge/ysyxsw1420227034.png',
  'Bologna': 'https://r2.thesportsdb.com/images/media/team/badge/ysquyv1420229122.png',
  'Torino': 'https://r2.thesportsdb.com/images/media/team/badge/vqxvqt1467285553.png',
  // Bundesliga
  'Bayern München': 'https://r2.thesportsdb.com/images/media/team/badge/rwqrpr1467379633.png',
  'Bayern Munich': 'https://r2.thesportsdb.com/images/media/team/badge/rwqrpr1467379633.png',
  'Borussia Dortmund': 'https://r2.thesportsdb.com/images/media/team/badge/vpxwys1467378360.png',
  'RB Leipzig': 'https://r2.thesportsdb.com/images/media/team/badge/ywywuq1534074521.png',
  'Bayer Leverkusen': 'https://r2.thesportsdb.com/images/media/team/badge/qxsxxw1467378380.png',
  'Bayer 04 Leverkusen': 'https://r2.thesportsdb.com/images/media/team/badge/qxsxxw1467378380.png',
  'Frankfurt': 'https://r2.thesportsdb.com/images/media/team/badge/2o1yfu1635160627.png',
  'Eintracht Frankfurt': 'https://r2.thesportsdb.com/images/media/team/badge/2o1yfu1635160627.png',
  'Wolfsburg': 'https://r2.thesportsdb.com/images/media/team/badge/tqvxpv1467378397.png',
  'VfL Wolfsburg': 'https://r2.thesportsdb.com/images/media/team/badge/tqvxpv1467378397.png',
  'Freiburg': 'https://r2.thesportsdb.com/images/media/team/badge/tw8prp1467378360.png',
  'SC Freiburg': 'https://r2.thesportsdb.com/images/media/team/badge/tw8prp1467378360.png',
  'Hoffenheim': 'https://r2.thesportsdb.com/images/media/team/badge/j8qqom1534073295.png',
  'TSG Hoffenheim': 'https://r2.thesportsdb.com/images/media/team/badge/j8qqom1534073295.png',
  "Gladbach": 'https://r2.thesportsdb.com/images/media/team/badge/trswqu1467378382.png',
  "Borussia M'gladbach": 'https://r2.thesportsdb.com/images/media/team/badge/trswqu1467378382.png',
  'Stuttgart': 'https://r2.thesportsdb.com/images/media/team/badge/klvgtl1510176668.png',
  'VfB Stuttgart': 'https://r2.thesportsdb.com/images/media/team/badge/klvgtl1510176668.png',
  // Ligue 1
  'Paris Saint-Germain': 'https://r2.thesportsdb.com/images/media/team/badge/rwqsvp1467465916.png',
  'PSG': 'https://r2.thesportsdb.com/images/media/team/badge/rwqsvp1467465916.png',
  'Monaco': 'https://r2.thesportsdb.com/images/media/team/badge/xuxwtr1467465875.png',
  'AS Monaco': 'https://r2.thesportsdb.com/images/media/team/badge/xuxwtr1467465875.png',
  'Marseille': 'https://r2.thesportsdb.com/images/media/team/badge/upptws1467465818.png',
  'Lyon': 'https://r2.thesportsdb.com/images/media/team/badge/gxvqxs1467465862.png',
  'Lille': 'https://r2.thesportsdb.com/images/media/team/badge/3mv26y1533649655.png'
}

// Cache local de logos buscados da API
const logoCache = ref({})

// Gerar logo placeholder baseado no nome do time
const getTeamLogo = (teamName, teamId = null) => {
  // Primeiro tenta no mapa de logos conhecidos
  if (TEAM_LOGOS[teamName]) {
    return TEAM_LOGOS[teamName]
  }
  // Fallback para avatar gerado com cores do tema
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName)}&background=1a1a2e&color=00e5ff&size=100&bold=true&format=png`
}
  // Fallback para avatar gerado
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(teamName)}&background=1a1a2e&color=00e5ff&size=100&bold=true&format=svg`
}

// Função para gerar "hash" numérico a partir de string (para variação consistente)
const hashString = (str) => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

// Times com força conhecida (ranking aproximado)
const TIMES_FORCA = {
  // Brasileirão
  'Flamengo': 95, 'Palmeiras': 94, 'Botafogo': 88, 'São Paulo': 86, 'Internacional': 85,
  'Fluminense': 84, 'Atlético Mineiro': 85, 'Mineiro': 85, 'Grêmio': 83, 'Cruzeiro': 82,
  'Corinthians': 80, 'Bahia': 78, 'Vasco da Gama': 76, 'Vasco': 76, 'Santos': 82,
  'Athletico Paranaense': 77, 'Athletico': 77, 'Fortaleza': 79, 'Bragantino': 75,
  'Cuiabá': 68, 'Goiás': 70, 'América Mineiro': 72, 'Coritiba': 69, 'Vitória': 71,
  'Juventude': 66, 'Chapecoense': 64, 'Ceará': 70, 'Sport': 68, 'Ponte Preta': 65,
  'Mirassol': 67, 'Clube do Remo': 63,
  // Premier League
  'Manchester City': 96, 'Arsenal': 93, 'Liverpool': 94, 'Chelsea': 87, 'Manchester United': 85,
  'Tottenham': 84, 'Newcastle': 82, 'Brighton': 78, 'Aston Villa': 80, 'West Ham': 76,
  'Crystal Palace': 72, 'Wolves': 73, 'Fulham': 71, 'Everton': 70, 'Brentford': 74,
  'Nottingham Forest': 69, 'Bournemouth': 68, 'Burnley': 65, 'Sheffield Utd': 62, 'Luton': 60,
  // La Liga
  'Real Madrid': 96, 'Barcelona': 95, 'Atlético Madrid': 87, 'Real Sociedad': 82, 'Villarreal': 80,
  'Athletic Bilbao': 79, 'Real Betis': 78, 'Sevilla': 77, 'Valencia': 75, 'Osasuna': 72,
  // Serie A
  'Inter': 92, 'Juventus': 88, 'Milan': 87, 'Napoli': 86, 'Roma': 82, 'Lazio': 80, 'Atalanta': 83,
  'Fiorentina': 78, 'Bologna': 75, 'Torino': 72,
  // Bundesliga
  'Bayern München': 95, 'Borussia Dortmund': 88, 'RB Leipzig': 85, 'Bayer Leverkusen': 90,
  'Frankfurt': 78, 'Wolfsburg': 75, 'Freiburg': 77, 'Hoffenheim': 73, 'Gladbach': 74
}

// Calcular análise baseada nos dados do jogo
const calcularAnalise = (match) => {
  const homeTeamName = match.homeTeam?.name || match.homeTeam?.shortName || 'Casa'
  const awayTeamName = match.awayTeam?.name || match.awayTeam?.shortName || 'Fora'
  
  // Buscar força dos times (ou gerar baseado no hash do nome)
  const getForca = (name) => {
    for (const [key, value] of Object.entries(TIMES_FORCA)) {
      if (name.toLowerCase().includes(key.toLowerCase()) || key.toLowerCase().includes(name.toLowerCase())) {
        return value
      }
    }
    return 60 + (hashString(name) % 20)
  }
  
  const forcaCasa = getForca(homeTeamName)
  const forcaFora = getForca(awayTeamName)
  
  // Fator casa (vantagem de 8-12%)
  const fatorCasa = 1.10 + (hashString(match.id?.toString() || homeTeamName) % 5) / 100
  
  // Calcular probabilidades
  const forcaCasaAjustada = forcaCasa * fatorCasa
  const total = forcaCasaAjustada + forcaFora
  
  let probCasa = Math.round((forcaCasaAjustada / total) * 85)
  let probFora = Math.round((forcaFora / total) * 75)
  
  // Adicionar variação baseada no ID do jogo
  const variacao = (hashString(match.id?.toString() || '1') % 15) - 7
  probCasa = Math.max(25, Math.min(75, probCasa + variacao))
  probFora = Math.max(15, Math.min(65, probFora - variacao / 2))
  
  // Empate é o resto
  let probEmpate = 100 - probCasa - probFora
  probEmpate = Math.max(15, Math.min(35, probEmpate))
  
  // Ajustar para somar 100%
  const soma = probCasa + probEmpate + probFora
  probCasa = Math.round((probCasa / soma) * 100)
  probFora = Math.round((probFora / soma) * 100)
  probEmpate = 100 - probCasa - probFora
  
  // Estimar odds baseado nas probabilidades
  const oddCasa = probCasa > 0 ? (95 / probCasa).toFixed(2) : '-'
  const oddEmpate = probEmpate > 0 ? (92 / probEmpate).toFixed(2) : '-'
  const oddFora = probFora > 0 ? (93 / probFora).toFixed(2) : '-'
  
  // Expected goals baseado na força
  const mediaGols = ((forcaCasa + forcaFora) / 2 - 60) / 10
  const xgTotal = 2.2 + mediaGols * 0.3 + (hashString(match.id?.toString() || '1') % 10) / 10
  const xgCasa = (xgTotal * (probCasa / 100) * 1.5).toFixed(1)
  const xgFora = (xgTotal * (probFora / 100) * 1.3).toFixed(1)
  
  // Prob Over/Under
  const probOver25 = Math.round(35 + mediaGols * 15 + (hashString(homeTeamName) % 20))
  const probUnder25 = 100 - probOver25
  const oddOver25 = (95 / probOver25).toFixed(2)
  const oddUnder25 = (95 / probUnder25).toFixed(2)
  
  // Determinar melhor aposta
  let melhorAposta = 'Análise pendente'
  let confianca = 0
  
  if (probCasa >= 55) {
    melhorAposta = `Vitória ${match.homeTeam?.shortName || homeTeamName}`
    confianca = probCasa
  } else if (probFora >= 48) {
    melhorAposta = `Vitória ${match.awayTeam?.shortName || awayTeamName}`
    confianca = probFora
  } else if (probOver25 >= 58) {
    melhorAposta = 'Over 2.5 Gols'
    confianca = probOver25
  } else if (probCasa > probFora && probCasa >= 40) {
    melhorAposta = `${match.homeTeam?.shortName || homeTeamName} ou Empate`
    confianca = probCasa + probEmpate
  } else if (probFora >= 35) {
    melhorAposta = `${match.awayTeam?.shortName || awayTeamName} ou Empate`
    confianca = probFora + probEmpate
  } else {
    melhorAposta = 'Empate'
    confianca = probEmpate + 25
  }
  
  // Limitar confiança entre 35-80%
  confianca = Math.max(35, Math.min(80, confianca))
  
  return {
    oddCasa,
    oddEmpate,
    oddFora,
    oddOver25,
    oddUnder25,
    oddBTTSYes: '-',
    oddBTTSNo: '-',
    probCasa,
    probEmpate,
    probFora,
    probOver25,
    probUnder25,
    probBTTS: 0,
    xgCasa: parseFloat(xgCasa),
    xgFora: parseFloat(xgFora),
    melhorAposta,
    confianca: Math.round(confianca),
    bookmaker: 'Análise ODINENX',
    hasOdds: true
  }
}
const formatarData = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

const formatarHora = (dateStr) => {
  return new Date(dateStr).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

const selecionarJogo = (jogo) => {
  // Verificar se já viu este jogo hoje
  const vistas = getAnalisesVistasHoje()
  const jaViu = vistas.ids.includes(jogo.id)
  
  // Se tem acesso completo ou já viu este jogo, abre direto
  if (temAcessoCompleto.value || jaViu) {
    jogoSelecionado.value = jogo
    if (!jaViu) salvarAnaliseVista(jogo.id)
    return
  }
  
  // Se ainda tem análises disponíveis, abre e salva
  if (analisesRestantes.value > 0) {
    salvarAnaliseVista(jogo.id)
    jogoSelecionado.value = jogo
  } else {
    // Limite atingido - mostra modal de upgrade
    jogoSelecionado.value = { ...jogo, showUpgrade: true }
  }
}
const fecharModal = () => { jogoSelecionado.value = null }
const logout = async () => { await supabase.auth.signOut(); router.push('/') }
const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value }
const navigateTo = (path) => { router.push(path); mobileMenuOpen.value = false }
</script>

<template>
  <div class="bet-page">
    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header">
        <div class="header-left">
          <h1>⚽ Módulo BET</h1>
          <p>Análise inteligente de apostas esportivas</p>
          <div class="api-status-row">
            <span class="api-badge real" v-if="!loading && jogos.length > 0">
              <span class="pulse-dot"></span>
              DADOS REAIS
            </span>
            <span class="api-badge loading" v-else-if="loading">
              <span class="loading-dot"></span>
              CARREGANDO...
            </span>
            <span class="last-update" v-if="lastUpdate">Atualizado: {{ lastUpdate }}</span>
          </div>
        </div>
        <div class="header-right">
          <div class="liga-selector">
            <select v-model="ligaSelecionada">
              <option value="brasileirao">🇧🇷 Brasileirão</option>
              <option value="premier">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier</option>
              <option value="laliga">🇪🇸 La Liga</option>
              <option value="seriea">🇮🇹 Serie A</option>
              <option value="bundesliga">🇩🇪 Bundesliga</option>
              <option value="ligue1">🇫🇷 Ligue 1</option>
              <option value="champions">🏆 UCL</option>
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
        <p>Carregando jogos...</p>
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
          <span>{{ jogosComLimite.length }} jogos disponíveis • Análise <strong>ODINENX IA</strong></span>
        </div>
        
        <!-- Trial/Limite Banner -->
        <div v-if="temAcessoCompleto" class="trial-banner success">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <div class="trial-text">
            <strong>Acesso Completo!</strong>
            <span>Análises ilimitadas disponíveis</span>
          </div>
        </div>
        
        <div v-else class="trial-banner info">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          <div class="trial-text">
            <strong>🎯 {{ analisesRestantes }}/3 análises restantes hoje</strong>
            <span>Todos os palpites visíveis. <router-link to="/pricing">Upgrade para ilimitado</router-link></span>
          </div>
        </div>
        
        <div class="disclaimer-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <p>Probabilidades calculadas pela IA ODINENX. Aposte com responsabilidade.</p>
        </div>

        <div class="jogos-grid">
          <div v-for="jogo in jogosComLimite" :key="jogo.id" class="jogo-card" :class="getNivelConfianca(jogo.confianca).nivel" @click="selecionarJogo(jogo)">
            <!-- Indicador de Confiança -->
            <div class="confianca-indicador" :class="getNivelConfianca(jogo.confianca).nivel">
              <span class="confianca-texto">{{ getNivelConfianca(jogo.confianca).texto }}</span>
              <span class="confianca-numero">{{ jogo.confianca }}%</span>
            </div>
            
            <div class="jogo-header">
              <div class="jogo-info">
                <span class="jogo-data">{{ jogo.data }} • {{ jogo.hora }}</span>
                <span class="jogo-local">{{ jogo.estadio }}</span>
              </div>
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
            
            <!-- Melhor Aposta Destaque -->
            <div class="melhor-aposta-destaque" :class="getNivelConfianca(jogo.confianca).nivel">
              <span class="label">🎯 MELHOR APOSTA:</span>
              <span class="valor">{{ jogo.melhorAposta }}</span>
            </div>
            
            <!-- CTA -->
            <div class="jogo-cta">
              <span>👆 Toque para ver análise completa</span>
            </div>
          </div>
        </div>

        <div v-if="jogosComLimite.length === 0" class="no-games">
          <p>Nenhum jogo encontrado para esta liga.</p>
        </div>
      </div>

      <!-- Modal Upgrade (jogo bloqueado) -->
      <div v-if="jogoSelecionado && jogoSelecionado.showUpgrade" class="modal-overlay" @click.self="fecharModal">
        <div class="modal-upgrade-jogo">
          <button class="modal-close" @click="fecharModal">×</button>
          
          <div class="upgrade-glow"></div>
          
          <div class="upgrade-header">
            <div class="upgrade-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="32" height="32"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <h2>Análise Premium</h2>
            <p>Desbloqueie insights avançados deste jogo</p>
          </div>
          
          <div class="upgrade-jogo-preview">
            <div class="preview-times">
              <div class="preview-team">
                <img :src="jogoSelecionado.casaLogo" @error="$event.target.src = '/icone.webp'">
                <span>{{ jogoSelecionado.casa }}</span>
              </div>
              <span class="preview-vs">VS</span>
              <div class="preview-team">
                <img :src="jogoSelecionado.foraLogo" @error="$event.target.src = '/icone.webp'">
                <span>{{ jogoSelecionado.fora }}</span>
              </div>
            </div>
          </div>
          
          <div class="upgrade-features">
            <div class="feature-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Análise completa H2H</span>
            </div>
            <div class="feature-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Odds de 6+ casas de apostas</span>
            </div>
            <div class="feature-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Recomendação ODINENX IA</span>
            </div>
            <div class="feature-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Estatísticas detalhadas</span>
            </div>
          </div>
          
          <div class="upgrade-cta">
            <router-link to="/pricing" class="btn-upgrade-main">
              <span>Ver Planos</span>
              <span class="btn-price">a partir de R$19,90</span>
            </router-link>
            <p class="upgrade-note">7 dias de garantia de satisfação</p>
          </div>
        </div>
      </div>

      <!-- Modal Análise (jogo liberado) -->
      <div v-if="jogoSelecionado && !jogoSelecionado.showUpgrade" class="modal-overlay" @click.self="fecharModal">
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

    <!-- Bottom Navigation Mobile -->
    <BottomNav :showAdmin="userIsAdmin" />
  </div>
</template>

<style scoped>
/* ===== BET PAGE - Layout Moderno ===== */
.bet-page { 
  min-height: 100vh; 
  min-height: 100dvh;
  background: #000; 
  color: #fff; 
}

.main-content { 
  padding: 20px;
  padding-top: calc(20px + env(safe-area-inset-top));
  padding-bottom: calc(100px + env(safe-area-inset-bottom));
  max-width: 1200px;
  margin: 0 auto;
}

/* Page Header */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; gap: 15px; }
.header-left h1 { font-size: 1.8rem; font-weight: 800; margin-bottom: 8px; }
.header-left p { color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; font-size: 0.9rem; }
.header-right { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.liga-selector select { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 10px 15px; color: #fff; font-size: 0.9rem; cursor: pointer; }
.liga-selector select option { background: #1a1a1a; color: #fff; }

/* API Status */
.api-status-row { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
.api-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.api-badge.real { background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2)); border: 1px solid rgba(34, 197, 94, 0.5); color: #22c55e; }
.api-badge.loading { background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.4); color: #fbbf24; }
.pulse-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; box-shadow: 0 0 8px #22c55e; }
.loading-dot { width: 8px; height: 8px; background: #fbbf24; border-radius: 50%; animation: blink 1s infinite; }
.last-update { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }

@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.btn-refresh { width: 44px; height: 44px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
.btn-refresh:hover { background: rgba(255, 255, 255, 0.2); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-refresh svg { width: 20px; height: 20px; stroke: #fff; }
.btn-refresh svg.spinning { animation: spin 1s linear infinite; }

/* Loading & Error States */
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

/* Bet Content */
.bet-content .api-badge { display: flex; align-items: center; gap: 10px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 12px 20px; margin-bottom: 15px; }
.bet-content .api-badge svg { width: 20px; height: 20px; stroke: #22c55e; }
.bet-content .api-badge span { font-size: 0.85rem; color: rgba(255, 255, 255, 0.8); }

.disclaimer-box { display: flex; align-items: center; gap: 15px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; }
.disclaimer-box svg { width: 24px; height: 24px; stroke: #fbbf24; flex-shrink: 0; }
.disclaimer-box p { font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); }

.no-games { text-align: center; padding: 60px 20px; color: rgba(255, 255, 255, 0.5); }

/* Jogos Grid */
.jogos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.jogo-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.3s; }
.jogo-card:hover { transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.05); }
.jogo-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }
.jogo-info { display: flex; flex-direction: column; gap: 3px; }
.jogo-data { font-size: 0.85rem; color: rgba(255, 255, 255, 0.7); }
.jogo-local { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }
.jogo-times { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.time { display: flex; flex-direction: column; align-items: center; gap: 8px; flex: 1; }
.time img { width: 50px; height: 50px; object-fit: contain; border-radius: 10px; background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid rgba(255, 255, 255, 0.1); padding: 6px; }
.time-nome { font-weight: 600; font-size: 0.85rem; text-align: center; }
.time-odd { font-size: 0.75rem; color: #3b82f6; background: rgba(59, 130, 246, 0.1); padding: 3px 8px; border-radius: 8px; font-weight: 600; }
.versus { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.vs { font-size: 0.75rem; color: rgba(255, 255, 255, 0.3); }
.xg { font-size: 1.1rem; font-weight: 700; color: rgba(255, 255, 255, 0.6); }
.probabilidades-bar { display: flex; height: 28px; border-radius: 8px; overflow: hidden; margin-bottom: 12px; }
.prob { display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 600; min-width: 35px; }
.prob.casa { background: #22c55e; color: #000; }
.prob.empate { background: #6b7280; color: #fff; }
.prob.fora { background: #3b82f6; color: #fff; }
.no-odds-bar { display: flex; align-items: center; justify-content: center; height: 28px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-bottom: 12px; }
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
.time-modal img { width: 70px; height: 70px; object-fit: contain; border-radius: 12px; background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid rgba(255, 255, 255, 0.1); padding: 10px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); }
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

/* NOVO: Indicador de Confiança Visual */
.confianca-indicador {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 15px;
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
  font-size: 0.85rem;
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

/* NOVO: Melhor Aposta Destaque */
.melhor-aposta-destaque {
  background: rgba(255, 255, 255, 0.08);
  padding: 15px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 12px;
}

.melhor-aposta-destaque .label {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.melhor-aposta-destaque .valor {
  display: block;
  font-size: 1.1rem;
  font-weight: 900;
}

.melhor-aposta-destaque.muito-alta .valor { color: #00e676; }
.melhor-aposta-destaque.alta .valor { color: #4caf50; }
.melhor-aposta-destaque.media .valor { color: #ffc107; }
.melhor-aposta-destaque.baixa .valor { color: #f44336; }

/* NOVO: CTA */
.jogo-cta {
  text-align: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

/* Trial Banner Info */
.trial-banner.info {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.trial-banner.info svg { 
  stroke: #3b82f6; 
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}
.trial-banner.info strong { color: #3b82f6; }

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

@media (max-width: 768px) {
  .main-content {
    padding: 15px;
    padding-bottom: calc(100px + env(safe-area-inset-bottom));
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
    gap: 12px;
  }
  
  .header-left h1 { font-size: 1.5rem; }
  
  .header-right {
    flex-direction: row;
    justify-content: center;
    gap: 10px;
  }
  
  .liga-selector select {
    padding: 10px 12px;
    font-size: 0.85rem;
  }
  
  .jogos-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .jogo-card { padding: 16px; }
  .time img { width: 45px; height: 45px; }
  .time-nome { font-size: 0.8rem; }
  
  /* Modal */
  .modal-overlay { 
    padding: 0;
    align-items: flex-end;
  }
  
  .modal-analise {
    max-height: 90vh;
    border-radius: 20px 20px 0 0;
    margin: 0;
  }
  
  .odds-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .mercados-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .header-left h1 { font-size: 1.3rem; }
  
  .jogo-times {
    gap: 5px;
  }
  
  .time img { width: 40px; height: 40px; padding: 4px; }
  .time-nome { font-size: 0.75rem; }
  .time-odd { font-size: 0.7rem; padding: 2px 6px; }
  
  .probabilidades-bar { height: 24px; }
  .prob { font-size: 0.65rem; min-width: 30px; }
  
  .confianca-indicador { padding: 10px 12px; }
  .confianca-texto { font-size: 0.75rem; }
  .confianca-numero { font-size: 1.1rem; }
  
  .melhor-aposta-destaque { padding: 12px; }
  .melhor-aposta-destaque .valor { font-size: 1rem; }
  
  .odds-grid { grid-template-columns: 1fr; gap: 8px; }
  .odd-card { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    padding: 12px; 
  }
  
  .recomendacao-texto { font-size: 1.1rem; }
}

/* ===== SAFARI FIXES ===== */
.header-right,
.jogo-footer {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
}

/* Fix para transform no Safari */
.jogo-card:hover {
  -webkit-transform: translateY(-5px);
  transform: translateY(-5px);
}

.spinner {
  -webkit-animation: spin 1s linear infinite;
  animation: spin 1s linear infinite;
}

/* ===== TRIAL/LIMITE BANNERS ===== */
.trial-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.trial-banner.success {
  background: rgba(76, 175, 80, 0.15);
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.trial-banner.success svg {
  color: #4caf50;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.trial-banner.warning {
  background: rgba(255, 193, 7, 0.15);
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.trial-banner.warning svg {
  color: #ffc107;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.trial-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trial-text strong {
  font-size: 0.9rem;
  color: #fff;
}

.trial-text span {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.trial-text a {
  color: #ffc107;
  text-decoration: underline;
}

/* ===== JOGO BLOQUEADO ===== */
.jogo-card.bloqueado {
  position: relative;
  cursor: pointer;
}

.jogo-card.bloqueado::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 14px;
  z-index: 1;
  pointer-events: none;
}

.jogo-bloqueado-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  z-index: 2;
  background: rgba(0, 0, 0, 0.85);
  padding: 16px 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.jogo-bloqueado-overlay svg {
  width: 28px;
  height: 28px;
  color: #ffc107;
}

.jogo-bloqueado-overlay span {
  font-size: 0.75rem;
  color: #ffc107;
  font-weight: 600;
  white-space: nowrap;
}

.blur-content {
  filter: blur(4px);
  pointer-events: none;
}

.confianca-badge.bloqueado {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.probabilidades-bar.bloqueado {
  opacity: 0.5;
}

.probabilidades-bar.bloqueado .prob {
  filter: blur(2px);
}

.melhor-aposta.bloqueado {
  color: rgba(255, 193, 7, 0.8);
}

.melhor-aposta.bloqueado svg {
  width: 16px;
  height: 16px;
}

.btn-desbloquear {
  background: linear-gradient(135deg, #ffc107, #ff9800) !important;
  color: #000 !important;
}

.btn-desbloquear:hover {
  filter: brightness(1.1);
}

/* ===== MODAL UPGRADE PREMIUM ===== */
.modal-upgrade-jogo {
  background: linear-gradient(145deg, #1a1a2e, #16162a);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 24px;
  width: 100%;
  max-width: 400px;
  padding: 32px;
  position: relative;
  text-align: center;
  overflow: hidden;
}

.upgrade-glow {
  position: absolute;
  top: -50%;
  left: 50%;
  transform: translateX(-50%);
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, transparent 70%);
  pointer-events: none;
}

.upgrade-header {
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}

.upgrade-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upgrade-icon svg {
  color: #8b5cf6;
}

.upgrade-header h2 {
  font-size: 1.4rem;
  margin-bottom: 8px;
  color: #fff;
  font-weight: 700;
}

.upgrade-header p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.upgrade-jogo-preview {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
}

.preview-times {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.preview-team {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-team img {
  width: 40px;
  height: 40px;
  object-fit: contain;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px;
}

.preview-team span {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  max-width: 80px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-vs {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 700;
}

.upgrade-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
}

.feature-item svg {
  width: 18px;
  height: 18px;
  color: #22c55e;
  flex-shrink: 0;
}

.feature-item span {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.85);
}

.upgrade-cta {
  margin-top: 8px;
}

.btn-upgrade-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  padding: 16px 24px;
  border-radius: 14px;
  text-decoration: none;
  transition: all 0.3s ease;
  gap: 4px;
}

.btn-upgrade-main:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4);
}

.btn-price {
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.85;
}

.upgrade-note {
  margin-top: 12px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 768px) {
  .trial-banner {
    flex-direction: column;
    text-align: center;
    gap: 8px;
    padding: 16px;
  }
  
  .trial-text {
    align-items: center;
  }
  
  .jogo-bloqueado-overlay {
    padding: 12px 18px;
  }
  
  .jogo-bloqueado-overlay svg {
    width: 22px;
    height: 22px;
  }
  
  .jogo-bloqueado-overlay span {
    font-size: 0.7rem;
  }
  
  .modal-upgrade-jogo {
    padding: 24px;
    margin: 20px;
    max-width: calc(100% - 40px);
  }
  
  .upgrade-header h2 {
    font-size: 1.2rem;
  }
}
</style>
