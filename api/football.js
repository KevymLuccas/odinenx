// Vercel Serverless Function - Proxy para Football-Data.org
// Com cache em memória para evitar rate limiting (429)

// Cache em memória (persiste entre requisições na mesma instância)
const cache = new Map()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutos

function getCachedData(key) {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data
  }
  cache.delete(key)
  return null
}

function setCachedData(key, data) {
  // Limitar tamanho do cache (máximo 50 entradas)
  if (cache.size >= 50) {
    const firstKey = cache.keys().next().value
    cache.delete(firstKey)
  }
  cache.set(key, { data, timestamp: Date.now() })
}

export default async function handler(req, res) {
  // CORS headers + Cache headers para CDN
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600') // Cache CDN 5min
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  const { competition, status, type } = req.query
  
  if (!competition) {
    return res.status(400).json({ error: 'Competition code required' })
  }
  
  const cacheKey = `${competition}-${status || 'all'}-${type || 'matches'}`
  
  // Verificar cache primeiro
  const cachedResponse = getCachedData(cacheKey)
  if (cachedResponse) {
    return res.status(200).json(cachedResponse)
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
        return res.status(200).json({ standings: [] })
      }
      
      const data = await response.json()
      setCachedData(cacheKey, data)
      return res.status(200).json(data)
    }
    
    // Buscar partidas
    const matchesUrl = `https://api.football-data.org/v4/competitions/${competition}/matches${status ? `?status=${status}` : ''}`
    const matchesResponse = await fetch(matchesUrl, {
      headers: { 'X-Auth-Token': API_KEY }
    })
    
    if (!matchesResponse.ok) {
      // Se for 429, retornar dados vazios em vez de erro
      if (matchesResponse.status === 429) {
        console.log('Rate limited for', competition)
        return res.status(200).json({ 
          matches: [], 
          competition: { name: competition },
          rateLimited: true 
        })
      }
      const error = await matchesResponse.json().catch(() => ({}))
      return res.status(matchesResponse.status).json(error)
    }
    
    const matchesData = await matchesResponse.json()
    
    // Tentar buscar standings para enriquecer os dados (apenas se não tivermos cache)
    const standingsCacheKey = `${competition}-standings`
    let positionMap = getCachedData(standingsCacheKey)
    
    if (!positionMap) {
      try {
        const standingsUrl = `https://api.football-data.org/v4/competitions/${competition}/standings`
        const standingsResponse = await fetch(standingsUrl, {
          headers: { 'X-Auth-Token': API_KEY }
        })
        
        if (standingsResponse.ok) {
          const standingsData = await standingsResponse.json()
          
          positionMap = {}
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
                    form: team.form
                  }
                }
              }
            }
          }
          setCachedData(standingsCacheKey, positionMap)
        }
      } catch (standingsError) {
        console.log('Standings not available for', competition)
      }
    }
    
    // Enriquecer matches com posições se tivermos
    if (positionMap && matchesData.matches) {
      matchesData.matches = matchesData.matches.map(match => ({
        ...match,
        homeTeam: {
          ...match.homeTeam,
          ...(positionMap[match.homeTeam?.id] || {})
        },
        awayTeam: {
          ...match.awayTeam,
          ...(positionMap[match.awayTeam?.id] || {})
        }
      }))
    }
    
    // Cachear resultado final
    setCachedData(cacheKey, matchesData)
    
    return res.status(200).json(matchesData)
    
  } catch (error) {
    return res.status(500).json({ error: error.message })
  }
}
