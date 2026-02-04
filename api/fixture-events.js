/**
 * 📢 API de Eventos do Jogo
 * ODINENX v2.0
 * 
 * Endpoint: /api/fixture-events
 * Retorna eventos (gols, cartões, substituições) de um jogo
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
    const { fixtureId } = req.query
    
    if (!fixtureId) {
      return res.status(400).json({
        success: false,
        error: 'fixtureId is required'
      })
    }
    
    // Buscar eventos do jogo
    const response = await fetch(
      `${API_URL}/fixtures/events?fixture=${fixtureId}`,
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
    
    // Formatar eventos
    const events = data.response?.map(event => ({
      time: {
        elapsed: event.time.elapsed,
        extra: event.time.extra
      },
      team: {
        id: event.team?.id,
        name: event.team?.name,
        logo: event.team?.logo
      },
      player: {
        id: event.player?.id,
        name: event.player?.name
      },
      assist: event.assist?.id ? {
        id: event.assist.id,
        name: event.assist.name
      } : null,
      type: event.type, // Goal, Card, Subst, Var
      detail: event.detail, // Normal Goal, Yellow Card, etc
      comments: event.comments
    })) || []
    
    // Separar por tipo
    const goals = events.filter(e => e.type === 'Goal')
    const cards = events.filter(e => e.type === 'Card')
    const substitutions = events.filter(e => e.type === 'subst')
    const varEvents = events.filter(e => e.type === 'Var')
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      fixtureId: parseInt(fixtureId),
      counts: {
        goals: goals.length,
        cards: cards.length,
        substitutions: substitutions.length,
        var: varEvents.length,
        total: events.length
      },
      events: {
        all: events,
        goals,
        cards,
        substitutions,
        var: varEvents
      }
    })
    
  } catch (error) {
    console.error('Fixture Events Error:', error)
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch fixture events',
      message: error.message
    })
  }
}
