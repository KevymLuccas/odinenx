import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://mzamszcpbverpadjelck.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTA5NjIsImV4cCI6MjA4NTM2Njk2Mn0.I8uUlJxgm2UgyavzRA6ATcaoV3SRVd9Z-NgeENzzUN4'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function checkDatabaseStructure() {
  try {
    console.log('📊 Verificando todas as tabelas...')
    
    // Tentar buscar profiles existentes
    const { data: profiles, error: profilesError } = await supabase
      .from('profiles')
      .select('*')
      .limit(5)
    
    console.log('👥 Profiles encontrados:', profiles?.length || 0)
    if (profiles && profiles.length > 0) {
      console.log('📋 Colunas na tabela profiles:', Object.keys(profiles[0]))
      console.log('🔍 Exemplo de profile:', profiles[0])
    } else if (profilesError) {
      console.log('❌ Erro ao buscar profiles:', profilesError.message)
    }
    
    // Tentar buscar subscriptions
    const { data: subscriptions } = await supabase
      .from('subscriptions')
      .select('*')
      .limit(3)
    
    console.log('💳 Subscriptions encontradas:', subscriptions?.length || 0)
    if (subscriptions && subscriptions.length > 0) {
      console.log('📋 Colunas na tabela subscriptions:', Object.keys(subscriptions[0]))
    }
    
    // Tentar buscar paper_trades
    const { data: paperTrades } = await supabase
      .from('paper_trades')
      .select('*')
      .limit(3)
    
    console.log('📈 Paper trades encontradas:', paperTrades?.length || 0)
    
    // Tentar buscar alerts
    const { data: alerts } = await supabase
      .from('alerts')
      .select('*')
      .limit(3)
    
    console.log('🔔 Alerts encontrados:', alerts?.length || 0)
    
    // Tentar criar um profile simples primeiro
    console.log('🔧 Tentando criar profile básico...')
    
    const { data: newProfile, error: createError } = await supabase
      .from('profiles')
      .insert({
        id: crypto.randomUUID(),
        email: 'test@example.com',
        created_at: new Date().toISOString()
      })
      .select()
      .single()
    
    if (createError) {
      console.log('⚠️ Erro ao criar profile básico:', createError.message)
    } else {
      console.log('✅ Profile básico criado:', newProfile)
      
      // Deletar o profile de teste
      await supabase
        .from('profiles')
        .delete()
        .eq('email', 'test@example.com')
    }
    
  } catch (error) {
    console.error('❌ Erro geral:', error)
  }
}

checkDatabaseStructure()