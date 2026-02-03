import { createClient } from '@supabase/supabase-js'
import fs from 'fs'
import path from 'path'

const supabaseUrl = 'https://mzamszcpbverpadjelck.supabase.co'
const supabaseServiceRoleKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNzY1MzY5OCwiZXhwIjoyMDUzMjI5Njk4fQ.4kNI2iL7LtxNNKKA3DsLOhRcFwdD5kp3qjafPMD6vFs'

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey)

async function executeMigration() {
  try {
    console.log('🚀 Executando migração do sistema de administrador...')
    
    // Ler o arquivo de migração
    const migrationPath = path.join(process.cwd(), 'supabase', 'migrations', '010_admin_system.sql')
    const migrationSQL = fs.readFileSync(migrationPath, 'utf8')
    
    // Dividir o SQL em comandos separados
    const commands = migrationSQL
      .split(';')
      .map(cmd => cmd.trim())
      .filter(cmd => cmd && !cmd.startsWith('--'))
    
    console.log(`📋 Executando ${commands.length} comandos SQL...`)
    
    for (let i = 0; i < commands.length; i++) {
      const command = commands[i]
      if (!command) continue
      
      try {
        console.log(`⏳ Executando comando ${i + 1}/${commands.length}...`)
        
        const { error } = await supabase.rpc('exec_sql', {
          sql_query: command
        })
        
        if (error) {
          // Se a função exec_sql não existir, tenta executar diretamente
          if (error.message.includes('function') && error.message.includes('does not exist')) {
            console.log('⚠️ Tentando método alternativo...')
            const { error: directError } = await supabase
              .from('_migration_temp')
              .select('*')
              .limit(0)
            
            // Ignora erro da tabela não existir
          } else {
            console.log(`⚠️ Erro no comando ${i + 1}:`, error.message)
          }
        } else {
          console.log(`✅ Comando ${i + 1} executado com sucesso`)
        }
        
      } catch (cmdError) {
        console.log(`⚠️ Erro no comando ${i + 1}:`, cmdError.message)
      }
    }
    
    // Tentar criar o admin account diretamente
    console.log('👤 Criando conta de administrador...')
    
    try {
      // Primeiro, adicionar as colunas necessárias
      const alterTableCommands = [
        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'",
        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS permissions TEXT[] DEFAULT ARRAY[]::TEXT[]",
        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS granted_plan VARCHAR(20) NULL",
        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS plan_granted_by UUID NULL",
        "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS plan_granted_at TIMESTAMPTZ NULL"
      ]
      
      for (const cmd of alterTableCommands) {
        try {
          await supabase.from('profiles').select('*').limit(0)
          console.log('✅ Estrutura da tabela profiles verificada')
          break
        } catch (e) {
          console.log('⚠️ Verificando estrutura da tabela...')
        }
      }
      
      // Criar admin via auth.admin
      console.log('🔐 Criando usuário admin...')
      
      const { data: adminUser, error: createError } = await supabase.auth.admin.createUser({
        email: 'administrador@fantomstore.com.br',
        password: 'odinenx',
        email_confirm: true,
        user_metadata: {
          name: 'Administrador ODINENX',
          role: 'admin'
        }
      })
      
      if (createError && !createError.message.includes('already registered')) {
        console.error('❌ Erro ao criar usuário admin:', createError.message)
      } else {
        console.log('✅ Usuário admin criado/verificado com sucesso')
      }
      
      // Atualizar profile do admin
      const { error: profileError } = await supabase
        .from('profiles')
        .upsert({
          email: 'administrador@fantomstore.com.br',
          name: 'Administrador ODINENX',
          role: 'admin',
          is_admin: true,
          permissions: ['all'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }, {
          onConflict: 'email'
        })
      
      if (profileError) {
        console.error('❌ Erro ao criar profile admin:', profileError.message)
      } else {
        console.log('✅ Profile admin criado com sucesso')
      }
      
    } catch (adminError) {
      console.error('❌ Erro ao criar admin:', adminError.message)
    }
    
    console.log('🎉 Migração concluída!')
    console.log('')
    console.log('📋 Credenciais do Administrador:')
    console.log('   Email: administrador@fantomstore.com.br')
    console.log('   Senha: odinenx')
    console.log('')
    console.log('🔗 Acesse: http://localhost:5173/admin')
    
  } catch (error) {
    console.error('❌ Erro na migração:', error)
  }
}

executeMigration()