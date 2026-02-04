-- Migration: Sistema de tracking de análises para evitar burla
-- Substitui localStorage por banco de dados

-- Tabela para rastrear análises vistas por usuário
CREATE TABLE IF NOT EXISTS user_analyses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  analysis_id TEXT NOT NULL,
  analysis_type TEXT DEFAULT 'palpite', -- palpite, cartola, odds
  viewed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  viewed_date DATE DEFAULT CURRENT_DATE -- Coluna para facilitar índice único
);

-- Índice único para evitar duplicatas no mesmo dia (usando coluna date)
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_analyses_unique_daily 
  ON user_analyses(user_id, analysis_id, viewed_date);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_user_analyses_user_id ON user_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analyses_date ON user_analyses(viewed_at);
CREATE INDEX IF NOT EXISTS idx_user_analyses_type ON user_analyses(analysis_type);

-- RLS (Row Level Security)
ALTER TABLE user_analyses ENABLE ROW LEVEL SECURITY;

-- Política: usuário só vê suas próprias análises
CREATE POLICY "Users can view own analyses" ON user_analyses
  FOR SELECT USING (auth.uid() = user_id);

-- Política: usuário só pode inserir suas próprias análises
CREATE POLICY "Users can insert own analyses" ON user_analyses
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Função para contar análises do dia
CREATE OR REPLACE FUNCTION get_daily_analyses_count(p_user_id UUID, p_type TEXT DEFAULT 'palpite')
RETURNS INTEGER AS $$
DECLARE
  count_result INTEGER;
BEGIN
  SELECT COUNT(*) INTO count_result
  FROM user_analyses
  WHERE user_id = p_user_id 
    AND analysis_type = p_type
    AND viewed_date = CURRENT_DATE;
  
  RETURN COALESCE(count_result, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para verificar se pode ver análise (limite de 3 para free)
CREATE OR REPLACE FUNCTION can_view_analysis(
  p_user_id UUID, 
  p_analysis_id TEXT,
  p_type TEXT DEFAULT 'palpite'
)
RETURNS JSONB AS $$
DECLARE
  user_plan TEXT;
  daily_count INTEGER;
  already_viewed BOOLEAN;
  max_free INTEGER := 3;
BEGIN
  -- Verificar plano do usuário
  SELECT COALESCE(plan, 'free') INTO user_plan
  FROM subscriptions
  WHERE user_id = p_user_id AND status = 'active';
  
  -- Se não encontrou assinatura, é free
  IF user_plan IS NULL THEN
    user_plan := 'free';
  END IF;
  
  -- Planos pagos têm acesso ilimitado
  IF user_plan IN ('basic', 'pro', 'elite') THEN
    RETURN jsonb_build_object(
      'allowed', true,
      'plan', user_plan,
      'remaining', -1,
      'reason', 'premium_access'
    );
  END IF;
  
  -- Para free: verificar se já viu esta análise hoje
  SELECT EXISTS(
    SELECT 1 FROM user_analyses
    WHERE user_id = p_user_id 
      AND analysis_id = p_analysis_id
      AND viewed_date = CURRENT_DATE
  ) INTO already_viewed;
  
  IF already_viewed THEN
    RETURN jsonb_build_object(
      'allowed', true,
      'plan', 'free',
      'remaining', NULL,
      'reason', 'already_viewed_today'
    );
  END IF;
  
  -- Contar quantas já viu hoje
  SELECT get_daily_analyses_count(p_user_id, p_type) INTO daily_count;
  
  IF daily_count >= max_free THEN
    RETURN jsonb_build_object(
      'allowed', false,
      'plan', 'free',
      'remaining', 0,
      'reason', 'daily_limit_reached'
    );
  END IF;
  
  RETURN jsonb_build_object(
    'allowed', true,
    'plan', 'free',
    'remaining', max_free - daily_count - 1,
    'reason', 'within_limit'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para registrar visualização de análise
CREATE OR REPLACE FUNCTION register_analysis_view(
  p_user_id UUID,
  p_analysis_id TEXT,
  p_type TEXT DEFAULT 'palpite'
)
RETURNS JSONB AS $$
DECLARE
  can_view JSONB;
BEGIN
  -- Primeiro verificar se pode ver
  can_view := can_view_analysis(p_user_id, p_analysis_id, p_type);
  
  -- Se não pode, retornar erro
  IF NOT (can_view->>'allowed')::boolean THEN
    RETURN can_view;
  END IF;
  
  -- Registrar visualização (ignorar se já existe)
  INSERT INTO user_analyses (user_id, analysis_id, analysis_type, viewed_date)
  VALUES (p_user_id, p_analysis_id, p_type, CURRENT_DATE)
  ON CONFLICT (user_id, analysis_id, viewed_date) DO NOTHING;
  
  RETURN can_view;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comentários
COMMENT ON TABLE user_analyses IS 'Rastreia análises visualizadas por usuários para controle de limites';
COMMENT ON FUNCTION can_view_analysis IS 'Verifica se usuário pode visualizar uma análise (respeita limite de 3/dia para free)';
COMMENT ON FUNCTION register_analysis_view IS 'Registra visualização e retorna se foi permitido';
