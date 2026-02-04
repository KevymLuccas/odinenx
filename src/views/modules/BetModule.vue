<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../../lib/supabase'
import { getSubscriptionStatus, plans, hasAccess, isAdmin as checkIsAdmin } from '../../lib/stripe'

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

// Mapa de logos dos times mais populares (fontes públicas - Wikipedia/Commons)
const TEAM_LOGOS = {
  // Brasileirão
  'Flamengo': 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg',
  'CR Flamengo': 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg',
  'Palmeiras': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg',
  'SE Palmeiras': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg',
  'Botafogo': 'https://upload.wikimedia.org/wikipedia/commons/1/12/Botafogo_de_Futebol_e_Regatas_logo.svg',
  'Botafogo FR': 'https://upload.wikimedia.org/wikipedia/commons/1/12/Botafogo_de_Futebol_e_Regatas_logo.svg',
  'São Paulo': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg',
  'Corinthians': 'https://upload.wikimedia.org/wikipedia/pt/b/b4/Corinthians_simbolo.png',
  'SC Corinthians Paulista': 'https://upload.wikimedia.org/wikipedia/pt/b/b4/Corinthians_simbolo.png',
  'Internacional': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg',
  'SC Internacional': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg',
  'Fluminense': 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Fluminense_fc_logo.svg',
  'Fluminense FC': 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Fluminense_fc_logo.svg',
  'Atlético Mineiro': 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Atletico_mineiro_galo.png',
  'Clube Atlético Mineiro': 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Atletico_mineiro_galo.png',
  'Grêmio': 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Gremio.svg',
  'Grêmio FBPA': 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Gremio.svg',
  'Cruzeiro': 'https://upload.wikimedia.org/wikipedia/commons/9/90/Cruzeiro_Esporte_Clube_%28logo%29.svg',
  'Cruzeiro EC': 'https://upload.wikimedia.org/wikipedia/commons/9/90/Cruzeiro_Esporte_Clube_%28logo%29.svg',
  'Santos': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Santos_Logo.png',
  'Santos FC': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Santos_Logo.png',
  'Vasco da Gama': 'https://upload.wikimedia.org/wikipedia/pt/c/cb/Vasco_da_Gama_logo.png',
  'Vasco': 'https://upload.wikimedia.org/wikipedia/pt/c/cb/Vasco_da_Gama_logo.png',
  'CR Vasco da Gama': 'https://upload.wikimedia.org/wikipedia/pt/c/cb/Vasco_da_Gama_logo.png',
  'Bahia': 'https://upload.wikimedia.org/wikipedia/pt/3/3b/ECBahia.png',
  'Fortaleza': 'https://upload.wikimedia.org/wikipedia/commons/c/c9/Fortaleza_Esporte_Clube_%28logo%29.svg',
  'Athletico Paranaense': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Club_Athletico_Paranaense_2019.svg',
  'Athletico': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Club_Athletico_Paranaense_2019.svg',
  'Bragantino': 'https://upload.wikimedia.org/wikipedia/pt/2/27/Red_Bull_Bragantino.png',
  'RB Bragantino': 'https://upload.wikimedia.org/wikipedia/pt/2/27/Red_Bull_Bragantino.png',
  'Cuiabá': 'https://upload.wikimedia.org/wikipedia/commons/7/7e/Cuiab%C3%A1_Esporte_Clube.png',
  'Cuiabá EC': 'https://upload.wikimedia.org/wikipedia/commons/7/7e/Cuiab%C3%A1_Esporte_Clube.png',
  'Vitória': 'https://upload.wikimedia.org/wikipedia/pt/5/53/ECVitoria.png',
  'EC Vitória': 'https://upload.wikimedia.org/wikipedia/pt/5/53/ECVitoria.png',
  'Juventude': 'https://upload.wikimedia.org/wikipedia/pt/d/db/ECJuventude.png',
  'Ceará': 'https://upload.wikimedia.org/wikipedia/commons/8/88/Cear%C3%A1_Sporting_Club_logo.svg',
  'Sport': 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Sport_Club_Recife.png',
  'Coritiba': 'https://upload.wikimedia.org/wikipedia/commons/2/20/Coritiba_FBC_-_Paran%C3%A1_-_Brasil.svg',
  'Coritiba FBC': 'https://upload.wikimedia.org/wikipedia/commons/2/20/Coritiba_FBC_-_Paran%C3%A1_-_Brasil.svg',
  'Chapecoense': 'https://upload.wikimedia.org/wikipedia/pt/9/9e/Chapecoense.png',
  'Chapecoense AF': 'https://upload.wikimedia.org/wikipedia/pt/9/9e/Chapecoense.png',
  'Mirassol': 'https://upload.wikimedia.org/wikipedia/pt/e/e0/Mirassol_Futebol_Clube.png',
  'Mirassol FC': 'https://upload.wikimedia.org/wikipedia/pt/e/e0/Mirassol_Futebol_Clube.png',
  'Goiás': 'https://upload.wikimedia.org/wikipedia/commons/7/7f/Goias_Esporte_Clube_logo.svg',
  'América Mineiro': 'https://upload.wikimedia.org/wikipedia/pt/6/6c/Am%C3%A9rica_FC_%28MG%29.png',
  'Ponte Preta': 'https://upload.wikimedia.org/wikipedia/commons/c/c0/AAPontePreta.svg',
  'Clube do Remo': 'https://upload.wikimedia.org/wikipedia/pt/c/c9/Clube_do_Remo.png',
  // Premier League
  'Manchester City': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg',
  'Arsenal': 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg',
  'Liverpool': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg',
  'Chelsea': 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg',
  'Manchester United': 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg',
  'Tottenham': 'https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg',
  'Tottenham Hotspur': 'https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg',
  'Newcastle': 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg',
  'Newcastle United': 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg',
  'Aston Villa': 'https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg',
  'Brighton': 'https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg',
  'West Ham': 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg',
  'West Ham United': 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg',
  'Everton': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg',
  'Fulham': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg',
  'Crystal Palace': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Crystal_Palace_FC_logo.svg',
  'Brentford': 'https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg',
  'Wolverhampton': 'https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg',
  'Wolves': 'https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg',
  'Bournemouth': 'https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg',
  'Nottingham Forest': 'https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg',
  'Ipswich': 'https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg',
  'Ipswich Town': 'https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg',
  'Leicester': 'https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg',
  'Leicester City': 'https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg',
  'Southampton': 'https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg',
  // La Liga
  'Real Madrid': 'https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg',
  'Barcelona': 'https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg',
  'Atlético Madrid': 'https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_Madrid_2017_logo.svg',
  'Atlético de Madrid': 'https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_Madrid_2017_logo.svg',
  'Real Sociedad': 'https://upload.wikimedia.org/wikipedia/en/f/f1/Real_Sociedad_logo.svg',
  'Villarreal': 'https://upload.wikimedia.org/wikipedia/en/b/b9/Villarreal_CF_logo.svg',
  'Athletic Club': 'https://upload.wikimedia.org/wikipedia/en/9/98/Athletic_Club_Bilbao_logo.svg',
  'Athletic Bilbao': 'https://upload.wikimedia.org/wikipedia/en/9/98/Athletic_Club_Bilbao_logo.svg',
  'Real Betis': 'https://upload.wikimedia.org/wikipedia/en/1/13/Real_betis_logo.svg',
  'Sevilla': 'https://upload.wikimedia.org/wikipedia/en/3/3b/Sevilla_FC_logo.svg',
  'Valencia': 'https://upload.wikimedia.org/wikipedia/en/c/ce/Valenciacf.svg',
  'Girona': 'https://upload.wikimedia.org/wikipedia/en/9/90/Girona_FC.svg',
  'Osasuna': 'https://upload.wikimedia.org/wikipedia/en/4/4b/Osasuna_logo.svg',
  // Serie A (Italia)
  'Inter': 'https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg',
  'Inter Milan': 'https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg',
  'Juventus': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Juventus_FC_2017_logo.svg',
  'Milan': 'https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg',
  'AC Milan': 'https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg',
  'Napoli': 'https://upload.wikimedia.org/wikipedia/commons/2/2d/SSC_Neapel.svg',
  'Roma': 'https://upload.wikimedia.org/wikipedia/en/f/f7/AS_Roma_logo_%282017%29.svg',
  'AS Roma': 'https://upload.wikimedia.org/wikipedia/en/f/f7/AS_Roma_logo_%282017%29.svg',
  'Lazio': 'https://upload.wikimedia.org/wikipedia/en/c/ce/S.S._Lazio_badge.svg',
  'Atalanta': 'https://upload.wikimedia.org/wikipedia/en/6/66/AtalantaBC.svg',
  'Fiorentina': 'https://upload.wikimedia.org/wikipedia/commons/8/8c/ACF_Fiorentina_2022.svg',
  'Bologna': 'https://upload.wikimedia.org/wikipedia/commons/5/5b/Bologna_F.C._1909_logo.svg',
  'Torino': 'https://upload.wikimedia.org/wikipedia/en/2/2e/Torino_FC_Logo.svg',
  // Bundesliga
  'Bayern München': 'https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg',
  'Bayern Munich': 'https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg',
  'Borussia Dortmund': 'https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg',
  'RB Leipzig': 'https://upload.wikimedia.org/wikipedia/en/0/04/RB_Leipzig_2014_logo.svg',
  'Bayer Leverkusen': 'https://upload.wikimedia.org/wikipedia/en/5/59/Bayer_04_Leverkusen_logo.svg',
  'Bayer 04 Leverkusen': 'https://upload.wikimedia.org/wikipedia/en/5/59/Bayer_04_Leverkusen_logo.svg',
  'Frankfurt': 'https://upload.wikimedia.org/wikipedia/commons/0/04/Eintracht_Frankfurt_Logo.svg',
  'Eintracht Frankfurt': 'https://upload.wikimedia.org/wikipedia/commons/0/04/Eintracht_Frankfurt_Logo.svg',
  'Wolfsburg': 'https://upload.wikimedia.org/wikipedia/commons/f/f3/Logo-VfL-Wolfsburg.svg',
  'VfL Wolfsburg': 'https://upload.wikimedia.org/wikipedia/commons/f/f3/Logo-VfL-Wolfsburg.svg',
  'Freiburg': 'https://upload.wikimedia.org/wikipedia/en/6/6d/SC_Freiburg_logo.svg',
  'SC Freiburg': 'https://upload.wikimedia.org/wikipedia/en/6/6d/SC_Freiburg_logo.svg',
  'Hoffenheim': 'https://upload.wikimedia.org/wikipedia/commons/e/e7/Logo_TSG_Hoffenheim.svg',
  'TSG Hoffenheim': 'https://upload.wikimedia.org/wikipedia/commons/e/e7/Logo_TSG_Hoffenheim.svg',
  'Gladbach': 'https://upload.wikimedia.org/wikipedia/commons/8/81/Borussia_M%C3%B6nchengladbach_logo.svg',
  "Borussia M'gladbach": 'https://upload.wikimedia.org/wikipedia/commons/8/81/Borussia_M%C3%B6nchengladbach_logo.svg',
  'Stuttgart': 'https://upload.wikimedia.org/wikipedia/commons/e/eb/VfB_Stuttgart_1893_Logo.svg',
  'VfB Stuttgart': 'https://upload.wikimedia.org/wikipedia/commons/e/eb/VfB_Stuttgart_1893_Logo.svg',
  // Ligue 1
  'Paris Saint-Germain': 'https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg',
  'PSG': 'https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg',
  'Monaco': 'https://upload.wikimedia.org/wikipedia/en/5/5d/AS_Monaco_FC.svg',
  'Marseille': 'https://upload.wikimedia.org/wikipedia/commons/d/d8/Olympique_Marseille_logo.svg',
  'Lyon': 'https://upload.wikimedia.org/wikipedia/en/c/c6/Olympique_Lyonnais.svg',
  'Lille': 'https://upload.wikimedia.org/wikipedia/en/3/3f/Lille_OSC_2018_logo.svg'
}

