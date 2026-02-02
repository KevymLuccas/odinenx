-- =============================================
-- USER TRIAL TRACKING - Sistema de 3 dias grátis
-- =============================================

-- Extensão profiles table com tracking de trial
-- Se não existir a tabela profiles, vamos criá-la
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email VARCHAR(255),
  name VARCHAR(255),
  trial_start DATE DEFAULT CURRENT_DATE,
  trial_used_days INTEGER DEFAULT 0,
  trial_expired BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Se a tabela já existir, adicionar as colunas
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'trial_start'
    ) THEN
        ALTER TABLE profiles ADD COLUMN trial_start DATE DEFAULT CURRENT_DATE;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'trial_used_days'
    ) THEN
        ALTER TABLE profiles ADD COLUMN trial_used_days INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'trial_expired'
    ) THEN
        ALTER TABLE profiles ADD COLUMN trial_expired BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- RLS (Row Level Security)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policies para profiles
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;

CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Função para criar profile automaticamente
CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, email, name, trial_start)
  VALUES (
    NEW.id, 
    NEW.email, 
    COALESCE(NEW.raw_user_meta_data->>'name', NEW.email),
    CURRENT_DATE
  )
  ON CONFLICT (id) DO UPDATE SET
    email = NEW.email,
    updated_at = NOW();
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para criar profile quando usuário se cadastra
DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_profile
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION create_user_profile();

-- Função para verificar e atualizar trial diariamente
CREATE OR REPLACE FUNCTION check_trial_expiration()
RETURNS void AS $$
BEGIN
  -- Atualizar trial_expired para usuários que passaram de 3 dias
  UPDATE profiles 
  SET 
    trial_expired = TRUE,
    updated_at = NOW()
  WHERE 
    trial_start + INTERVAL '3 days' <= CURRENT_DATE
    AND trial_expired = FALSE
    AND id NOT IN (
      -- Excluir usuários com assinatura ativa
      SELECT user_id FROM subscriptions 
      WHERE status = 'active' OR status = 'trialing'
    );
  
  -- Atualizar dias utilizados
  UPDATE profiles 
  SET 
    trial_used_days = GREATEST(0, CURRENT_DATE - trial_start),
    updated_at = NOW()
  WHERE 
    trial_expired = FALSE
    AND trial_start IS NOT NULL;
    
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_profiles_trial_start ON profiles(trial_start);
CREATE INDEX IF NOT EXISTS idx_profiles_trial_expired ON profiles(trial_expired);

-- Comentários
COMMENT ON TABLE profiles IS 'Perfis de usuário com tracking de trial de 3 dias';
COMMENT ON COLUMN profiles.trial_start IS 'Data de início do trial gratuito';
COMMENT ON COLUMN profiles.trial_used_days IS 'Quantidade de dias utilizados do trial';
COMMENT ON COLUMN profiles.trial_expired IS 'Se o trial de 3 dias expirou';