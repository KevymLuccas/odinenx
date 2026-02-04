// API de Odds Gratuitas para usuários Free
// Usa API-Football (100 requests/dia grátis)

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  const { league = 71, fixture } = req.query // 71 = Brasileirão
  
  // API-Football - Plano Free: 100 requests/dia
  const API_KEY = process.env.FOOTBALL_API_KEY || process.env.API_FOOTBALL_KEY
  
  // Mapeamento de ligas
  const LEAGUES = {
    'BSA': 71,   // Brasileirão Série A
    'BSB': 72,   // Brasileirão Série B
    'PL': 39,    // Premier League
    'PD': 140,   // La Liga
    'SA': 135,   // Serie A Italia
    'BL1': 78,   // Bundesliga
    'FL1': 61,   // Ligue 1
    'CL': 2,     // Champions League
    'EL': 3,     // Europa League
    'COP': 73    // Copa do Brasil
  }

  const leagueId = LEAGUES[league] || league

  try {
    // Se não tem API key, retorna odds estimadas
    if (!API_KEY) {
      return res.status(200).json({
        success: true,
        source: 'estimated',
        message: 'Odds estimadas baseadas em estatísticas',
        odds: generateEstimatedOdds(leagueId)
      })
    }

    // Buscar fixtures com odds
    const url = fixture 
      ? `https://v3.football.api-sports.io/odds?fixture=${fixture}`
      : `https://v3.football.api-sports.io/odds?league=${leagueId}&season=2025`
    
    const response = await fetch(url, {
      headers: {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
      }
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()
    
    // Processar odds
    const processedOdds = data.response?.map(item => processOdds(item)) || []

    return res.status(200).json({
      success: true,
      source: 'api-football',
      odds: processedOdds,
      remaining: response.headers.get('x-ratelimit-requests-remaining'),
      updated_at: new Date().toISOString()
    })

  } catch (error) {
    console.error('Erro ao buscar odds:', error)
    
    // Fallback para odds estimadas
    return res.status(200).json({
      success: true,
      source: 'estimated',
      message: 'Usando odds estimadas',
      odds: generateEstimatedOdds(leagueId),
      error: error.message
    })
  }
}

// Processar odds da API
function processOdds(item) {
  const fixture = item.fixture
  const bookmakers = item.bookmakers || []
  
  // Pegar odds de múltiplas casas
  const oddsData = bookmakers.map(bm => {
    const h2hBet = bm.bets?.find(b => b.name === 'Match Winner' || b.name === '1X2')
    if (!h2hBet) return null
    
    const outcomes = {}
    h2hBet.values?.forEach(v => {
      if (v.value === 'Home') outcomes.home = parseFloat(v.odd)
      if (v.value === 'Draw') outcomes.draw = parseFloat(v.odd)
      if (v.value === 'Away') outcomes.away = parseFloat(v.odd)
    })
    
    return {
      name: bm.name,
      key: bm.name.toLowerCase().replace(/\s+/g, ''),
      icon: getBookmakerIcon(bm.name),
      odds: outcomes
    }
  }).filter(Boolean)
  
  // Calcular estatísticas
  const stats = calculateStats(oddsData)
  const probs = calculateProbabilities(stats.average)
  
  return {
    fixture_id: fixture.id,
    home_team: item.league?.home || 'Casa',
    away_team: item.league?.away || 'Fora',
    date: fixture.date,
    bookmakers: oddsData,
    stats,
    probabilities: probs,
    analysis: generateAnalysis(stats, probs)
  }
}

// Ícones das casas de apostas
function getBookmakerIcon(name) {
  const icons = {
    'Bet365': '🟢',
    'Betfair': '🟡',
    '1xBet': '🔷',
    'Pinnacle': '🔵',
    'Betway': '⚫',
    'Unibet': '🟣',
    'William Hill': '🟤',
    'Bwin': '🟠',
    'Marathon Bet': '🔴',
    'Sportingbet': '💚'
  }
  return icons[name] || '📊'
}

// Calcular estatísticas das odds
function calculateStats(oddsData) {
  if (oddsData.length === 0) {
    return { average: { home: 2.0, draw: 3.5, away: 3.5 }, best: {}, worst: {} }
  }
  
  const homeOdds = oddsData.map(b => b.odds.home).filter(Boolean)
  const drawOdds = oddsData.map(b => b.odds.draw).filter(Boolean)
  const awayOdds = oddsData.map(b => b.odds.away).filter(Boolean)
  
  return {
    average: {
      home: homeOdds.length ? (homeOdds.reduce((a, b) => a + b, 0) / homeOdds.length).toFixed(2) : 0,
      draw: drawOdds.length ? (drawOdds.reduce((a, b) => a + b, 0) / drawOdds.length).toFixed(2) : 0,
      away: awayOdds.length ? (awayOdds.reduce((a, b) => a + b, 0) / awayOdds.length).toFixed(2) : 0
    },
    best: {
      home: Math.max(...homeOdds, 0),
      draw: Math.max(...drawOdds, 0),
      away: Math.max(...awayOdds, 0)
    },
    worst: {
      home: Math.min(...homeOdds, 0),
      draw: Math.min(...drawOdds, 0),
      away: Math.min(...awayOdds, 0)
    },
    count: oddsData.length
  }
}

// Calcular probabilidades implícitas
function calculateProbabilities(avgOdds) {
  const homeProb = avgOdds.home > 0 ? (1 / avgOdds.home) * 100 : 0
  const drawProb = avgOdds.draw > 0 ? (1 / avgOdds.draw) * 100 : 0
  const awayProb = avgOdds.away > 0 ? (1 / avgOdds.away) * 100 : 0
  
  const total = homeProb + drawProb + awayProb
  
  return {
    home: total > 0 ? Math.round((homeProb / total) * 100) : 33,
    draw: total > 0 ? Math.round((drawProb / total) * 100) : 34,
    away: total > 0 ? Math.round((awayProb / total) * 100) : 33,
    overround: (total - 100).toFixed(1)
  }
}

// Gerar análise explicativa
function generateAnalysis(stats, probs) {
  const reasons = []
  
  if (probs.home > 50) {
    reasons.push(`Time da casa tem ${probs.home}% de chance segundo as casas de apostas`)
    reasons.push(`Odds média de @${stats.average.home} indica favoritismo claro`)
  } else if (probs.away > 50) {
    reasons.push(`Time visitante surpreende com ${probs.away}% de chance`)
    reasons.push(`Mesmo fora, odds de @${stats.average.away} mostra confiança do mercado`)
  } else {
    reasons.push(`Jogo equilibrado: casa ${probs.home}% x fora ${probs.away}%`)
    reasons.push(`Empate com ${probs.draw}% pode ser interessante`)
  }
  
  if (parseFloat(stats.average.draw) > 3.5) {
    reasons.push(`Odd de empate alta (@${stats.average.draw}) - times devem buscar vitória`)
  }
  
  return reasons
}

// Gerar odds estimadas (fallback)
function generateEstimatedOdds(leagueId) {
  // Dados base para demonstração
  const matches = [
    { home: 'Flamengo', away: 'Palmeiras', homePos: 1, awayPos: 2 },
    { home: 'Corinthians', away: 'São Paulo', homePos: 8, awayPos: 5 },
    { home: 'Atlético-MG', away: 'Cruzeiro', homePos: 3, awayPos: 12 },
    { home: 'Botafogo', away: 'Fluminense', homePos: 4, awayPos: 10 },
    { home: 'Internacional', away: 'Grêmio', homePos: 6, awayPos: 7 }
  ]
  
  return matches.map((match, idx) => {
    const homeStrength = (22 - match.homePos) * 1.35
    const awayStrength = (22 - match.awayPos)
    const total = homeStrength + awayStrength + 8
    
    const homeProb = Math.round((homeStrength / total) * 100)
    const awayProb = Math.round((awayStrength / total) * 100)
    const drawProb = 100 - homeProb - awayProb
    
    const homeOdd = (100 / homeProb * 1.05).toFixed(2)
    const drawOdd = (100 / drawProb * 1.05).toFixed(2)
    const awayOdd = (100 / awayProb * 1.05).toFixed(2)
    
    return {
      fixture_id: `est_${idx}`,
      home_team: match.home,
      away_team: match.away,
      date: new Date(Date.now() + idx * 86400000).toISOString(),
      bookmakers: [
        {
          name: 'Estimativa ODINENX',
          key: 'odinenx',
          icon: '🎯',
          odds: { home: parseFloat(homeOdd), draw: parseFloat(drawOdd), away: parseFloat(awayOdd) }
        }
      ],
      stats: {
        average: { home: homeOdd, draw: drawOdd, away: awayOdd },
        count: 1
      },
      probabilities: { home: homeProb, draw: drawProb, away: awayProb },
      analysis: [
        `${match.home} está em ${match.homePos}º lugar - ${homeProb}% de chance`,
        `${match.away} está em ${match.awayPos}º lugar - ${awayProb}% de chance`,
        match.homePos < match.awayPos 
          ? `Mandante favorito por estar melhor na tabela`
          : `Visitante chega em melhor fase`,
        `Vantagem de jogar em casa adiciona ~10% de chance`
      ]
    }
  })
}
