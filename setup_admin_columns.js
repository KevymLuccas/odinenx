// Script para adicionar colunas admin na tabela profiles
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://mzamszcpbverpadjelck.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTA5NjIsImV4cCI6MjA4NTM2Njk2Mn0.I8uUlJxgm2UgyavzRA6ATcaoV3SRVd9Z-NgeENzzUN4'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function setupAdminColumns() {
  try {
    console.log('🔧 Verificando estrutura da tabela profiles...')
    
    // Tentar buscar um profile para ver a estrutura atual
    const { data: sampleProfile } = await supabase
      .from('profiles')
      .select('*')
      .limit(1)
    
    console.log('📋 Estrutura atual:', sampleProfile?.[0] ? Object.keys(sampleProfile[0]) : 'Nenhum profile encontrado')
    
    // Tentar inserir um profile admin para testar
    const { error: insertError } = await supabase
      .from('profiles')
      .upsert({
        email: 'administrador@fantomstore.com.br',
        name: 'Administrador ODINENX',
        role: 'admin',
        is_admin: true,
        permissions: ['all'],
        granted_plan: null,
        plan_granted_by: null,
        plan_granted_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
    
    if (insertError) {
      console.log('⚠️ Erro ao inserir admin (esperado se colunas não existirem):', insertError.message)
      
      // Se deu erro, provavelmente as colunas não existem
      // Vamos tentar uma inserção mais simples
      const { error: simpleInsertError } = await supabase
        .from('profiles')
        .upsert({
          email: 'administrador@fantomstore.com.br',
          name: 'Administrador ODINENX',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
      
      if (simpleInsertError) {
        console.log('❌ Erro na inserção simples:', simpleInsertError.message)
      } else {
        console.log('✅ Profile básico criado, colunas admin podem estar faltando')
      }
    } else {
      console.log('✅ Admin profile criado com todas as colunas!')
    }
    
    // Verificar se o profile foi criado
    const { data: adminProfile } = await supabase
      .from('profiles')
      .select('*')
      .eq('email', 'administrador@fantomstore.com.br')
      .single()
    
    console.log('👤 Profile admin atual:', adminProfile)
    
  } catch (error) {
    console.error('❌ Erro geral:', error)
  }
}

setupAdminColumns()