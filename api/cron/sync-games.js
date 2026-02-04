// Cron Job para Sincronização de Jogos - A cada 30 minutos
// Atualiza placares e status dos jogos do dia

import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL || 'https://mzamszcpbverpadjelck.supabase.co',
  process.env.SUPABASE_SERVICE_KEY || process.env.VITE_SUPABASE_ANON_KEY
)

// Football-Data.org API
const FOOTBALL_DATA_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
const FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'

// Ligas
const LIGAS = {
  'BSA': 'Brasileirão Série A',
  'PL': 'Premier League',
  'PD': 'La Liga',
  'SA': 'Serie A',
  'BL1': 'Bundesliga',
  'FL1': 'Ligue 1',
  'CL': 'Champions League'
}

const STATUS_MAP = {
  'SCHEDULED': 'scheduled',
  'TIMED': 'scheduled',
  'IN_PLAY': 'live',
  'PAUSED': 'halftime',
  'FINISHED': 'finished',
  'SUSPENDED': 'cancelled',
  'POSTPONED': 'cancelled',
  'CANCELLED': 'cancelled'
}

export default async function handler(req, res) {
  console.log('🏟️ Sincronizando jogos:', new Date().toISOString())
  
  const fixtures = []
  const today = new Date().toISOString().split('T')[0]
  
  try {
    // Buscar jogos de cada liga
    for (const [leagueCode, leagueName] of Object.entries(LIGAS)) {
      try {
        const response = await fetch(
          `${FOOTBALL_DATA_URL}/competitions/${leagueCode}/matches?dateFrom=${today}&dateTo=${today}`,
          { headers: { 'X-Auth-Token': FOOTBALL_DATA_KEY } }
        )
        
        if (response.status === 429) {
          console.log(`⚠️ Rate limit: ${leagueCode}`)
          await new Promise(r => setTimeout(r, 1000))
          continue
        }
        
        if (!response.ok) continue
        
        const data = await response.json()
        
        for (const match of data.matches || []) {
          const statusStr = match.status || 'SCHEDULED'
          
          let minute = 0
          if (statusStr === 'IN_PLAY') {
            const startTime = new Date(match.utcDate)
            minute = Math.max(0, Math.min(90, Math.floor((Date.now() - startTime) / 60000)))
          } else if (statusStr === 'PAUSED') {
            minute = 45
          }
          
          fixtures.push({
            fixture_id: match.id,
            home_team: match.homeTeam?.name,
            away_team: match.awayTeam?.name,
            home_team_logo: match.homeTeam?.crest || '',
            away_team_logo: match.awayTeam?.crest || '',
            home_score: match.score?.fullTime?.home || 0,
            away_score: match.score?.fullTime?.away || 0,
            minute,
            status: STATUS_MAP[statusStr] || 'scheduled',
            league: leagueName,
            league_logo: data.competition?.emblem || '',
            start_time: match.utcDate
          })
        }
        
        await new Promise(r => setTimeout(r, 400))
        
      } catch (e) {
        console.log(`❌ ${leagueCode}:`, e.message)
      }
    }
    
    console.log(`📊 ${fixtures.length} jogos encontrados`)
    
    // Upsert
    let created = 0, updated = 0
    
    for (const fixture of fixtures) {
      const { data: existing } = await supabase
        .from('game_rooms')
        .select('id')
        .eq('fixture_id', fixture.fixture_id)
        .single()
      
      if (existing) {
        await supabase
          .from('game_rooms')
          .update({
            home_score: fixture.home_score,
            away_score: fixture.away_score,
            minute: fixture.minute,
            status: fixture.status,
            updated_at: new Date().toISOString()
          })
          .eq('id', existing.id)
        updated++
      } else {
        await supabase.from('game_rooms').insert(fixture)
        created++
      }
    }
    
    console.log(`✅ Criados: ${created}, Atualizados: ${updated}`)
    
    return res.status(200).json({
      success: true,
      total: fixtures.length,
      created,
      updated,
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('❌ Erro:', error)
    return res.status(500).json({ success: false, error: error.message })
  }
}
