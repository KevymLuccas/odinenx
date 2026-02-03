-- =============================================
-- EXECUTE ESTE SQL NO SUPABASE DASHBOARD > SQL EDITOR
-- =============================================

-- PASSO 1: Adicionar coluna role na tabela profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- PASSO 2: Após criar a conta via interface do Supabase Auth,
-- execute este comando (substitua o email):
-- 
-- UPDATE profiles SET role = 'admin', is_admin = true 
-- WHERE email = 'admin@odinenx.com';

-- =============================================
-- INSTRUÇÕES:
-- =============================================
-- 
-- 1. Acesse: https://supabase.com/dashboard/project/mzamszcpbverpadjelck
-- 
-- 2. Vá em "SQL Editor" (menu lateral)
-- 
-- 3. Cole e execute o PASSO 1 acima
-- 
-- 4. Vá em "Authentication" > "Users" (menu lateral)
-- 
-- 5. Clique em "Add User" > "Create New User"
--    - Email: admin@odinenx.com
--    - Password: Admin@ODINENX2024!
--    - Marque "Auto Confirm User"
-- 
-- 6. Volte ao SQL Editor e execute:
--    UPDATE profiles SET role = 'admin', is_admin = true 
--    WHERE email = 'admin@odinenx.com';
-- 
-- 7. Pronto! Acesse: https://odinenx.vercel.app/admin
-- =============================================
