-- =========================================
-- 012: Profile Customization - Avatar & Focus Preference
-- =========================================
-- Adiciona sistema de personalização do perfil do usuário
-- - Avatar/foto de perfil
-- - Foco/preferência do dashboard (BET, Trade, Cartola)

-- 1. Adicionar colunas na tabela profiles (se existir)
DO $$ 
BEGIN
  -- Adicionar coluna avatar_url
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'profiles' AND column_name = 'avatar_url'
  ) THEN
    ALTER TABLE profiles ADD COLUMN avatar_url TEXT;
  END IF;
  
  -- Adicionar coluna focus_preference
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'profiles' AND column_name = 'focus_preference'
  ) THEN
    ALTER TABLE profiles ADD COLUMN focus_preference TEXT DEFAULT 'all';
  END IF;
END $$;

-- 2. Criar bucket de storage para avatares (executar no Supabase Dashboard)
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('avatars', 'avatars', true)
-- ON CONFLICT (id) DO NOTHING;

-- 3. Políticas de storage para avatares
-- (Executar no Supabase Dashboard > Storage > Policies)

-- Política de leitura pública
-- CREATE POLICY "Avatars são públicos" ON storage.objects
--   FOR SELECT USING (bucket_id = 'avatars');

-- Política de upload para usuários autenticados
-- CREATE POLICY "Usuários podem fazer upload do próprio avatar" ON storage.objects
--   FOR INSERT WITH CHECK (
--     bucket_id = 'avatars' 
--     AND auth.uid()::text = (storage.foldername(name))[1]
--   );

-- Política de atualização
-- CREATE POLICY "Usuários podem atualizar próprio avatar" ON storage.objects
--   FOR UPDATE USING (
--     bucket_id = 'avatars' 
--     AND auth.uid()::text = (storage.foldername(name))[1]
--   );

-- Política de deleção
-- CREATE POLICY "Usuários podem deletar próprio avatar" ON storage.objects
--   FOR DELETE USING (
--     bucket_id = 'avatars' 
--     AND auth.uid()::text = (storage.foldername(name))[1]
--   );

-- 4. Comentários nas colunas
COMMENT ON COLUMN profiles.avatar_url IS 'URL da foto de perfil do usuário';
COMMENT ON COLUMN profiles.focus_preference IS 'Foco do dashboard: all, bet, trade, cartola';

-- Verificar
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name IN ('avatar_url', 'focus_preference');
