/**
 * 🎬 API de Replays de Gols
 * ODINENX v2.0
 * 
 * Endpoint: /api/goal-replays
 * Usa Scorebat API para buscar replays de gols
 */

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
  
  try {
    const { team, competition, limit = 10 } = req.query
    
    // Buscar vídeos
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
    
    // Formatar resposta
    const videos = (data.response || data)
      .slice(0, parseInt(limit))
      .map(video => ({
        id: video.matchviewUrl || video.title,
        title: video.title,
        competition: video.competition?.name || video.competition,
        competitionLogo: video.competition?.url,
        matchviewUrl: video.matchviewUrl,
        thumbnail: video.thumbnail,
        date: video.date,
        teams: {
          home: {
            name: video.side1?.name || video.team1,
            logo: video.side1?.url
          },
          away: {
            name: video.side2?.name || video.team2,
            logo: video.side2?.url
          }
        },
        videos: video.videos?.map(v => ({
          id: v.id,
          title: v.title,
          embed: v.embed
        })) || []
      }))
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      count: videos.length,
      disclaimer: 'Replays disponíveis com delay legal de 1-2 minutos após os gols',
      videos
    })
    
  } catch (error) {
    console.error('Goal Replays Error:', error)
    
    // Se não tiver token, retornar mock para desenvolvimento
    if (!SCOREBAT_TOKEN) {
      return res.status(200).json({
        success: true,
        timestamp: new Date().toISOString(),
        count: 0,
        disclaimer: 'API de replays não configurada (SCOREBAT_TOKEN não definido)',
        videos: [],
        mock: true
      })
    }
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch goal replays',
      message: error.message
    })
  }
}
