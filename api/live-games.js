/**
 * 🔴 API Proxy para Jogos Ao Vivo
 * Usa API-Football (api-sports.io) - Mais robusta para live
 */

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  // API-Football key (api-sports.io) - Gratuita: 100 req/dia
  const API_FOOTBALL_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
  
  try {
    const { type = 'today' } = req.query
    
    let games = []
    
    // Buscar jogos AO VIVO primeiro
    const liveResponse = await fetch(
      'https://api.football-data.org/v4/matches?status=LIVE,IN_PLAY,PAUSED',
      { headers: { 'X-Auth-Token': API_FOOTBALL_KEY } }
    )
    
    if (liveResponse.ok) {
      const liveData = await liveResponse.json()
      games = [...(liveData.matches || [])]
    }
    
    // Também buscar jogos de HOJE (agendados e finalizados)
    const today = new Date().toISOString().split('T')[0]
    const todayResponse = await fetch(
      `https://api.football-data.org/v4/matches?dateFrom=${today}&dateTo=${today}`,
      { headers: { 'X-Auth-Token': API_FOOTBALL_KEY } }
    )
    
    if (todayResponse.ok) {
      const todayData = await todayResponse.json()
      // Adicionar jogos de hoje que não estão na lista de live
      const liveIds = new Set(games.map(g => g.id))
      const todayGames = (todayData.matches || []).filter(m => !liveIds.has(m.id))
      games = [...games, ...todayGames]
    }
    
    // Mapear para formato padronizado
    const LEAGUES = {
      'BSA': { name: 'Brasileirão Série A', flag: '🇧🇷' },
      'PL': { name: 'Premier League', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
      'PD': { name: 'La Liga', flag: '🇪🇸' },
      'SA': { name: 'Serie A', flag: '🇮🇹' },
      'BL1': { name: 'Bundesliga', flag: '🇩🇪' },
      'FL1': { name: 'Ligue 1', flag: '🇫🇷' },
      'CL': { name: 'Champions League', flag: '🇪🇺' },
      'ELC': { name: 'Championship', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
      'DED': { name: 'Eredivisie', flag: '🇳🇱' },
      'PPL': { name: 'Primeira Liga', flag: '🇵🇹' },
      'EC': { name: 'Copa do Brasil', flag: '🇧🇷' },
      'CLI': { name: 'Libertadores', flag: '🌎' }
    }
    
    const statusMap = {
      'IN_PLAY': 'live',
      'LIVE': 'live',
      'PAUSED': 'halftime',
      'HALFTIME': 'halftime',
      'FINISHED': 'finished',
      'SCHEDULED': 'scheduled',
      'TIMED': 'scheduled',
      'POSTPONED': 'postponed',
      'CANCELLED': 'cancelled'
    }
    
    const formattedGames = games.map(match => ({
      id: match.id,
      home_team: match.homeTeam?.shortName || match.homeTeam?.name || 'Time Casa',
      away_team: match.awayTeam?.shortName || match.awayTeam?.name || 'Time Fora',
      home_logo: match.homeTeam?.crest || null,
      away_logo: match.awayTeam?.crest || null,
      home_score: match.score?.fullTime?.home ?? match.score?.halfTime?.home ?? null,
      away_score: match.score?.fullTime?.away ?? match.score?.halfTime?.away ?? null,
      status: statusMap[match.status] || 'scheduled',
      match_date: match.utcDate,
      league: match.competition?.code || 'OTHER',
      league_name: LEAGUES[match.competition?.code]?.name || match.competition?.name || 'Liga',
      league_flag: LEAGUES[match.competition?.code]?.flag || '⚽',
      minute: match.minute || null,
      matchday: match.matchday || null
    }))
    
    // Ordenar: ao vivo primeiro, depois por horário
    formattedGames.sort((a, b) => {
      if (a.status === 'live' && b.status !== 'live') return -1
      if (b.status === 'live' && a.status !== 'live') return 1
      if (a.status === 'halftime' && b.status !== 'halftime') return -1
      if (b.status === 'halftime' && a.status !== 'halftime') return 1
      return new Date(a.match_date) - new Date(b.match_date)
    })
    
    return res.status(200).json({
      success: true,
      count: formattedGames.length,
      live_count: formattedGames.filter(g => g.status === 'live' || g.status === 'halftime').length,
      timestamp: new Date().toISOString(),
      games: formattedGames
    })
    
  } catch (error) {
    console.error('API Error:', error)
    
    // Retornar dados de fallback para não quebrar a UI
    return res.status(200).json({
      success: false,
      error: error.message,
      count: 0,
      games: [],
      message: 'Não foi possível carregar os jogos. Tente novamente em alguns segundos.'
    })
  }
}
