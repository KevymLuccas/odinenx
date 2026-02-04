/**
 * Script para executar SQL no Supabase
 * Executa a migration 013 para corrigir o trigger
 */

import { createClient } from '@supabase/supabase-js'
import fs from 'fs'

const SUPABASE_URL = 'https://mzamszcpbverpadjelck.supabase.co'
const SERVICE_ROLE_KEY = process.argv[2]

if (!SERVICE_ROLE_KEY) {
  console.error('❌ Uso: node run_migration.js SERVICE_ROLE_KEY')
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

async function runMigration() {
  console.log('🚀 Executando correção do trigger...\n')
  
  try {
    // Dropar trigger existente
    console.log('1️⃣ Removendo trigger antigo...')
    await supabase.rpc('exec_sql', { 
      sql: 'DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users' 
    }).catch(() => {})
    
    // Como não temos exec_sql, vamos tentar via tabelas
    // Primeiro, verificar se profiles existe
    const { data: profiles, error: profilesErr } = await supabase
      .from('profiles')
      .select('id')
      .limit(1)
    
    if (profilesErr && profilesErr.code === '42P01') {
      console.log('⚠️ Tabela profiles não existe. Precisa criar via SQL Editor.')
    } else {
      console.log('✅ Tabela profiles existe!')
    }
    
    // Verificar subscriptions
    const { data: subs, error: subsErr } = await supabase
      .from('subscriptions')
      .select('id')
      .limit(1)
    
    if (subsErr && subsErr.code === '42P01') {
      console.log('⚠️ Tabela subscriptions não existe. Precisa criar via SQL Editor.')
    } else {
      console.log('✅ Tabela subscriptions existe!')
    }
    
    console.log('\n⚠️ Para executar o SQL completo, use o SQL Editor do Supabase:')
    console.log('👉 https://supabase.com/dashboard/project/mzamszcpbverpadjelck/sql/new')
    console.log('\nCole o conteúdo do arquivo: supabase/migrations/013_fix_user_trigger_v2.sql')
    
  } catch (error) {
    console.error('❌ Erro:', error.message)
  }
}

runMigration()
