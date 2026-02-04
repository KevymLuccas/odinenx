/**
 * ⚽ API de Jogos ao Vivo
 * ODINENX v2.0
 * 
 * Endpoint: /api/live-fixtures
 * Usa API Football para buscar jogos ao vivo
 */

const API_KEY = process.env.API_FOOTBALL_KEY
const API_URL = 'https://v3.football.api-sports.io'

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
    const { league, date, live = 'all' } = req.query
    
    // Construir query
    const params = new URLSearchParams()
    
    if (live === 'true') {
      params.append('live', 'all')
    } else if (date) {
      params.append('date', date)
    } else {
      // Hoje por padrão
      params.append('date', new Date().toISOString().split('T')[0])
    }
    
    if (league) {
      params.append('league', league)
    }
    
    const response = await fetch(
      `${API_URL}/fixtures?${params.toString()}`,
      {
        headers: {
          'x-rapidapi-key': API_KEY,
          'x-rapidapi-host': 'v3.football.api-sports.io'
        }
      }
    )
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Formatar resposta
    const fixtures = data.response?.map(match => ({
      id: match.fixture.id,
      referee: match.fixture.referee,
      timezone: match.fixture.timezone,
      date: match.fixture.date,
      timestamp: match.fixture.timestamp,
      venue: {
        id: match.fixture.venue?.id,
        name: match.fixture.venue?.name,
        city: match.fixture.venue?.city
      },
      status: {
        short: match.fixture.status?.short,
        long: match.fixture.status?.long,
        elapsed: match.fixture.status?.elapsed
      },
      league: {
        id: match.league.id,
        name: match.league.name,
        country: match.league.country,
        logo: match.league.logo,
        round: match.league.round
      },
      teams: {
        home: {
          id: match.teams.home?.id,
          name: match.teams.home?.name,
          logo: match.teams.home?.logo,
          winner: match.teams.home?.winner
        },
        away: {
          id: match.teams.away?.id,
          name: match.teams.away?.name,
          logo: match.teams.away?.logo,
          winner: match.teams.away?.winner
        }
      },
      goals: {
        home: match.goals.home,
        away: match.goals.away
      },
      score: {
        halftime: match.score.halftime,
        fulltime: match.score.fulltime,
        extratime: match.score.extratime,
        penalty: match.score.penalty
      },
      events: match.events?.map(event => ({
        time: event.time,
        team: event.team,
        player: event.player,
        assist: event.assist,
        type: event.type,
        detail: event.detail
      })) || []
    })) || []
    
    // Separar por status
    const liveFixtures = fixtures.filter(f => 
      ['1H', '2H', 'HT', 'ET', 'BT', 'P'].includes(f.status.short)
    )
    
    const scheduledFixtures = fixtures.filter(f => 
      ['NS', 'TBD'].includes(f.status.short)
    )
    
    const finishedFixtures = fixtures.filter(f => 
      ['FT', 'AET', 'PEN'].includes(f.status.short)
    )
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      counts: {
        live: liveFixtures.length,
        scheduled: scheduledFixtures.length,
        finished: finishedFixtures.length,
        total: fixtures.length
      },
      fixtures: {
        live: liveFixtures,
        scheduled: scheduledFixtures,
        finished: finishedFixtures
      }
    })
    
  } catch (error) {
    console.error('Live Fixtures Error:', error)
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch live fixtures',
      message: error.message
    })
  }
}
