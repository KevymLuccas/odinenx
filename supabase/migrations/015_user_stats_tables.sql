-- ===========================================
-- ODINENX: Tabelas de Estatísticas do Usuário
-- Migration: 015_user_stats_tables.sql
-- ===========================================

-- Tabela de estatísticas do usuário
CREATE TABLE IF NOT EXISTS user_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    analyses_today INTEGER DEFAULT 0,
    last_analysis_date DATE,
    total_profit DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de histórico de análises
CREATE TABLE IF NOT EXISTS analysis_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    match_id TEXT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    league TEXT,
    analysis_type TEXT DEFAULT 'bet', -- bet, trade, cartola
    prediction TEXT, -- ex: "home_win", "over_2.5", "btts"
    odds DECIMAL(5,2),
    stake DECIMAL(10,2),
    result TEXT, -- "win", "loss", "pending", "void"
    profit DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_user_id ON analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at ON analysis_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_history_result ON analysis_history(result);

-- RLS (Row Level Security)
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;

-- Políticas para user_stats
DROP POLICY IF EXISTS "Users can view own stats" ON user_stats;
CREATE POLICY "Users can view own stats" ON user_stats
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own stats" ON user_stats;
CREATE POLICY "Users can insert own stats" ON user_stats
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own stats" ON user_stats;
CREATE POLICY "Users can update own stats" ON user_stats
    FOR UPDATE USING (auth.uid() = user_id);

-- Políticas para analysis_history
DROP POLICY IF EXISTS "Users can view own history" ON analysis_history;
CREATE POLICY "Users can view own history" ON analysis_history
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own history" ON analysis_history;
CREATE POLICY "Users can insert own history" ON analysis_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own history" ON analysis_history;
CREATE POLICY "Users can update own history" ON analysis_history
    FOR UPDATE USING (auth.uid() = user_id);

-- Função para criar stats automaticamente para novos usuários
CREATE OR REPLACE FUNCTION create_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_stats (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para criar stats ao registrar usuário
DROP TRIGGER IF EXISTS on_auth_user_created_stats ON auth.users;
CREATE TRIGGER on_auth_user_created_stats
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_stats();

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_user_stats_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para updated_at
DROP TRIGGER IF EXISTS update_user_stats_timestamp ON user_stats;
CREATE TRIGGER update_user_stats_timestamp
    BEFORE UPDATE ON user_stats
    FOR EACH ROW EXECUTE FUNCTION update_user_stats_timestamp();

-- Inserir stats para usuários existentes que ainda não têm
INSERT INTO user_stats (user_id)
SELECT id FROM auth.users
WHERE id NOT IN (SELECT user_id FROM user_stats)
ON CONFLICT (user_id) DO NOTHING;
