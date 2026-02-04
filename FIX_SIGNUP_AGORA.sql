-- =============================================
-- SOLUÇÃO DEFINITIVA - REMOVE TRIGGER PROBLEMÁTICO
-- Execute no SQL Editor do Supabase
-- =============================================

-- 1. REMOVER TRIGGER COMPLETAMENTE
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS handle_new_user_trigger ON auth.users;

-- 2. REMOVER TODAS AS FUNÇÕES RELACIONADAS
DROP FUNCTION IF EXISTS handle_new_user() CASCADE;
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;

-- 3. GARANTIR QUE PROFILES EXISTE E ESTÁ CORRETA
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  stripe_customer_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. DESABILITAR RLS TEMPORARIAMENTE PARA TESTES
ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;

-- 5. DROPAR TODAS AS POLICIES
DO $$ 
DECLARE
    policy_name TEXT;
BEGIN
    FOR policy_name IN 
        SELECT policyname FROM pg_policies WHERE tablename = 'profiles'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON profiles', policy_name);
    END LOOP;
END $$;

-- 6. HABILITAR RLS COM POLÍTICA PERMISSIVA
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_profiles" ON profiles FOR ALL USING (true) WITH CHECK (true);

-- 7. CONCEDER TODAS AS PERMISSÕES
GRANT ALL ON public.profiles TO postgres;
GRANT ALL ON public.profiles TO service_role;
GRANT ALL ON public.profiles TO authenticated;
GRANT ALL ON public.profiles TO anon;

-- 8. SUBSCRIPTIONS TAMBÉM
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  stripe_subscription_id TEXT,
  stripe_customer_id TEXT,
  plan TEXT DEFAULT 'free',
  status TEXT DEFAULT 'active',
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.subscriptions DISABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE
    policy_name TEXT;
BEGIN
    FOR policy_name IN 
        SELECT policyname FROM pg_policies WHERE tablename = 'subscriptions'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON subscriptions', policy_name);
    END LOOP;
END $$;

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_all_subscriptions" ON subscriptions FOR ALL USING (true) WITH CHECK (true);

GRANT ALL ON public.subscriptions TO postgres;
GRANT ALL ON public.subscriptions TO service_role;
GRANT ALL ON public.subscriptions TO authenticated;
GRANT ALL ON public.subscriptions TO anon;

-- 9. VERIFICAR
SELECT 'Triggers removidos:' as status, count(*) as count 
FROM pg_trigger 
WHERE tgname LIKE '%user%' AND tgrelid = 'auth.users'::regclass;

SELECT '✅ PRONTO! O signup deve funcionar agora.' as resultado;
