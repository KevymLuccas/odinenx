-- =============================================
-- SISTEMA DE ADMINISTRADOR COMPLETO
-- =============================================

-- Adicionar coluna de role aos profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS permissions TEXT[] DEFAULT ARRAY[]::TEXT[];
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS granted_plan VARCHAR(20) NULL;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS plan_granted_by UUID NULL;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS plan_granted_at TIMESTAMPTZ NULL;

-- Criar conta de administrador específica
-- Primeiro, vamos criar uma função para inserir o admin
CREATE OR REPLACE FUNCTION create_admin_account()
RETURNS void AS $$
BEGIN
  -- Inserir o usuário admin se não existir
  INSERT INTO auth.users (
    id,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    role
  )
  VALUES (
    gen_random_uuid(),
    'administrador@fantomstore.com.br',
    crypt('odinenx', gen_salt('bf')),
    NOW(),
    NOW(),
    NOW(),
    '{"provider": "email", "providers": ["email"]}',
    '{"name": "Administrador ODINENX", "role": "admin"}',
    false,
    'authenticated'
  )
  ON CONFLICT (email) DO NOTHING;
  
  -- Criar profile do admin
  INSERT INTO profiles (
    id,
    email,
    name,
    role,
    is_admin,
    permissions,
    trial_expired,
    created_at
  )
  SELECT 
    u.id,
    u.email,
    'Administrador ODINENX',
    'admin',
    true,
    ARRAY['admin_panel', 'user_management', 'plan_management', 'financial_reports', 'system_monitoring'],
    false,
    NOW()
  FROM auth.users u
  WHERE u.email = 'administrador@fantomstore.com.br'
  ON CONFLICT (id) DO UPDATE SET
    role = 'admin',
    is_admin = true,
    permissions = ARRAY['admin_panel', 'user_management', 'plan_management', 'financial_reports', 'system_monitoring'];
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Executar criação do admin
SELECT create_admin_account();

-- Tabela de logs de ações administrativas
CREATE TABLE IF NOT EXISTS admin_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID REFERENCES auth.users(id),
  action VARCHAR(100) NOT NULL,
  target_user_id UUID REFERENCES auth.users(id),
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de planos concedidos manualmente
CREATE TABLE IF NOT EXISTS granted_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  plan_id VARCHAR(20) NOT NULL,
  granted_by UUID REFERENCES auth.users(id),
  expires_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Função para verificar se usuário é admin
