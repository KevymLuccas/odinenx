/**
 * 🏟️ API Unificada de Salas ao Vivo
 * ODINENX v2.0
 * 
 * Endpoint: /api/live
 * Actions: fixtures, events, replays, odds
 * 
 * Consolidação de APIs para respeitar limite Hobby (12 functions)
 */

const API_FOOTBALL_KEY = process.env.API_FOOTBALL_KEY
const API_FOOTBALL_URL = 'https://v3.football.api-sports.io'
const ODDS_API_KEY = process.env.ODDS_API_KEY
const ODDS_API_URL = 'https://api.the-odds-api.com/v4/sports'
const SCOREBAT_TOKEN = process.env.SCOREBAT_TOKEN
const SCOREBAT_URL = 'https://www.scorebat.com/video-api/v3'

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
  
  const { action } = req.query
  
  try {
    switch (action) {
      case 'fixtures':
        return await handleFixtures(req, res)
      case 'events':
        return await handleEvents(req, res)
      case 'replays':
        return await handleReplays(req, res)
      case 'odds':
        return await handleOdds(req, res)
      default:
        return res.status(400).json({
          success: false,
          error: 'Invalid action',
          validActions: ['fixtures', 'events', 'replays', 'odds']
        })
    }
  } catch (error) {
    console.error('Live API Error:', error)
    res.status(500).json({
      success: false,
      error: error.message
    })
  }
}

// ===== FIXTURES =====
async function handleFixtures(req, res) {
  const { league, date, live = 'all' } = req.query
  
  const params = new URLSearchParams()
  
  if (live === 'true') {
    params.append('live', 'all')
  } else if (date) {
    params.append('date', date)
  } else {
    params.append('date', new Date().toISOString().split('T')[0])
  }
  
  if (league) {
    params.append('league', league)
  }
  
  const response = await fetch(
    `${API_FOOTBALL_URL}/fixtures?${params.toString()}`,
    {
      headers: {
        'x-rapidapi-key': API_FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
      }
    }
  )
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  
  const data = await response.json()
  
  const fixtures = data.response?.map(match => ({
    id: match.fixture.id,
    date: match.fixture.date,
    timestamp: match.fixture.timestamp,
    venue: {
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
      logo: match.league.logo
    },
    teams: {
      home: {
        id: match.teams.home?.id,
        name: match.teams.home?.name,
        logo: match.teams.home?.logo
      },
      away: {
        id: match.teams.away?.id,
        name: match.teams.away?.name,
        logo: match.teams.away?.logo
      }
    },
    goals: {
      home: match.goals.home,
      away: match.goals.away
    }
  })) || []
  
  const liveFixtures = fixtures.filter(f => 
    ['1H', '2H', 'HT', 'ET', 'BT', 'P'].includes(f.status.short)
  )
  
  const scheduledFixtures = fixtures.filter(f => 
    ['NS', 'TBD'].includes(f.status.short)
  )
  
  return res.status(200).json({
    success: true,
    counts: {
      live: liveFixtures.length,
      scheduled: scheduledFixtures.length,
      total: fixtures.length
    },
    fixtures: {
      live: liveFixtures,
      scheduled: scheduledFixtures
    }
  })
}

// ===== EVENTS =====
async function handleEvents(req, res) {
  const { fixtureId } = req.query
  
  if (!fixtureId) {
    return res.status(400).json({
      success: false,
      error: 'fixtureId is required'
    })
  }
  
  const response = await fetch(
    `${API_FOOTBALL_URL}/fixtures/events?fixture=${fixtureId}`,
    {
      headers: {
        'x-rapidapi-key': API_FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
      }
    }
  )
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  
  const data = await response.json()
  
  const events = data.response?.map(event => ({
    time: {
      elapsed: event.time.elapsed,
      extra: event.time.extra
    },
    team: {
      id: event.team.id,
      name: event.team.name,
      logo: event.team.logo
    },
    player: {
      id: event.player?.id,
      name: event.player?.name
    },
    assist: {
      id: event.assist?.id,
      name: event.assist?.name
    },
    type: event.type,
    detail: event.detail
  })) || []
  
  return res.status(200).json({
    success: true,
    fixtureId,
    count: events.length,
    events
  })
}

// ===== REPLAYS =====
async function handleReplays(req, res) {
  const { team, competition, limit = 10 } = req.query
  
  let url = `${SCOREBAT_URL}/feed/?token=${SCOREBAT_TOKEN}`
  
  if (team) {
    url = `${SCOREBAT_URL}/team/${encodeURIComponent(team)}/?token=${SCOREBAT_TOKEN}`
  } else if (competition) {
    url = `${SCOREBAT_URL}/competition/${encodeURIComponent(competition)}/?token=${SCOREBAT_TOKEN}`
  }
  
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  
  const data = await response.json()
  
  const videos = (data.response || data)
    .slice(0, parseInt(limit))
    .map(video => ({
      id: video.matchviewUrl || video.title,
      title: video.title,
      competition: video.competition?.name || video.competition,
      competitionUrl: video.competition?.url,
      matchviewUrl: video.matchviewUrl,
      thumbnail: video.thumbnail,
      date: video.date,
      videos: video.videos?.map(v => ({
        title: v.title,
        embed: v.embed
      })) || []
    }))
  
  return res.status(200).json({
    success: true,
    count: videos.length,
    videos
  })
}

// ===== ODDS =====
async function handleOdds(req, res) {
  const { fixtureId, sport = 'soccer_brazil_campeonato' } = req.query
  
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
  
  let odds = data
  if (fixtureId) {
    odds = data.filter(match => match.id === fixtureId)
  }
  
  const formattedOdds = odds.slice(0, 20).map(match => ({
    id: match.id,
    sport: match.sport_key,
    homeTeam: match.home_team,
    awayTeam: match.away_team,
    commenceTime: match.commence_time,
    bookmakers: match.bookmakers?.slice(0, 5).map(book => ({
      key: book.key,
      title: book.title,
      markets: book.markets?.map(market => ({
        key: market.key,
        outcomes: market.outcomes
      }))
    }))
  }))
  
  return res.status(200).json({
    success: true,
    count: formattedOdds.length,
    odds: formattedOdds
  })
}
