-- =========================================
-- 014: Update Plan Types - Ultra & Legend
-- =========================================
-- Atualiza os tipos de planos para incluir Ultra e Legend
-- Substitui 'elite' por 'ultra' e adiciona 'legend'

-- 1. Atualizar subscriptions existentes de 'elite' para 'ultra'
UPDATE subscriptions 
SET plan = 'ultra' 
WHERE plan = 'elite';

-- 2. Remover constraint antiga e adicionar nova em subscriptions
DO $$ 
BEGIN
  -- Tentar remover constraint existente
  BEGIN
    ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_plan_check;
  EXCEPTION WHEN OTHERS THEN
    -- Ignorar se não existir
  END;
  
  -- Adicionar nova constraint
  ALTER TABLE subscriptions 
  ADD CONSTRAINT subscriptions_plan_check 
  CHECK (plan IN ('free', 'basic', 'pro', 'ultra', 'legend'));
END $$;

-- 3. Atualizar room_users se existir
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'room_users') THEN
    -- Atualizar planos existentes
    UPDATE room_users SET plan = 'ultra' WHERE plan = 'elite';
    
    -- Remover constraint antiga
    BEGIN
      ALTER TABLE room_users DROP CONSTRAINT IF EXISTS room_users_plan_check;
    EXCEPTION WHEN OTHERS THEN
      -- Ignorar
    END;
    
    -- Adicionar nova constraint
    ALTER TABLE room_users 
    ADD CONSTRAINT room_users_plan_check 
    CHECK (plan IN ('free', 'basic', 'pro', 'ultra', 'legend'));
  END IF;
END $$;

-- 4. Atualizar profiles.granted_plan se existir
DO $$ 
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'profiles' AND column_name = 'granted_plan'
  ) THEN
    UPDATE profiles SET granted_plan = 'ultra' WHERE granted_plan = 'elite';
    UPDATE profiles SET granted_plan = 'legend' WHERE is_admin = true;
  END IF;
END $$;

-- 5. Atualizar store_items se existir
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'store_items') THEN
    UPDATE store_items SET min_plan = 'ultra' WHERE min_plan = 'elite';
  END IF;
END $$;

-- 6. Atualizar função get_admin_stats se existir
CREATE OR REPLACE FUNCTION get_admin_stats()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_users', (SELECT COUNT(*) FROM profiles),
    'active_subscriptions', (SELECT COUNT(*) FROM subscriptions WHERE status = 'active'),
    'mrr', (
      SELECT COALESCE(SUM(
        CASE 
          WHEN s.plan = 'legend' THEN 199.90
          WHEN s.plan = 'ultra' THEN 99.90
          WHEN s.plan = 'pro' THEN 49.90
          WHEN s.plan = 'basic' THEN 19.90
          ELSE 0 
        END
      ), 0)
      FROM subscriptions s WHERE s.status = 'active'
    ),
    'plans', json_build_object(
      'free', (SELECT COUNT(*) FROM profiles p WHERE NOT EXISTS (SELECT 1 FROM subscriptions s WHERE s.user_id = p.id AND s.status = 'active')),
      'basic', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'basic' AND status = 'active'),
      'pro', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'pro' AND status = 'active'),
      'ultra', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'ultra' AND status = 'active'),
      'legend', (SELECT COUNT(*) FROM subscriptions WHERE plan = 'legend' AND status = 'active')
    )
  ) INTO result;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Comentário sobre os planos
COMMENT ON TABLE subscriptions IS 'Assinaturas dos usuários. Planos: free, basic, pro, ultra, legend';

-- Verificar
SELECT DISTINCT plan, COUNT(*) as total 
FROM subscriptions 
GROUP BY plan 
ORDER BY total DESC;