CREATE OR REPLACE FUNCTION is_admin_user(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM profiles 
    WHERE id = user_id 
    AND (is_admin = true OR role = 'admin')
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para conceder plano a usuário
CREATE OR REPLACE FUNCTION grant_plan_to_user(
  target_user_id UUID,
  plan_id VARCHAR(20),
  admin_id UUID,
  expires_at TIMESTAMPTZ DEFAULT NULL
)
RETURNS json AS $$
DECLARE
  result json;
BEGIN
  -- Verificar se quem está concedendo é admin
  IF NOT is_admin_user(admin_id) THEN
    RETURN json_build_object('success', false, 'error', 'Acesso negado: usuário não é administrador');
  END IF;
  
  -- Inserir plano concedido
  INSERT INTO granted_plans (user_id, plan_id, granted_by, expires_at)
  VALUES (target_user_id, plan_id, admin_id, expires_at);
  
  -- Atualizar profile do usuário
  UPDATE profiles 
  SET 
    granted_plan = plan_id,
    plan_granted_by = admin_id,
    plan_granted_at = NOW()
  WHERE id = target_user_id;
  
  -- Registrar log
  INSERT INTO admin_logs (admin_id, action, target_user_id, details)
  VALUES (
    admin_id, 
    'GRANT_PLAN', 
    target_user_id, 
    json_build_object('plan', plan_id, 'expires_at', expires_at)
  );
  
  result := json_build_object(
    'success', true,
    'message', 'Plano concedido com sucesso',
    'plan', plan_id,
    'user_id', target_user_id
  );
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para remover acesso de usuário
CREATE OR REPLACE FUNCTION revoke_user_access(
  target_user_id UUID,
  admin_id UUID
)
RETURNS json AS $$
DECLARE
  result json;
BEGIN
  -- Verificar se quem está revogando é admin
  IF NOT is_admin_user(admin_id) THEN
    RETURN json_build_object('success', false, 'error', 'Acesso negado: usuário não é administrador');
  END IF;
  
  -- Desativar planos concedidos
  UPDATE granted_plans 
  SET is_active = false 
  WHERE user_id = target_user_id;
  
  -- Forçar expiração do trial
  UPDATE profiles 
  SET 
    trial_expired = true,
    granted_plan = NULL,
    plan_granted_by = NULL,
    plan_granted_at = NULL
  WHERE id = target_user_id;
  
  -- Registrar log
  INSERT INTO admin_logs (admin_id, action, target_user_id, details)
  VALUES (admin_id, 'REVOKE_ACCESS', target_user_id, json_build_object('reason', 'Manual revocation'));
  
  result := json_build_object(
    'success', true,
    'message', 'Acesso revogado com sucesso',
    'user_id', target_user_id
  );
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para obter estatísticas completas
CREATE OR REPLACE FUNCTION get_admin_stats()
RETURNS json AS $$
DECLARE
  result json;
  total_users integer;
  active_subscriptions integer;
  trial_users integer;
  expired_trials integer;
  revenue_estimate decimal;
  plan_stats json;
BEGIN
  -- Total de usuários
  SELECT COUNT(*) INTO total_users FROM profiles;
  
  -- Assinaturas ativas (incluindo concedidas)
  SELECT COUNT(*) INTO active_subscriptions 
  FROM profiles p
  LEFT JOIN subscriptions s ON p.id = s.user_id
  WHERE s.status = 'active' OR p.granted_plan IS NOT NULL;
  
  -- Usuários em trial
  SELECT COUNT(*) INTO trial_users 
  FROM profiles 
  WHERE trial_expired = false AND granted_plan IS NULL;
  
  -- Trials expirados
  SELECT COUNT(*) INTO expired_trials 
  FROM profiles 
  WHERE trial_expired = true AND granted_plan IS NULL;
  
  -- Estimativa de receita (simplificada)
  revenue_estimate := (
    SELECT COALESCE(SUM(
      CASE 
        WHEN s.plan = 'basic' THEN 79
        WHEN s.plan = 'pro' THEN 199
        WHEN s.plan = 'elite' THEN 399
        ELSE 0
      END
    ), 0)
    FROM subscriptions s
    WHERE s.status = 'active'
  );
  
  -- Estatísticas por plano
  SELECT json_build_object(
    'free', (SELECT COUNT(*) FROM profiles WHERE (granted_plan IS NULL AND trial_expired = false) OR (granted_plan IS NULL AND NOT EXISTS(SELECT 1 FROM subscriptions WHERE user_id = profiles.id AND status = 'active'))),
    'basic', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'basic' AND status = 'active') + (SELECT COUNT(*) FROM profiles WHERE granted_plan = 'basic'),
    'pro', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'pro' AND status = 'active') + (SELECT COUNT(*) FROM profiles WHERE granted_plan = 'pro'),
    'elite', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'elite' AND status = 'active') + (SELECT COUNT(*) FROM profiles WHERE granted_plan = 'elite')
  ) INTO plan_stats;
  
  result := json_build_object(
    'totalUsers', total_users,
    'activeSubscriptions', active_subscriptions,
    'trialUsers', trial_users,
    'expiredTrials', expired_trials,
    'revenueEstimate', revenue_estimate,
    'planStats', plan_stats,
    'timestamp', NOW()
  );
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_is_admin ON profiles(is_admin);
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_granted_plans_user_id ON granted_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_granted_plans_is_active ON granted_plans(is_active);

-- RLS para admin_logs
ALTER TABLE admin_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE granted_plans ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Admins can view all logs" ON admin_logs FOR SELECT 
USING (is_admin_user(auth.uid()));

CREATE POLICY "Admins can insert logs" ON admin_logs FOR INSERT 
WITH CHECK (is_admin_user(auth.uid()));

CREATE POLICY "Admins can view granted plans" ON granted_plans FOR SELECT 
USING (is_admin_user(auth.uid()));

CREATE POLICY "Admins can manage granted plans" ON granted_plans FOR ALL
USING (is_admin_user(auth.uid()));

-- Permitir acesso às funções admin
GRANT EXECUTE ON FUNCTION grant_plan_to_user(UUID, VARCHAR, UUID, TIMESTAMPTZ) TO authenticated;
GRANT EXECUTE ON FUNCTION revoke_user_access(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_admin_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION is_admin_user(UUID) TO authenticated;

-- Comentários
COMMENT ON TABLE admin_logs IS 'Logs de ações administrativas';
COMMENT ON TABLE granted_plans IS 'Planos concedidos manualmente por administradores';
COMMENT ON FUNCTION is_admin_user(UUID) IS 'Verifica se usuário é administrador';
COMMENT ON FUNCTION grant_plan_to_user(UUID, VARCHAR, UUID, TIMESTAMPTZ) IS 'Concede plano a usuário específico';
COMMENT ON FUNCTION revoke_user_access(UUID, UUID) IS 'Remove acesso de usuário';
COMMENT ON FUNCTION get_admin_stats() IS 'Retorna estatísticas completas do sistema';