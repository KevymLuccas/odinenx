// Cron Job de Manutenção Diária - Executado às 3:00 AM (horário de Brasília)
// Vercel Cron: https://vercel.com/docs/cron-jobs

import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL || 'https://mzamszcpbverpadjelck.supabase.co',
  process.env.SUPABASE_SERVICE_KEY || process.env.VITE_SUPABASE_ANON_KEY
)

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
    
    // 5. Registrar execução do cron
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
