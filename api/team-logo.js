// Vercel Serverless Function - Proxy para logos de times via TheSportsDB
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=86400, stale-while-revalidate') // Cache 24h
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  const { team } = req.query
  
  if (!team) {
    return res.status(400).json({ error: 'Team name required' })
  }
  
  try {
    // TheSportsDB é gratuita e tem logos de todos os times
    const response = await fetch(
      `https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t=${encodeURIComponent(team)}`
    )
    
    if (!response.ok) {
      throw new Error('TheSportsDB API error')
    }
    
    const data = await response.json()
    
    if (data.teams && data.teams.length > 0) {
      // Retorna o badge (logo) do primeiro time encontrado
      return res.status(200).json({
        success: true,
        team: data.teams[0].strTeam,
        badge: data.teams[0].strBadge,
        logo: data.teams[0].strLogo,
        country: data.teams[0].strCountry,
        league: data.teams[0].strLeague
      })
    }
    
    // Time não encontrado
    return res.status(200).json({
      success: false,
      team: team,
      badge: null,
      message: 'Team not found'
    })
    
  } catch (error) {
    console.error('Error fetching team logo:', error)
    return res.status(500).json({ 
      error: 'Failed to fetch team logo',
      message: error.message 
    })
  }
}
