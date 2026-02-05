/**
 * 🔴 API Proxy para Jogos Ao Vivo
 * Usa API-Football (api-sports.io) - Mais confiável para live
 * Registre-se em: https://dashboard.api-football.com/register
 * Plano Free: 100 requests/dia
 */

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  // ⚠️ IMPORTANTE: Substitua pela sua chave da API-Football
  // Registre-se em: https://dashboard.api-football.com/register
  const API_KEY = process.env.API_FOOTBALL_KEY || 'YOUR_API_KEY_HERE'
  
  try {
    let games = []
    
    // Buscar jogos AO VIVO da API-Football
    const liveResponse = await fetch(
      'https://v3.football.api-sports.io/fixtures?live=all',
      { 
        headers: { 
          'x-apisports-key': API_KEY
        } 
      }
    )
    
    if (liveResponse.ok) {
      const liveData = await liveResponse.json()
      
      if (liveData.response && liveData.response.length > 0) {
        games = liveData.response.map(match => ({
          id: match.fixture.id,
          home_team: match.teams.home.name,
          away_team: match.teams.away.name,
          home_logo: match.teams.home.logo,
          away_logo: match.teams.away.logo,
          home_score: match.goals.home,
          away_score: match.goals.away,
          status: mapStatus(match.fixture.status.short),
          match_date: match.fixture.date,
          league: match.league.country,
          league_name: match.league.name,
          league_flag: match.league.flag || '⚽',
          league_logo: match.league.logo,
          minute: match.fixture.status.elapsed,
          venue: match.fixture.venue?.name || null
        }))
      }
    }
    
    // Se não houver jogos ao vivo, buscar jogos de hoje
    if (games.length === 0) {
      const today = new Date().toISOString().split('T')[0]
      const todayResponse = await fetch(
        `https://v3.football.api-sports.io/fixtures?date=${today}`,
        { 
          headers: { 
            'x-apisports-key': API_KEY
          } 
        }
      )
      
      if (todayResponse.ok) {
        const todayData = await todayResponse.json()
        
        if (todayData.response && todayData.response.length > 0) {
          games = todayData.response.slice(0, 50).map(match => ({
            id: match.fixture.id,
            home_team: match.teams.home.name,
            away_team: match.teams.away.name,
            home_logo: match.teams.home.logo,
            away_logo: match.teams.away.logo,
            home_score: match.goals.home,
            away_score: match.goals.away,
            status: mapStatus(match.fixture.status.short),
            match_date: match.fixture.date,
            league: match.league.country,
            league_name: match.league.name,
            league_flag: match.league.flag || '⚽',
            league_logo: match.league.logo,
            minute: match.fixture.status.elapsed,
            venue: match.fixture.venue?.name || null
          }))
        }
      }
    }
    
    // Ordenar: ao vivo primeiro, depois por horário
    games.sort((a, b) => {
      if (a.status === 'live' && b.status !== 'live') return -1
      if (b.status === 'live' && a.status !== 'live') return 1
      if (a.status === 'halftime' && b.status !== 'halftime') return -1
      if (b.status === 'halftime' && a.status !== 'halftime') return 1
      return new Date(a.match_date) - new Date(b.match_date)
    })
    
    const liveCount = games.filter(g => g.status === 'live' || g.status === 'halftime').length
    
    return res.status(200).json({
      success: true,
      count: games.length,
      live_count: liveCount,
      timestamp: new Date().toISOString(),
      games: games
    })
    
  } catch (error) {
    console.error('API Error:', error)
    
    return res.status(200).json({
      success: false,
      error: error.message,
      count: 0,
      live_count: 0,
      games: [],
      message: 'Não foi possível carregar os jogos. Configure sua chave API.'
    })
  }
}

function mapStatus(status) {
  const statusMap = {
    // Em Jogo
    '1H': 'live',
    '2H': 'live',
    'HT': 'halftime',
    'ET': 'live',
    'BT': 'halftime',
    'P': 'live',
    'LIVE': 'live',
    // Finalizado
    'FT': 'finished',
    'AET': 'finished',
    'PEN': 'finished',
    // Agendado
    'TBD': 'scheduled',
    'NS': 'scheduled',
    // Outros
    'PST': 'postponed',
    'CANC': 'cancelled',
    'ABD': 'cancelled',
    'SUSP': 'suspended',
    'INT': 'interrupted',
    'AWD': 'finished',
    'WO': 'finished'
  }
  return statusMap[status] || 'scheduled'
}
