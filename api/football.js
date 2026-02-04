// Vercel Serverless Function - Proxy para Football-Data.org
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  const { competition, status, type } = req.query
  
  if (!competition) {
    return res.status(400).json({ error: 'Competition code required' })
  }
  
  const API_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
  
  try {
    // Se pediu standings
    if (type === 'standings') {
      const standingsUrl = `https://api.football-data.org/v4/competitions/${competition}/standings`
      const response = await fetch(standingsUrl, {
        headers: { 'X-Auth-Token': API_KEY }
      })
      
      if (!response.ok) {
        return res.status(200).json({ standings: [] }) // Retorna vazio se não tiver
      }
      
      const data = await response.json()
      return res.status(200).json(data)
    }
    
    // Buscar partidas
    const matchesUrl = `https://api.football-data.org/v4/competitions/${competition}/matches${status ? `?status=${status}` : ''}`
    const matchesResponse = await fetch(matchesUrl, {
      headers: { 'X-Auth-Token': API_KEY }
    })
    
    if (!matchesResponse.ok) {
      const error = await matchesResponse.json().catch(() => ({}))
      return res.status(matchesResponse.status).json(error)
    }
    
    const matchesData = await matchesResponse.json()
    
    // Tentar buscar standings para enriquecer os dados
    try {
      const standingsUrl = `https://api.football-data.org/v4/competitions/${competition}/standings`
      const standingsResponse = await fetch(standingsUrl, {
        headers: { 'X-Auth-Token': API_KEY }
      })
      
      if (standingsResponse.ok) {
        const standingsData = await standingsResponse.json()
        
        // Criar mapa de posições por time ID
        const positionMap = {}
        if (standingsData.standings) {
          for (const standing of standingsData.standings) {
            if (standing.table) {
              for (const team of standing.table) {
                positionMap[team.team.id] = {
                  position: team.position,
                  points: team.points,
                  playedGames: team.playedGames,
                  won: team.won,
                  draw: team.draw,
                  lost: team.lost,
                  goalsFor: team.goalsFor,
                  goalsAgainst: team.goalsAgainst,
                  goalDifference: team.goalDifference,
                  form: team.form // últimos 5 jogos
                }
              }
            }
          }
        }
        
        // Enriquecer matches com posições
        if (matchesData.matches) {
          matchesData.matches = matchesData.matches.map(match => ({
            ...match,
            homeTeam: {
              ...match.homeTeam,
              ...positionMap[match.homeTeam.id]
            },
            awayTeam: {
              ...match.awayTeam,
              ...positionMap[match.awayTeam.id]
            }
          }))
        }
      }
    } catch (standingsError) {
      // Se falhar standings, continua sem eles
      console.log('Standings not available for', competition)
    }
    
    return res.status(200).json(matchesData)
    
  } catch (error) {
    return res.status(500).json({ error: error.message })
  }
}