// Gerar logo placeholder baseado no nome do time
const getTeamLogo = (teamName, teamId = null) => {
  // Primeiro tenta no mapa de logos conhecidos
  if (TEAM_LOGOS[teamName]) {
    return TEAM_LOGOS[teamName]
  }
  // Se tiver ID, usa a URL do football-data.org através de um proxy
  if (teamId) {
    return `https://crests.football-data.org/${teamId}.png`
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
          <div class="api-fonte">
            <span class="fonte-badge">⚽ Football-Data.org</span>
          </div>
          <div class="liga-selector">
            <select v-model="ligaSelecionada">
              <option value="brasileirao">🇧🇷 Brasileirão Série A</option>
              <option value="premier">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League</option>
              <option value="laliga">🇪🇸 La Liga</option>
              <option value="seriea">🇮🇹 Serie A</option>
              <option value="bundesliga">🇩🇪 Bundesliga</option>
              <option value="ligue1">🇫🇷 Ligue 1</option>
              <option value="champions">🏆 Champions League</option>
              <option value="eredivisie">🇳🇱 Eredivisie</option>
              <option value="portugal">🇵🇹 Primeira Liga</option>
              <option value="championship">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship</option>
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
          
          <div class="upgrade-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <h2>Análise Bloqueada</h2>
            <p>Seu trial de 3 dias expirou</p>
          </div>
          
          <div class="upgrade-jogo-preview">
            <span class="preview-label">Você quer ver:</span>
            <div class="preview-times">
              <img :src="jogoSelecionado.casaLogo" @error="$event.target.src = '/icone.webp'">
              <span>{{ jogoSelecionado.casa }} vs {{ jogoSelecionado.fora }}</span>
              <img :src="jogoSelecionado.foraLogo" @error="$event.target.src = '/icone.webp'">
            </div>
          </div>
          
          <div class="upgrade-benefits">
            <h4>Faça upgrade para desbloquear:</h4>
            <ul>
              <li>✓ Palpites ilimitados</li>
              <li>✓ Análise completa de cada jogo</li>
              <li>✓ Estatísticas H2H detalhadas</li>
              <li>✓ Odds de múltiplas casas</li>
              <li>✓ Recomendações ODINENX IA</li>
            </ul>
          </div>
          
          <div class="upgrade-plans">
            <router-link to="/settings" class="btn-upgrade-primary">
              Ver Planos a partir de R$79/mês
            </router-link>
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
  </div>
</template>

<style scoped>
.dashboard { 
  display: -webkit-box;
  display: -webkit-flex;
  display: flex; 
  min-height: 100vh; 
  min-height: 100dvh;
  min-height: -webkit-fill-available;
  background: #000; 
  color: #fff; 
}
.sidebar { 
  width: 260px; 
  background: rgba(10, 10, 10, 0.95); 
  border-right: 1px solid rgba(255, 255, 255, 0.1); 
  display: -webkit-box;
  display: -webkit-flex;
  display: flex; 
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column; 
  position: fixed; 
  height: 100vh;
  height: 100dvh; 
  z-index: 100;
  -webkit-transform: translateZ(0);
  transform: translateZ(0);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
}
.sidebar-header { padding: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.sidebar-logo { height: 40px; width: auto; }
.sidebar-nav { -webkit-box-flex: 1; -webkit-flex: 1; flex: 1; padding: 20px 15px; display: -webkit-box; display: -webkit-flex; display: flex; -webkit-box-orient: vertical; -webkit-box-direction: normal; -webkit-flex-direction: column; flex-direction: column; gap: 5px; overflow-y: auto; -webkit-overflow-scrolling: touch; }
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
.mobile-menu-btn svg { width: 28px; height: 28px; stroke: #000; }
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
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
}
.mobile-menu.open { -webkit-transform: translateY(0); transform: translateY(0); }
.mobile-menu-header { text-align: center; margin-bottom: 20px; }
.mobile-logo { height: 35px; }
.mobile-nav { display: -webkit-box; display: -webkit-flex; display: flex; -webkit-box-orient: vertical; -webkit-box-direction: normal; -webkit-flex-direction: column; flex-direction: column; gap: 8px; }
.mobile-nav-item { padding: 15px 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #fff; font-weight: 500; cursor: pointer; -webkit-transition: all 0.3s; transition: all 0.3s; text-align: left; -webkit-tap-highlight-color: transparent; }
.mobile-nav-item:hover, .mobile-nav-item.active { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); }
.mobile-logout { width: 100%; margin-top: 15px; padding: 15px; background: transparent; border: 1px solid #ef4444; border-radius: 12px; color: #ef4444; font-weight: 600; cursor: pointer; -webkit-tap-highlight-color: transparent; }

.main-content { 
  -webkit-box-flex: 1; 
  -webkit-flex: 1; 
  flex: 1; 
  margin-left: 260px; 
  padding: 30px;
  padding-top: calc(30px + env(safe-area-inset-top));
  padding-bottom: calc(30px + env(safe-area-inset-bottom));
  -webkit-overflow-scrolling: touch;
}
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; gap: 20px; }
.header-left h1 { font-size: 2rem; font-weight: 800; margin-bottom: 8px; }
.header-left p { color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; }
.header-right { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.liga-selector select { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 12px 20px; color: #fff; font-size: 1rem; cursor: pointer; }
.liga-selector select option { background: #1a1a1a; color: #fff; }

/* API Status */
.api-status-row { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
.api-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.api-badge.real { background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2)); border: 1px solid rgba(34, 197, 94, 0.5); color: #22c55e; }
.api-badge.loading { background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.4); color: #fbbf24; }
.pulse-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; box-shadow: 0 0 8px #22c55e; }
.loading-dot { width: 8px; height: 8px; background: #fbbf24; border-radius: 50%; animation: blink 1s infinite; }
.last-update { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }
.api-fonte { display: flex; align-items: center; gap: 8px; }
.fonte-badge { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #3b82f6; padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 600; }

@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
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
.time img { width: 60px; height: 60px; object-fit: contain; border-radius: 10px; background: rgba(255, 255, 255, 0.1); padding: 6px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); }
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
.time-modal img { width: 70px; height: 70px; object-fit: contain; border-radius: 12px; background: rgba(255, 255, 255, 0.1); padding: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); }
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

@media (max-width: 968px) {
  /* Sidebar e Menu Mobile */
  .sidebar { display: none !important; }
  
  .mobile-menu-btn { 
    display: flex !important;
    position: fixed !important;
    top: 15px !important;
    right: 15px !important;
    width: 48px !important;
    height: 48px !important;
    z-index: 1001 !important;
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-size: 1.5rem !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
  }
  
  .mobile-overlay { display: block; }
  .mobile-menu { display: block; }
  
  /* Conteúdo Principal */
  .main-content { 
    margin-left: 0 !important; 
    padding: 70px 15px 120px 15px !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
  }
  
  /* Grid de Jogos */
  .jogos-grid { 
    grid-template-columns: 1fr !important; 
    gap: 15px !important; 
    width: 100% !important;
  }
  
  /* Header da Página */
  .page-header { 
    flex-direction: column !important; 
    align-items: center !important; 
    text-align: center !important; 
    gap: 15px !important;
    width: 100% !important;
  }
  .header-left { text-align: center !important; width: 100% !important; }
  .header-left h1 { font-size: 1.4rem !important; }
  .header-right { 
    width: 100% !important; 
    display: flex !important; 
    flex-direction: column !important; 
    align-items: center !important; 
    gap: 10px !important; 
  }
  .liga-selector { width: 100% !important; max-width: 100% !important; }
  .liga-selector select { width: 100% !important; text-align: center !important; }
  .api-fonte { justify-content: center !important; }
  
  /* Cards de Jogos */
  .jogo-card { 
    padding: 15px !important;
    width: 100% !important;
    box-sizing: border-box !important;
  }
  .jogo-times { gap: 8px !important; }
  .time img { width: 40px !important; height: 40px !important; }
  .time-nome { font-size: 0.8rem !important; }
  
  /* Modal */
  .modal-overlay { padding: 10px !important; align-items: flex-end !important; }
  .modal-analise { 
    max-height: 85vh !important; 
    border-radius: 20px 20px 0 0 !important;
    padding: 15px !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
  }
  .odds-grid { grid-template-columns: repeat(3, 1fr) !important; gap: 8px !important; }
  .odd-card { padding: 10px 6px !important; }
  .odd-value { font-size: 1rem !important; }
  .mercados-grid { grid-template-columns: 1fr !important; gap: 10px !important; }
}

@media (max-width: 480px) {
  .main-content { 
    padding: 70px 12px 130px 12px !important;
  }
  .header-left h1 { font-size: 1.3rem !important; }
  
  /* Times em coluna no mobile pequeno */
  .jogo-times { 
    flex-direction: column !important; 
    gap: 12px !important; 
  }
  .time { 
    flex-direction: row !important; 
    width: 100% !important; 
    justify-content: flex-start !important; 
    gap: 10px !important; 
  }
  .time img { width: 36px !important; height: 36px !important; }
  .time-nome { text-align: left !important; font-size: 0.85rem !important; }
  .versus { padding: 8px 0 !important; font-size: 0.75rem !important; }
  
  /* Barra de Probabilidades */
  .probabilidades-bar { height: 30px !important; }
  .prob { font-size: 0.65rem !important; min-width: 25px !important; }
  
  /* Odds em coluna */
  .odds-grid { grid-template-columns: 1fr !important; gap: 8px !important; }
  .odd-card { 
    display: flex !important; 
    justify-content: space-between !important; 
    align-items: center !important; 
    padding: 12px !important; 
  }
  .odd-label { margin-bottom: 0 !important; font-size: 0.8rem !important; }
  .odd-value { margin-bottom: 0 !important; font-size: 1rem !important; }
  
  /* Modal Header */
  .modal-header-jogo { flex-direction: column !important; gap: 15px !important; }
  .time-modal { flex-direction: row !important; gap: 10px !important; }
  .time-modal img { width: 45px !important; height: 45px !important; }
  .time-modal h3 { font-size: 0.95rem !important; text-align: left !important; }
  
  .recomendacao-texto { font-size: 1.1rem !important; }
  
  .jogo-footer { 
    flex-direction: column !important; 
    align-items: flex-start !important;
    gap: 8px !important;
  }
  .melhor-aposta { width: 100% !important; }
}

/* ===== SAFARI FIXES ===== */
.dashboard { 
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
}

.sidebar-nav,
.mobile-nav,
.header-right,
.jogo-footer {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
}

/* Fix gap para Safari antigo */
@supports not (gap: 10px) {
  .jogos-grid > * { margin-bottom: 15px; }
  .jogo-times > * { margin-right: 10px; }
}

/* Fix para inputs no Safari */
input, select, textarea, button {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  border-radius: 10px;
}

/* Fix scroll Safari */
.main-content {
  -webkit-overflow-scrolling: touch;
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

/* ===== MODAL UPGRADE ===== */
.modal-upgrade-jogo {
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  width: 100%;
  max-width: 420px;
  padding: 32px;
  position: relative;
  text-align: center;
}

.upgrade-header {
  margin-bottom: 24px;
}

.upgrade-header svg {
  color: #ffc107;
  margin-bottom: 16px;
}

.upgrade-header h2 {
  font-size: 1.4rem;
  margin-bottom: 8px;
  color: #fff;
}

.upgrade-header p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.upgrade-jogo-preview {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.preview-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  display: block;
  margin-bottom: 12px;
}

.preview-times {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.preview-times img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 6px;
}

.preview-times span {
  font-size: 0.9rem;
  font-weight: 600;
  color: #fff;
}

.upgrade-benefits {
  text-align: left;
  margin-bottom: 24px;
}

.upgrade-benefits h4 {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 12px;
}

.upgrade-benefits ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.upgrade-benefits li {
  font-size: 0.85rem;
  color: #fff;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.upgrade-benefits li:last-child {
  border-bottom: none;
}

.upgrade-plans {
  margin-top: 20px;
}

.btn-upgrade-primary {
  display: inline-block;
  width: 100%;
  background: linear-gradient(135deg, #ffc107, #ff9800);
  color: #000;
  font-weight: 700;
  font-size: 0.95rem;
  padding: 14px 24px;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.3s ease;
}

.btn-upgrade-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 193, 7, 0.3);
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
