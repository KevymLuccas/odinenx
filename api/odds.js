// API de Odds Reais - Integração com The Odds API
// Agrega odds de múltiplas casas de apostas

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  const { sport = 'soccer', region = 'br', markets = 'h2h', bookmakers } = req.query
  
  // API Key do The Odds API - DEVE estar configurada nas variáveis de ambiente do Vercel
  const API_KEY = process.env.ODDS_API_KEY
  
  if (!API_KEY) {
    console.error('ODDS_API_KEY não configurada')
    return res.status(500).json({ error: 'API não configurada', demo: true, odds: [] })
  }
  
  // Mapeamento de ligas para The Odds API
  const LEAGUES = {
    // Brasil
    'BSA': 'soccer_brazil_campeonato',
    'BSB': 'soccer_brazil_serie_b',
    // Europa
    'PL': 'soccer_epl',
    'PD': 'soccer_spain_la_liga',
    'SA': 'soccer_italy_serie_a',
    'BL1': 'soccer_germany_bundesliga',
    'FL1': 'soccer_france_ligue_one',
    'CL': 'soccer_uefa_champs_league',
    'EL': 'soccer_uefa_europa_league',
    // Outros
    'PPL': 'soccer_portugal_primeira_liga',
    'DED': 'soccer_netherlands_eredivisie',
    'MLS': 'soccer_usa_mls'
  }

  // Casas de apostas disponíveis
  const BOOKMAKERS_INFO = {
    'bet365': { name: 'Bet365', icon: '🟢', country: 'UK' },
    'betfair': { name: 'Betfair', icon: '🟡', country: 'UK' },
    'pinnacle': { name: 'Pinnacle', icon: '🔵', country: 'Curaçao' },
    '1xbet': { name: '1xBet', icon: '🔷', country: 'Curaçao' },
    'betway': { name: 'Betway', icon: '⚫', country: 'Malta' },
    'unibet': { name: 'Unibet', icon: '🟣', country: 'Malta' },
    'williamhill': { name: 'William Hill', icon: '🟤', country: 'UK' },
    'bovada': { name: 'Bovada', icon: '🔴', country: 'Curaçao' },
    'draftkings': { name: 'DraftKings', icon: '🟠', country: 'USA' },
    'fanduel': { name: 'FanDuel', icon: '💙', country: 'USA' },
    'betonline': { name: 'BetOnline', icon: '🖤', country: 'Panama' },
    'mybookieag': { name: 'MyBookie', icon: '💜', country: 'Curaçao' },
    'betmgm': { name: 'BetMGM', icon: '💛', country: 'USA' },
    'pointsbetus': { name: 'PointsBet', icon: '🧡', country: 'Australia' },
    'superbook': { name: 'SuperBook', icon: '💚', country: 'USA' },
    'betsson': { name: 'Betsson', icon: '🩵', country: 'Malta' },
    'nordicbet': { name: 'NordicBet', icon: '🩶', country: 'Malta' }
  }

  try {
    const league = req.query.league
    const sportKey = league ? LEAGUES[league] : null
    
    // Se tem liga específica, busca só dela
    let url = `https://api.the-odds-api.com/v4/sports/${sportKey || 'soccer_brazil_campeonato'}/odds/`
    url += `?apiKey=${API_KEY}`
    url += `&regions=${region}`
    url += `&markets=${markets}`
    url += `&oddsFormat=decimal`
    
    if (bookmakers) {
      url += `&bookmakers=${bookmakers}`
    }

    const response = await fetch(url)
    
    if (!response.ok) {
      // Se a API principal falhar, retorna dados simulados para demonstração
      if (response.status === 401 || response.status === 403) {
        return res.status(200).json({
          success: true,
          demo: true,
          message: 'Usando dados de demonstração. Configure ODDS_API_KEY para odds reais.',
          odds: generateDemoOdds(league),
          bookmakers: BOOKMAKERS_INFO,
          remaining_requests: 'N/A (demo)'
        })
      }
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()
    const remainingRequests = response.headers.get('x-requests-remaining')

    // Processar e enriquecer dados
    const processedOdds = data.map(match => processMatch(match, BOOKMAKERS_INFO))

    return res.status(200).json({
      success: true,
      demo: false,
      odds: processedOdds,
      bookmakers: BOOKMAKERS_INFO,
      remaining_requests: remainingRequests,
      updated_at: new Date().toISOString()
    })

  } catch (error) {
    console.error('Erro ao buscar odds:', error)
    
    // Retorna dados de demonstração em caso de erro
    return res.status(200).json({
      success: true,
      demo: true,
      message: 'Usando dados de demonstração devido a erro na API.',
      odds: generateDemoOdds(req.query.league),
      bookmakers: BOOKMAKERS_INFO,
      error: error.message
    })
  }
}

