-- ============================================
-- 🏟️ ODINENX v2.0 - Sistema de Salas ao Vivo
-- EXECUTE ESTE SCRIPT NO SQL EDITOR DO SUPABASE
-- https://supabase.com/dashboard/project/mzamszcpbverpadjelck/sql/new
-- ============================================

-- ============================================
-- TABELA: game_rooms (Salas de Jogo)
-- ============================================
CREATE TABLE IF NOT EXISTS game_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fixture_id INTEGER NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_team_logo TEXT,
    away_team_logo TEXT,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    minute INTEGER DEFAULT 0,
    status TEXT DEFAULT 'scheduled',
    league TEXT,
    league_logo TEXT,
    start_time TIMESTAMPTZ,
    is_private BOOLEAN DEFAULT FALSE,
    private_code TEXT,
    owner_id UUID REFERENCES auth.users(id),
    max_users INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_game_rooms_fixture ON game_rooms(fixture_id);
CREATE INDEX IF NOT EXISTS idx_game_rooms_status ON game_rooms(status);

-- ============================================
-- TABELA: room_users (Usuários na Sala)
-- ============================================
CREATE TABLE IF NOT EXISTS room_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    plan TEXT DEFAULT 'free',
    avatar_url TEXT,
    selected_odds JSONB DEFAULT '[]',
    is_online BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(room_id, user_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_room_users_room ON room_users(room_id);
CREATE INDEX IF NOT EXISTS idx_room_users_user ON room_users(user_id);

-- ============================================
-- TABELA: room_messages (Chat da Sala)
-- ============================================
CREATE TABLE IF NOT EXISTS room_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    username TEXT NOT NULL,
    user_plan TEXT DEFAULT 'free',
    message TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    gif_url TEXT,
    sticker_id TEXT,
    is_highlighted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_room_messages_room ON room_messages(room_id);
CREATE INDEX IF NOT EXISTS idx_room_messages_created ON room_messages(room_id, created_at DESC);

-- ============================================
-- TABELA: user_odds (Odds Selecionadas)
-- ============================================
CREATE TABLE IF NOT EXISTS user_odds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    odd_type TEXT NOT NULL,
    odd_pick TEXT NOT NULL,
    odd_value DECIMAL(5,2) NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_user_odds_room ON user_odds(room_id);
CREATE INDEX IF NOT EXISTS idx_user_odds_user ON user_odds(user_id);

-- ============================================
-- TABELA: room_reactions (Reações Rápidas)
-- ============================================
CREATE TABLE IF NOT EXISTS room_reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reaction TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_room_reactions_room ON room_reactions(room_id);

-- ============================================
-- HABILITAR RLS (Row Level Security)
-- ============================================

-- game_rooms
ALTER TABLE game_rooms ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "game_rooms_select" ON game_rooms;
CREATE POLICY "game_rooms_select" ON game_rooms FOR SELECT USING (true);

DROP POLICY IF EXISTS "game_rooms_insert" ON game_rooms;
CREATE POLICY "game_rooms_insert" ON game_rooms FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "game_rooms_update" ON game_rooms;
CREATE POLICY "game_rooms_update" ON game_rooms FOR UPDATE USING (auth.uid() IS NOT NULL);

-- room_users
ALTER TABLE room_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "room_users_select" ON room_users;
CREATE POLICY "room_users_select" ON room_users FOR SELECT USING (true);

DROP POLICY IF EXISTS "room_users_insert" ON room_users;
CREATE POLICY "room_users_insert" ON room_users FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "room_users_update" ON room_users;
CREATE POLICY "room_users_update" ON room_users FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "room_users_delete" ON room_users;
CREATE POLICY "room_users_delete" ON room_users FOR DELETE USING (auth.uid() = user_id);

-- room_messages
ALTER TABLE room_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "room_messages_select" ON room_messages;
CREATE POLICY "room_messages_select" ON room_messages FOR SELECT USING (true);

DROP POLICY IF EXISTS "room_messages_insert" ON room_messages;
CREATE POLICY "room_messages_insert" ON room_messages FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- user_odds
ALTER TABLE user_odds ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_odds_select" ON user_odds;
CREATE POLICY "user_odds_select" ON user_odds FOR SELECT USING (true);

DROP POLICY IF EXISTS "user_odds_insert" ON user_odds;
CREATE POLICY "user_odds_insert" ON user_odds FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_odds_update" ON user_odds;
CREATE POLICY "user_odds_update" ON user_odds FOR UPDATE USING (auth.uid() = user_id);

-- room_reactions
ALTER TABLE room_reactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "room_reactions_select" ON room_reactions;
CREATE POLICY "room_reactions_select" ON room_reactions FOR SELECT USING (true);

DROP POLICY IF EXISTS "room_reactions_insert" ON room_reactions;
CREATE POLICY "room_reactions_insert" ON room_reactions FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- HABILITAR REALTIME (pode dar erro se já existir, ignore)
-- ============================================
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE game_rooms;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE room_users;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE room_messages;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE user_odds;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE room_reactions;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- ============================================
-- ✅ PRONTO! Tabelas criadas com sucesso!
-- ============================================
SELECT 'Tabelas criadas com sucesso!' as resultado;
