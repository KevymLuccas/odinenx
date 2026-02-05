-- ============================================
-- 🔧 ODINENX v2.0 - Correções de Tabelas
-- EXECUTE NO SQL EDITOR DO SUPABASE
-- https://supabase.com/dashboard/project/mzamszcpbverpadjelck/sql/new
-- ============================================

-- ============================================
-- 1. TABELA: user_alerts (Alertas do Usuário)
-- ============================================
CREATE TABLE IF NOT EXISTS user_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'price', -- 'price', 'percentage', 'odd'
    asset TEXT NOT NULL, -- nome do ativo/time
    condition TEXT DEFAULT 'above', -- 'above', 'below', 'equals'
    target_value DECIMAL(12,2) NOT NULL,
    current_value DECIMAL(12,2),
    active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_user_alerts_user ON user_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_alerts_active ON user_alerts(active);

-- RLS
ALTER TABLE user_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_alerts_select" ON user_alerts;
CREATE POLICY "user_alerts_select" ON user_alerts FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_alerts_insert" ON user_alerts;
CREATE POLICY "user_alerts_insert" ON user_alerts FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_alerts_update" ON user_alerts;
CREATE POLICY "user_alerts_update" ON user_alerts FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_alerts_delete" ON user_alerts;
CREATE POLICY "user_alerts_delete" ON user_alerts FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- 2. TABELA: analysis_history (Histórico de Análises)
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- 'bet', 'trade', 'cartola'
    title TEXT NOT NULL,
    description TEXT,
    asset TEXT, -- time, ativo, jogador
    prediction TEXT, -- previsão feita
    result TEXT, -- 'pending', 'win', 'loss', 'draw'
    confidence DECIMAL(5,2), -- % de confiança
    odd_value DECIMAL(5,2),
    stake DECIMAL(12,2),
    profit_loss DECIMAL(12,2),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_analysis_history_user ON analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_type ON analysis_history(type);
CREATE INDEX IF NOT EXISTS idx_analysis_history_created ON analysis_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_history_result ON analysis_history(result);

-- RLS
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "analysis_history_select" ON analysis_history;
CREATE POLICY "analysis_history_select" ON analysis_history FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "analysis_history_insert" ON analysis_history;
CREATE POLICY "analysis_history_insert" ON analysis_history FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "analysis_history_update" ON analysis_history;
CREATE POLICY "analysis_history_update" ON analysis_history FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 3. TABELA: user_stats (Estatísticas do Usuário)
-- ============================================
CREATE TABLE IF NOT EXISTS user_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    total_analyses INTEGER DEFAULT 0,
    analyses_today INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    total_profit DECIMAL(12,2) DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    last_analysis_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_stats_select" ON user_stats;
CREATE POLICY "user_stats_select" ON user_stats FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_stats_upsert" ON user_stats;
CREATE POLICY "user_stats_upsert" ON user_stats FOR ALL USING (auth.uid() = user_id);

-- ============================================
-- 4. FUNÇÃO: Atualizar stats do usuário
-- ============================================
CREATE OR REPLACE FUNCTION update_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Criar ou atualizar stats
    INSERT INTO user_stats (user_id, total_analyses, analyses_today, last_analysis_date)
    VALUES (NEW.user_id, 1, 1, CURRENT_DATE)
    ON CONFLICT (user_id) DO UPDATE SET
        total_analyses = user_stats.total_analyses + 1,
        analyses_today = CASE 
            WHEN user_stats.last_analysis_date = CURRENT_DATE THEN user_stats.analyses_today + 1
            ELSE 1
        END,
        last_analysis_date = CURRENT_DATE,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para atualizar stats quando nova análise é criada
DROP TRIGGER IF EXISTS on_analysis_created ON analysis_history;
CREATE TRIGGER on_analysis_created
    AFTER INSERT ON analysis_history
    FOR EACH ROW EXECUTE FUNCTION update_user_stats();

-- ============================================
-- 5. FUNÇÃO: Resetar análises diárias (rodar via cron)
-- ============================================
CREATE OR REPLACE FUNCTION reset_daily_analyses()
RETURNS void AS $$
BEGIN
    UPDATE user_stats 
    SET analyses_today = 0 
    WHERE last_analysis_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- ✅ PRONTO!
-- ============================================
SELECT 'Correções aplicadas com sucesso!' as resultado;