// Processa cada partida e calcula estatísticas
function processMatch(match, bookmakersInfo) {
  const { id, sport_key, sport_title, commence_time, home_team, away_team, bookmakers } = match
  
  // Agregar todas as odds por resultado
  const oddsAggregated = {
    home: [],
    draw: [],
    away: []
  }
  
  const bookmakerOdds = bookmakers.map(bm => {
    const h2hMarket = bm.markets.find(m => m.key === 'h2h')
    if (!h2hMarket) return null
    
    const outcomes = {}
    h2hMarket.outcomes.forEach(o => {
      if (o.name === home_team) {
        outcomes.home = o.price
        oddsAggregated.home.push(o.price)
      } else if (o.name === away_team) {
        outcomes.away = o.price
        oddsAggregated.away.push(o.price)
      } else if (o.name === 'Draw') {
        outcomes.draw = o.price
        oddsAggregated.draw.push(o.price)
      }
    })
    
    return {
      key: bm.key,
      name: bookmakersInfo[bm.key]?.name || bm.title,
      icon: bookmakersInfo[bm.key]?.icon || '📊',
      last_update: bm.last_update,
      odds: outcomes
    }
  }).filter(Boolean)
  
  // Calcular estatísticas
  const stats = calculateOddsStats(oddsAggregated)
  
  // Calcular probabilidades implícitas (média)
  const impliedProbs = calculateImpliedProbabilities(stats.average)
  
  // Encontrar value bets
  const valueBets = findValueBets(bookmakerOdds, impliedProbs)
  
  return {
    id,
    sport_key,
    sport_title,
    commence_time,
    home_team,
    away_team,
    bookmakers: bookmakerOdds,
    stats,
    implied_probabilities: impliedProbs,
    value_bets: valueBets,
    best_odds: {
      home: { value: stats.best.home, bookmaker: findBestBookmaker(bookmakerOdds, 'home', stats.best.home) },
      draw: { value: stats.best.draw, bookmaker: findBestBookmaker(bookmakerOdds, 'draw', stats.best.draw) },
      away: { value: stats.best.away, bookmaker: findBestBookmaker(bookmakerOdds, 'away', stats.best.away) }
    },
    worst_odds: {
      home: stats.worst.home,
      draw: stats.worst.draw,
      away: stats.worst.away
    }
  }
}

// Calcular estatísticas das odds
function calculateOddsStats(aggregated) {
  const calc = (arr) => {
    if (arr.length === 0) return { avg: 0, best: 0, worst: 0, spread: 0 }
    const avg = arr.reduce((a, b) => a + b, 0) / arr.length
    const best = Math.max(...arr)
    const worst = Math.min(...arr)
    return { avg: Number(avg.toFixed(2)), best, worst, spread: Number((best - worst).toFixed(2)) }
  }
  
  const home = calc(aggregated.home)
  const draw = calc(aggregated.draw)
  const away = calc(aggregated.away)
  
  return {
    average: { home: home.avg, draw: draw.avg, away: away.avg },
    best: { home: home.best, draw: draw.best, away: away.best },
    worst: { home: home.worst, draw: draw.worst, away: away.worst },
    spread: { home: home.spread, draw: draw.spread, away: away.spread },
    bookmakers_count: aggregated.home.length
  }
}

// Calcular probabilidades implícitas das odds
function calculateImpliedProbabilities(avgOdds) {
  const homeProb = avgOdds.home > 0 ? (1 / avgOdds.home) * 100 : 0
  const drawProb = avgOdds.draw > 0 ? (1 / avgOdds.draw) * 100 : 0
  const awayProb = avgOdds.away > 0 ? (1 / avgOdds.away) * 100 : 0
  
  // Calcular overround (margem da casa)
  const total = homeProb + drawProb + awayProb
  const overround = total - 100
  
  // Probabilidades ajustadas (removendo overround)
  const adjustedHome = (homeProb / total) * 100
  const adjustedDraw = (drawProb / total) * 100
  const adjustedAway = (awayProb / total) * 100
  
  return {
    raw: {
      home: Number(homeProb.toFixed(1)),
      draw: Number(drawProb.toFixed(1)),
      away: Number(awayProb.toFixed(1))
    },
    adjusted: {
      home: Number(adjustedHome.toFixed(1)),
      draw: Number(adjustedDraw.toFixed(1)),
      away: Number(adjustedAway.toFixed(1))
    },
    overround: Number(overround.toFixed(2)),
    fair_odds: {
      home: Number((100 / adjustedHome).toFixed(2)),
      draw: Number((100 / adjustedDraw).toFixed(2)),
      away: Number((100 / adjustedAway).toFixed(2))
    }
  }
}

