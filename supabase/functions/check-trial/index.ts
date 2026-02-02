import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    // Executar verificação de expiração de trials
    const { error: updateError } = await supabaseClient
      .rpc('check_trial_expiration')

    if (updateError) {
      console.error('Erro ao verificar trials:', updateError)
      return new Response(
        JSON.stringify({ error: 'Erro ao verificar trials' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Buscar estatísticas dos trials
    const { data: stats, error: statsError } = await supabaseClient
      .from('profiles')
      .select('trial_expired, trial_used_days, trial_start')
      .not('trial_start', 'is', null)

    if (statsError) {
      console.error('Erro ao buscar estatísticas:', statsError)
    }

    const totalUsers = stats?.length || 0
    const expiredUsers = stats?.filter(s => s.trial_expired).length || 0
    const activeTrials = totalUsers - expiredUsers

    console.log(`✅ Trial check completed:`)
    console.log(`   📊 Total users: ${totalUsers}`)
    console.log(`   ⏰ Active trials: ${activeTrials}`)
    console.log(`   🔒 Expired trials: ${expiredUsers}`)

    return new Response(
      JSON.stringify({ 
        success: true,
        message: 'Trial expiration check completed',
        stats: {
          totalUsers,
          activeTrials,
          expiredUsers,
          timestamp: new Date().toISOString()
        }
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Unexpected error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})