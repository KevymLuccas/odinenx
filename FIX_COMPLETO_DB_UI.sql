-- ================================================================
-- SCRIPT DE CORREÇÃO COMPLETA DO BANCO DE DADOS - ODINENX v2.0
-- Execute TUDO no SQL Editor do Supabase (supabase.com/dashboard)
-- ================================================================

-- ============================================
-- 1. ADICIONAR COLUNAS FALTANDO EM PROFILES
-- ============================================

-- Colunas de admin/role
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

-- Colunas de trial (para novos usuários não expirarem imediatamente)
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS trial_start DATE DEFAULT CURRENT_DATE;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS trial_used_days INTEGER DEFAULT 0;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS trial_expired BOOLEAN DEFAULT FALSE;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS trial_start_date TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '3 days');

-- Colunas de subscription
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive';

-- ============================================
-- 2. CRIAR TABELA DE ALERTAS SE NÃO EXISTIR
-- ============================================

CREATE TABLE IF NOT EXISTS public.alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type TEXT DEFAULT 'crypto',
  symbol TEXT NOT NULL,
  condition TEXT NOT NULL,
  target_value NUMERIC NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  triggered BOOLEAN DEFAULT FALSE,
  triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Adicionar coluna active se tabela já existe mas coluna não
ALTER TABLE public.alerts ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON public.alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON public.alerts(active);

-- RLS para alerts
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "alerts_select_own" ON public.alerts;
CREATE POLICY "alerts_select_own" ON public.alerts
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "alerts_insert_own" ON public.alerts;
CREATE POLICY "alerts_insert_own" ON public.alerts
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "alerts_update_own" ON public.alerts;
CREATE POLICY "alerts_update_own" ON public.alerts
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "alerts_delete_own" ON public.alerts;
CREATE POLICY "alerts_delete_own" ON public.alerts
  FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- 3. CRIAR TABELA trade_config_risco
-- ============================================

CREATE TABLE IF NOT EXISTS public.trade_config_risco (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  max_position_size NUMERIC DEFAULT 0.05,
  stop_loss_percentage NUMERIC DEFAULT 0.02,
  take_profit_percentage NUMERIC DEFAULT 0.04,
  max_daily_trades INTEGER DEFAULT 10,
  max_open_positions INTEGER DEFAULT 5,
  risk_per_trade NUMERIC DEFAULT 0.01,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

-- RLS para trade_config_risco
ALTER TABLE public.trade_config_risco ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "config_select_own" ON public.trade_config_risco;
CREATE POLICY "config_select_own" ON public.trade_config_risco
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "config_insert_own" ON public.trade_config_risco;
CREATE POLICY "config_insert_own" ON public.trade_config_risco
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "config_update_own" ON public.trade_config_risco;
CREATE POLICY "config_update_own" ON public.trade_config_risco
  FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 4. CRIAR TABELA paper_wallet SE NÃO EXISTIR
-- ============================================

CREATE TABLE IF NOT EXISTS public.paper_wallet (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  balance NUMERIC DEFAULT 100000,
  initial_balance NUMERIC DEFAULT 100000,
  total_trades INTEGER DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  losing_trades INTEGER DEFAULT 0,
  total_profit NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

ALTER TABLE public.paper_wallet ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "wallet_select_own" ON public.paper_wallet;
CREATE POLICY "wallet_select_own" ON public.paper_wallet
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "wallet_insert_own" ON public.paper_wallet;
CREATE POLICY "wallet_insert_own" ON public.paper_wallet
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "wallet_update_own" ON public.paper_wallet;
CREATE POLICY "wallet_update_own" ON public.paper_wallet
  FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 5. CRIAR TABELA paper_trades SE NÃO EXISTIR
-- ============================================

CREATE TABLE IF NOT EXISTS public.paper_trades (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  type TEXT NOT NULL,
  side TEXT NOT NULL,
  entry_price NUMERIC NOT NULL,
  exit_price NUMERIC,
  quantity NUMERIC NOT NULL,
  profit_loss NUMERIC DEFAULT 0,
  status TEXT DEFAULT 'open',
  stop_loss NUMERIC,
  take_profit NUMERIC,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_paper_trades_user ON public.paper_trades(user_id);

ALTER TABLE public.paper_trades ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "trades_select_own" ON public.paper_trades;
CREATE POLICY "trades_select_own" ON public.paper_trades
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "trades_insert_own" ON public.paper_trades;
CREATE POLICY "trades_insert_own" ON public.paper_trades
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "trades_update_own" ON public.paper_trades;
CREATE POLICY "trades_update_own" ON public.paper_trades
  FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 6. ATUALIZAR TRIGGER DE CRIAÇÃO DE USUÁRIO
-- ============================================

-- Primeiro, remover triggers problemáticos
DROP TRIGGER IF EXISTS on_auth_user_created_paper_wallet ON auth.users;
DROP FUNCTION IF EXISTS create_initial_paper_wallet();

-- Criar função segura para novo usuário
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id,
    email,
    plan,
    is_admin,
    role,
    trial_start,
    trial_used_days,
    trial_expired,
    trial_start_date,
    trial_end_date,
    subscription_status,
    created_at,
    updated_at
  ) VALUES (
    NEW.id,
    NEW.email,
    'free',
    FALSE,
    'user',
    CURRENT_DATE,
    0,
    FALSE,
    NOW(),
    NOW() + INTERVAL '3 days',
    'inactive',
    NOW(),
    NOW()
  ) ON CONFLICT (id) DO NOTHING;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recriar trigger seguro
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- 7. ATUALIZAR USUÁRIOS EXISTENTES SEM TRIAL
-- ============================================

UPDATE public.profiles 
SET 
  trial_start = COALESCE(trial_start, CURRENT_DATE),
  trial_used_days = COALESCE(trial_used_days, 0),
  trial_expired = COALESCE(trial_expired, FALSE),
  trial_start_date = COALESCE(trial_start_date, created_at),
  trial_end_date = COALESCE(trial_end_date, created_at + INTERVAL '3 days'),
  is_admin = COALESCE(is_admin, FALSE),
  role = COALESCE(role, 'user'),
  plan = COALESCE(plan, 'free')
WHERE trial_start IS NULL 
   OR trial_start_date IS NULL 
   OR is_admin IS NULL;

-- ============================================
-- 8. CORRIGIR RLS DO PROFILES
-- ============================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Permitir que usuários vejam seu próprio perfil
DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
CREATE POLICY "profiles_select_own" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

-- Permitir que usuários atualizem seu próprio perfil
DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;
CREATE POLICY "profiles_update_own" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- Permitir inserção via trigger (SECURITY DEFINER)
DROP POLICY IF EXISTS "profiles_insert_service" ON public.profiles;
CREATE POLICY "profiles_insert_service" ON public.profiles
  FOR INSERT WITH CHECK (TRUE);

-- ============================================
-- 9. VERIFICAÇÃO FINAL
-- ============================================

-- Ver estrutura final de profiles
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'profiles' 
ORDER BY ordinal_position;

-- Ver se todas as tabelas existem
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- ============================================
-- PRONTO! O banco de dados está corrigido.
-- ============================================