// Encontrar value bets
function findValueBets(bookmakerOdds, impliedProbs) {
  const valueBets = []
  const threshold = 3 // Mínimo de % de value para considerar
  
  bookmakerOdds.forEach(bm => {
    // Verificar casa
    if (bm.odds.home) {
      const impliedProb = (1 / bm.odds.home) * 100
      const value = impliedProbs.adjusted.home - impliedProb
      if (value > threshold) {
        valueBets.push({
          bookmaker: bm.name,
          bookmaker_key: bm.key,
          icon: bm.icon,
          outcome: 'home',
          odds: bm.odds.home,
          value_percentage: Number(value.toFixed(1)),
          implied_prob: Number(impliedProb.toFixed(1)),
          fair_prob: impliedProbs.adjusted.home
        })
      }
    }
    
    // Verificar empate
    if (bm.odds.draw) {
      const impliedProb = (1 / bm.odds.draw) * 100
      const value = impliedProbs.adjusted.draw - impliedProb
      if (value > threshold) {
        valueBets.push({
          bookmaker: bm.name,
          bookmaker_key: bm.key,
          icon: bm.icon,
          outcome: 'draw',
          odds: bm.odds.draw,
          value_percentage: Number(value.toFixed(1)),
          implied_prob: Number(impliedProb.toFixed(1)),
          fair_prob: impliedProbs.adjusted.draw
        })
      }
    }
    
    // Verificar fora
    if (bm.odds.away) {
      const impliedProb = (1 / bm.odds.away) * 100
      const value = impliedProbs.adjusted.away - impliedProb
      if (value > threshold) {
        valueBets.push({
          bookmaker: bm.name,
          bookmaker_key: bm.key,
          icon: bm.icon,
          outcome: 'away',
          odds: bm.odds.away,
          value_percentage: Number(value.toFixed(1)),
          implied_prob: Number(impliedProb.toFixed(1)),
          fair_prob: impliedProbs.adjusted.away
        })
      }
    }
  })
  
  // Ordenar por maior value
  return valueBets.sort((a, b) => b.value_percentage - a.value_percentage)
}

// Encontrar qual bookmaker tem a melhor odd
function findBestBookmaker(bookmakerOdds, outcome, bestValue) {
  const bm = bookmakerOdds.find(b => b.odds[outcome] === bestValue)
  return bm ? { name: bm.name, key: bm.key, icon: bm.icon } : null
}

// Gerar dados de demonstração
function generateDemoOdds(league) {
  const demoMatches = [
    {
      home_team: 'Flamengo',
      away_team: 'Palmeiras',
      bookmakers: [
        { name: 'Bet365', key: 'bet365', icon: '🟢', home: 2.10, draw: 3.40, away: 3.50 },
        { name: 'Betfair', key: 'betfair', icon: '🟡', home: 2.15, draw: 3.35, away: 3.45 },
        { name: '1xBet', key: '1xbet', icon: '🔷', home: 2.12, draw: 3.38, away: 3.52 },
        { name: 'Pinnacle', key: 'pinnacle', icon: '🔵', home: 2.18, draw: 3.42, away: 3.48 }
      ]
    },
    {
      home_team: 'Corinthians',
      away_team: 'São Paulo',
      bookmakers: [
        { name: 'Bet365', key: 'bet365', icon: '🟢', home: 2.45, draw: 3.25, away: 2.90 },
        { name: 'Betfair', key: 'betfair', icon: '🟡', home: 2.50, draw: 3.20, away: 2.85 },
        { name: '1xBet', key: '1xbet', icon: '🔷', home: 2.48, draw: 3.22, away: 2.88 },
        { name: 'Pinnacle', key: 'pinnacle', icon: '🔵', home: 2.52, draw: 3.28, away: 2.92 }
      ]
    },
    {
      home_team: 'Atlético-MG',
      away_team: 'Cruzeiro',
      bookmakers: [
        { name: 'Bet365', key: 'bet365', icon: '🟢', home: 1.85, draw: 3.60, away: 4.20 },
        { name: 'Betfair', key: 'betfair', icon: '🟡', home: 1.88, draw: 3.55, away: 4.15 },
        { name: '1xBet', key: '1xbet', icon: '🔷', home: 1.87, draw: 3.58, away: 4.18 },
        { name: 'Pinnacle', key: 'pinnacle', icon: '🔵', home: 1.90, draw: 3.62, away: 4.25 }
      ]
    }
  ]
  
  return demoMatches.map((match, index) => {
    const aggregated = {
      home: match.bookmakers.map(b => b.home),
      draw: match.bookmakers.map(b => b.draw),
      away: match.bookmakers.map(b => b.away)
    }
    
    const stats = calculateOddsStats(aggregated)
    const impliedProbs = calculateImpliedProbabilities(stats.average)
    
    const bookmakerOdds = match.bookmakers.map(b => ({
      key: b.key,
      name: b.name,
      icon: b.icon,
      odds: { home: b.home, draw: b.draw, away: b.away }
    }))
    
    return {
      id: `demo_${index}`,
      sport_key: 'soccer_brazil_campeonato',
      sport_title: 'Brasileirão Série A',
      commence_time: new Date(Date.now() + (index + 1) * 86400000).toISOString(),
      home_team: match.home_team,
      away_team: match.away_team,
      bookmakers: bookmakerOdds,
      stats,
      implied_probabilities: impliedProbs,
      value_bets: findValueBets(bookmakerOdds, impliedProbs),
      best_odds: {
        home: { value: stats.best.home, bookmaker: bookmakerOdds.find(b => b.odds.home === stats.best.home) },
        draw: { value: stats.best.draw, bookmaker: bookmakerOdds.find(b => b.odds.draw === stats.best.draw) },
        away: { value: stats.best.away, bookmaker: bookmakerOdds.find(b => b.odds.away === stats.best.away) }
      }
    }
  })
}
