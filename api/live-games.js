/**
 * 🔴 API Proxy para Football-Data.org
 * Resolve problema de CORS
 */

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  const FOOTBALL_API_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
  
  try {
    // Buscar jogos de hoje até próxima semana
    const today = new Date().toISOString().split('T')[0]
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    
    const response = await fetch(
      `https://api.football-data.org/v4/matches?dateFrom=${today}&dateTo=${nextWeek}`,
      {
        headers: {
          'X-Auth-Token': FOOTBALL_API_KEY
        }
      }
    )
    
    if (!response.ok) {
      throw new Error(`Football API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Mapear para formato simplificado
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
      'PPL': { name: 'Primeira Liga', flag: '🇵🇹' }
    }
    
    const statusMap = {
      'IN_PLAY': 'live',
      'PAUSED': 'halftime',
      'FINISHED': 'finished',
      'SCHEDULED': 'scheduled',
      'TIMED': 'scheduled',
      'POSTPONED': 'postponed',
      'CANCELLED': 'cancelled'
    }
    
    const games = (data.matches || []).map(match => ({
      id: match.id,
      home_team: match.homeTeam.shortName || match.homeTeam.name,
      away_team: match.awayTeam.shortName || match.awayTeam.name,
      home_logo: match.homeTeam.crest,
      away_logo: match.awayTeam.crest,
      home_score: match.score?.fullTime?.home ?? (match.score?.halfTime?.home ?? null),
      away_score: match.score?.fullTime?.away ?? (match.score?.halfTime?.away ?? null),
      status: statusMap[match.status] || 'scheduled',
      match_date: match.utcDate,
      league: match.competition.code,
      league_name: LEAGUES[match.competition.code]?.name || match.competition.name,
      league_flag: LEAGUES[match.competition.code]?.flag || '⚽',
      minute: match.minute || null
    }))
    
    return res.status(200).json({
      success: true,
      count: games.length,
      games
    })
    
  } catch (error) {
    console.error('Football API Error:', error)
    return res.status(500).json({
      success: false,
      error: error.message
    })
  }
}
