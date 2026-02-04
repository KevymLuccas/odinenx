/**
 * 📊 API de Odds em Tempo Real
 * ODINENX v2.0
 * 
 * Endpoint: /api/live-odds
 */

const ODDS_API_KEY = process.env.ODDS_API_KEY
const ODDS_API_URL = 'https://api.the-odds-api.com/v4/sports'

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }
  
  try {
    const { fixtureId, sport = 'soccer_brazil_campeonato' } = req.query
    
    // Buscar odds ao vivo
    const response = await fetch(
      `${ODDS_API_URL}/${sport}/odds/?` + new URLSearchParams({
        apiKey: ODDS_API_KEY,
        regions: 'br,eu',
        markets: 'h2h,spreads,totals',
        oddsFormat: 'decimal'
      })
    )
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Se tiver fixtureId, filtrar
    let odds = data
    if (fixtureId) {
      odds = data.filter(match => match.id === fixtureId)
    }
    
    // Formatar resposta
    const formattedOdds = odds.map(match => ({
      id: match.id,
      sport: match.sport_key,
      homeTeam: match.home_team,
      awayTeam: match.away_team,
      startTime: match.commence_time,
      bookmakers: match.bookmakers?.map(bm => ({
        name: bm.title,
        markets: bm.markets?.map(market => ({
          type: market.key,
          lastUpdate: market.last_update,
          outcomes: market.outcomes?.map(outcome => ({
            name: outcome.name,
            price: outcome.price,
            point: outcome.point // para spreads/totals
          }))
        }))
      })) || []
    }))
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      count: formattedOdds.length,
      odds: formattedOdds
    })
    
  } catch (error) {
    console.error('Live Odds Error:', error)
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch live odds',
      message: error.message
    })
  }
}
