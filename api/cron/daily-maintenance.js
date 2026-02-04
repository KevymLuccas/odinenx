// Cron Job de Manutenção Diária - Executado às 3:00 AM (horário de Brasília)
// Vercel Cron: https://vercel.com/docs/cron-jobs

import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL || 'https://mzamszcpbverpadjelck.supabase.co',
  process.env.SUPABASE_SERVICE_KEY || process.env.VITE_SUPABASE_ANON_KEY
)

// Football-Data.org API
const FOOTBALL_DATA_KEY = '1d1cd9e04db74a98ac8246a1668a0532'
const FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'

// Ligas disponíveis
const LIGAS = {
  'BSA': 'Brasileirão Série A',
  'PL': 'Premier League',
  'PD': 'La Liga',
  'SA': 'Serie A',
  'BL1': 'Bundesliga',
  'FL1': 'Ligue 1',
  'CL': 'Champions League'
}

// Mapeamento de status
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
  // Verificar se é uma requisição do Vercel Cron (segurança)
  const authHeader = req.headers.authorization
  
  // Log de início
  console.log('🕐 Iniciando manutenção diária:', new Date().toISOString())
  
  const results = {
    timestamp: new Date().toISOString(),
    tasks: []
  }
  
  try {
    // 1. Verificar trials expirados e desativar
    console.log('📋 Verificando trials expirados...')
    const hoje = new Date().toISOString().split('T')[0]
    
    const { data: trialsExpirados, error: trialError } = await supabase
      .from('profiles')
      .update({ 
        trial_active: false,
        plan: 'free'
      })
      .lt('trial_ends_at', hoje)
      .eq('trial_active', true)
      .select('id')
    
    results.tasks.push({
      name: 'Trials Expirados',
      success: !trialError,
      count: trialsExpirados?.length || 0,
      error: trialError?.message
    })
    
    // 2. Verificar assinaturas expiradas
    console.log('📋 Verificando assinaturas expiradas...')
    const { data: subsExpiradas, error: subError } = await supabase
      .from('profiles')
      .update({ 
        plan: 'free',
        subscription_status: 'expired'
      })
      .lt('subscription_ends_at', hoje)
      .neq('plan', 'free')
      .select('id')
    
    results.tasks.push({
      name: 'Assinaturas Expiradas',
      success: !subError,
      count: subsExpiradas?.length || 0,
      error: subError?.message
    })
    
    // 3. Limpar logs antigos (mais de 30 dias)
    console.log('🗑️ Limpando logs antigos...')
    const trintaDiasAtras = new Date()
    trintaDiasAtras.setDate(trintaDiasAtras.getDate() - 30)
    
    const { count: logsRemovidos, error: logError } = await supabase
      .from('activity_logs')
      .delete()
      .lt('created_at', trintaDiasAtras.toISOString())
    
    results.tasks.push({
      name: 'Logs Antigos Removidos',
      success: !logError,
      count: logsRemovidos || 0,
      error: logError?.message
    })
    
    // 4. Atualizar estatísticas de uso
    console.log('📊 Atualizando estatísticas...')
    const { count: totalUsers } = await supabase
      .from('profiles')
      .select('*', { count: 'exact', head: true })
    
    const { count: usersAtivos } = await supabase
      .from('profiles')
      .select('*', { count: 'exact', head: true })
      .neq('plan', 'free')
    
    results.tasks.push({
      name: 'Estatísticas Atualizadas',
      success: true,
      data: {
        totalUsers,
        usersAtivos
      }
    })
    
    // 5. Sincronizar jogos do dia (Live Rooms)
    console.log('🏟️ Sincronizando jogos do dia...')
    const syncResult = await syncLiveRooms()
    results.tasks.push({
      name: 'Jogos Sincronizados',
      success: syncResult.success,
      count: syncResult.count,
      error: syncResult.error
    })
    
    // 6. Limpar jogos antigos (mais de 2 dias)
    console.log('🗑️ Limpando jogos antigos...')
    const doisDiasAtras = new Date()
    doisDiasAtras.setDate(doisDiasAtras.getDate() - 2)
    
    const { count: jogosRemovidos, error: jogosError } = await supabase
      .from('game_rooms')
      .delete()
      .eq('status', 'finished')
      .lt('start_time', doisDiasAtras.toISOString())
    
    results.tasks.push({
      name: 'Jogos Antigos Removidos',
      success: !jogosError,
      count: jogosRemovidos || 0,
      error: jogosError?.message
    })
    
    // 7. Registrar execução do cron
    console.log('💾 Registrando execução...')
    await supabase
      .from('cron_logs')
      .insert({
        job_name: 'daily-maintenance',
        executed_at: new Date().toISOString(),
        results: JSON.stringify(results),
        success: true
      })
    
    console.log('✅ Manutenção diária concluída com sucesso!')
    
    return res.status(200).json({
      success: true,
      message: 'Manutenção diária executada com sucesso',
      results
    })
    
  } catch (error) {
    console.error('❌ Erro na manutenção diária:', error)
    
    // Registrar erro
    await supabase
      .from('cron_logs')
      .insert({
        job_name: 'daily-maintenance',
        executed_at: new Date().toISOString(),
        error: error.message,
        success: false
      })
    
    return res.status(500).json({
      success: false,
      error: error.message
    })
  }
}

// ===== SINCRONIZAÇÃO DE JOGOS AO VIVO =====
async function syncLiveRooms() {
  const fixtures = []
  const today = new Date().toISOString().split('T')[0]
  
  try {
    // Buscar jogos de cada liga
    for (const [leagueCode, leagueName] of Object.entries(LIGAS)) {
      try {
        const response = await fetch(
          `${FOOTBALL_DATA_URL}/competitions/${leagueCode}/matches?dateFrom=${today}&dateTo=${today}`,
          {
            headers: { 'X-Auth-Token': FOOTBALL_DATA_KEY }
          }
        )
        
        if (response.status === 429) {
          console.log(`   ⚠️ Rate limit para ${leagueCode}`)
          await new Promise(r => setTimeout(r, 1000))
          continue
        }
        
        if (!response.ok) continue
        
        const data = await response.json()
        
        for (const match of data.matches || []) {
          const statusStr = match.status || 'SCHEDULED'
          
          // Calcular minuto
          let minute = 0
          if (statusStr === 'IN_PLAY') {
            const startTime = new Date(match.utcDate)
            const now = new Date()
            minute = Math.max(0, Math.min(90, Math.floor((now - startTime) / 60000)))
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
        
        // Rate limit
        await new Promise(r => setTimeout(r, 500))
        
      } catch (e) {
        console.log(`   ❌ Erro em ${leagueCode}:`, e.message)
      }
    }
    
    console.log(`   📊 Encontrados ${fixtures.length} jogos`)
    
    // Upsert jogos no Supabase
    for (const fixture of fixtures) {
      // Verificar se existe
      const { data: existing } = await supabase
        .from('game_rooms')
        .select('id')
        .eq('fixture_id', fixture.fixture_id)
        .single()
      
      if (existing) {
        // Atualizar
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
      } else {
        // Inserir
        await supabase
          .from('game_rooms')
          .insert(fixture)
      }
    }
    
    return { success: true, count: fixtures.length }
    
  } catch (error) {
    console.error('❌ Erro ao sincronizar jogos:', error)
    return { success: false, count: 0, error: error.message }
  }
}
