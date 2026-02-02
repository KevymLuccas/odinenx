-- =============================================
-- SISTEMA DE ALERTAS EM TEMPO REAL
-- =============================================

-- Tabela de configurações de alertas
CREATE TABLE IF NOT EXISTS alerts_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  type VARCHAR(20) NOT NULL, -- bet, crypto, stock, forex
  symbol VARCHAR(50) NOT NULL, -- BTCUSDT, PETR4, USDBRL, etc
  condition VARCHAR(20) NOT NULL, -- price_above, price_below, volume_above, etc
  target_value DECIMAL(15,8) NOT NULL,
  current_value DECIMAL(15,8) DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  triggered_count INTEGER DEFAULT 0,
  last_triggered_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de histórico de alertas disparados
CREATE TABLE IF NOT EXISTS alerts_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id UUID REFERENCES alerts_config(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol VARCHAR(50) NOT NULL,
  condition VARCHAR(20) NOT NULL,
  target_value DECIMAL(15,8) NOT NULL,
  triggered_value DECIMAL(15,8) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de notificações push (futuro - integração com web push)
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_alerts_config_user ON alerts_config(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_config_active ON alerts_config(is_active);
CREATE INDEX IF NOT EXISTS idx_alerts_config_type ON alerts_config(type);
CREATE INDEX IF NOT EXISTS idx_alerts_history_user ON alerts_history(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_history_read ON alerts_history(is_read);

-- RLS (Row Level Security)
ALTER TABLE alerts_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

-- Policies para alerts_config
CREATE POLICY "Users can view own alert configs" ON alerts_config FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own alert configs" ON alerts_config FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own alert configs" ON alerts_config FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own alert configs" ON alerts_config FOR DELETE USING (auth.uid() = user_id);

-- Policies para alerts_history
CREATE POLICY "Users can view own alert history" ON alerts_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own alert history" ON alerts_history FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own alert history" ON alerts_history FOR UPDATE USING (auth.uid() = user_id);

-- Policies para push_subscriptions
CREATE POLICY "Users can view own push subscriptions" ON push_subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own push subscriptions" ON push_subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own push subscriptions" ON push_subscriptions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own push subscriptions" ON push_subscriptions FOR DELETE USING (auth.uid() = user_id);

-- Função para processar alertas (será chamada por Edge Function)
CREATE OR REPLACE FUNCTION process_alerts()
RETURNS JSON AS $$
DECLARE
  alert_record RECORD;
  alerts_triggered INTEGER := 0;
  result JSON;
BEGIN
  -- Processar alertas ativos
  FOR alert_record IN 
    SELECT * FROM alerts_config 
    WHERE is_active = true
  LOOP
    -- Lógica será implementada na Edge Function
    -- Esta função é só para estrutura
  END LOOP;
  
  result := json_build_object(
    'success', true,
    'alerts_processed', alerts_triggered,
    'timestamp', NOW()
  );
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comentários
COMMENT ON TABLE alerts_config IS 'Configurações de alertas dos usuários';
COMMENT ON TABLE alerts_history IS 'Histórico de alertas disparados';
COMMENT ON TABLE push_subscriptions IS 'Subscrições para notificações push';

-- Exemplos de configuração de alertas:
-- INSERT INTO alerts_config (user_id, name, type, symbol, condition, target_value) VALUES
-- (auth.uid(), 'Bitcoin acima de R$ 350.000', 'crypto', 'BTCUSDT', 'price_above', 350000),
-- (auth.uid(), 'Petrobras abaixo de R$ 35', 'stock', 'PETR4', 'price_below', 35),
-- (auth.uid(), 'Dólar acima de R$ 5.50', 'forex', 'USDBRL', 'price_above', 5.50);