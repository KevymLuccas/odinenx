-- ============================================
-- 🏟️ ODINENX v2.0 - Sistema de Salas ao Vivo
-- Migration: 012_live_rooms_system.sql
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
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'halftime', 'finished')),
    league TEXT,
    league_logo TEXT,
    start_time TIMESTAMPTZ,
    is_private BOOLEAN DEFAULT FALSE,
    private_code TEXT UNIQUE,
    owner_id UUID REFERENCES auth.users(id),
    max_users INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_game_rooms_fixture ON game_rooms(fixture_id);
CREATE INDEX IF NOT EXISTS idx_game_rooms_status ON game_rooms(status);
CREATE INDEX IF NOT EXISTS idx_game_rooms_private ON game_rooms(is_private, private_code);

-- ============================================
-- TABELA: room_users (Usuários na Sala)
-- ============================================
CREATE TABLE IF NOT EXISTS room_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'basic', 'pro', 'elite')),
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
CREATE INDEX IF NOT EXISTS idx_room_users_online ON room_users(room_id, is_online);

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
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'gif', 'sticker', 'reaction', 'system')),
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
    odd_type TEXT NOT NULL, -- '1x2', 'over_under', 'btts', 'correct_score'
    odd_pick TEXT NOT NULL, -- 'home', 'draw', 'away', 'over_2.5', 'yes'
    odd_value DECIMAL(5,2) NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'won', 'lost')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_user_odds_room ON user_odds(room_id);
CREATE INDEX IF NOT EXISTS idx_user_odds_user ON user_odds(user_id);
CREATE INDEX IF NOT EXISTS idx_user_odds_status ON user_odds(room_id, status);

-- ============================================
-- TABELA: room_reactions (Reações Rápidas)
-- ============================================
CREATE TABLE IF NOT EXISTS room_reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reaction TEXT NOT NULL, -- '⚽', '🔥', '😱', '👏', '🎉', '😭', '💪'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice
CREATE INDEX IF NOT EXISTS idx_room_reactions_room ON room_reactions(room_id);

-- ============================================
-- TABELA: user_customizations (Loja Elite)
-- ============================================
CREATE TABLE IF NOT EXISTS user_customizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL, -- 'confete', 'som', 'moldura', 'entrada'
    item_id TEXT NOT NULL,
    item_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    purchased_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, item_type, item_id)
);

-- Índice
CREATE INDEX IF NOT EXISTS idx_user_customizations_user ON user_customizations(user_id);

-- ============================================
-- TABELA: private_room_invites (Convites Sala Privada)
-- ============================================
CREATE TABLE IF NOT EXISTS private_room_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES game_rooms(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES auth.users(id),
    invite_code TEXT UNIQUE NOT NULL,
    max_uses INTEGER DEFAULT 10,
    uses INTEGER DEFAULT 0,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- HABILITAR REALTIME
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE game_rooms;
ALTER PUBLICATION supabase_realtime ADD TABLE room_users;
ALTER PUBLICATION supabase_realtime ADD TABLE room_messages;
ALTER PUBLICATION supabase_realtime ADD TABLE user_odds;
ALTER PUBLICATION supabase_realtime ADD TABLE room_reactions;

-- ============================================
-- RLS (Row Level Security)
-- ============================================

-- game_rooms
ALTER TABLE game_rooms ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Salas públicas visíveis para todos" ON game_rooms
    FOR SELECT USING (is_private = FALSE OR owner_id = auth.uid());

CREATE POLICY "Usuários autenticados podem criar salas" ON game_rooms
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Dono pode atualizar sala" ON game_rooms
    FOR UPDATE USING (owner_id = auth.uid());

-- room_users
ALTER TABLE room_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver usuários da sala" ON room_users
    FOR SELECT USING (TRUE);

CREATE POLICY "Entrar na sala" ON room_users
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Atualizar próprio status" ON room_users
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Sair da sala" ON room_users
    FOR DELETE USING (auth.uid() = user_id);

-- room_messages
ALTER TABLE room_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver mensagens da sala" ON room_messages
    FOR SELECT USING (TRUE);

CREATE POLICY "Enviar mensagem" ON room_messages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- user_odds
ALTER TABLE user_odds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver odds" ON user_odds
    FOR SELECT USING (TRUE);

CREATE POLICY "Criar odds" ON user_odds
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Atualizar próprias odds" ON user_odds
    FOR UPDATE USING (auth.uid() = user_id);

-- room_reactions
ALTER TABLE room_reactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver reações" ON room_reactions
    FOR SELECT USING (TRUE);

CREATE POLICY "Enviar reação" ON room_reactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- user_customizations
ALTER TABLE user_customizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver próprias customizações" ON user_customizations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Comprar customização" ON user_customizations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Atualizar customização" ON user_customizations
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- FUNÇÕES ÚTEIS
-- ============================================

-- Função para contar viewers online
CREATE OR REPLACE FUNCTION get_room_viewers(p_room_id UUID)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*) 
        FROM room_users 
        WHERE room_id = p_room_id AND is_online = TRUE
    );
END;
$$ LANGUAGE plpgsql;

-- Função para atualizar last_seen do usuário
CREATE OR REPLACE FUNCTION update_user_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_seen = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_last_seen
    BEFORE UPDATE ON room_users
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_seen();

-- Função para criar sala automaticamente quando jogo começa
CREATE OR REPLACE FUNCTION create_room_for_fixture(
    p_fixture_id INTEGER,
    p_home_team TEXT,
    p_away_team TEXT,
    p_home_logo TEXT DEFAULT NULL,
    p_away_logo TEXT DEFAULT NULL,
    p_league TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_room_id UUID;
BEGIN
    -- Verificar se sala já existe
    SELECT id INTO v_room_id FROM game_rooms WHERE fixture_id = p_fixture_id;
    
    IF v_room_id IS NULL THEN
        INSERT INTO game_rooms (fixture_id, home_team, away_team, home_team_logo, away_team_logo, league, status)
        VALUES (p_fixture_id, p_home_team, p_away_team, p_home_logo, p_away_logo, p_league, 'live')
        RETURNING id INTO v_room_id;
    END IF;
    
    RETURN v_room_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DADOS INICIAIS (Itens da Loja)
-- ============================================
CREATE TABLE IF NOT EXISTS store_items (
    id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    is_included BOOLEAN DEFAULT FALSE,
    min_plan TEXT DEFAULT 'elite',
    preview_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO store_items (id, item_type, name, description, price, is_included) VALUES
-- Confetes
('confete_copa', 'confete', 'Copa do Mundo', 'Confete temático da Copa', 0, TRUE),
('confete_neon', 'confete', 'Neon Party', 'Confete com cores neon vibrantes', 9.90, FALSE),
('confete_ouro', 'confete', 'Chuva de Ouro', 'Confete dourado premium', 14.90, FALSE),
('confete_fogo', 'confete', 'Chamas', 'Efeito de chamas épico', 19.90, FALSE),
-- Sons
('som_torcida', 'som', 'Torcida', 'Som de torcida vibrando', 0, TRUE),
('som_narracao', 'som', 'Narração Épica', 'Narração estilo Galvão', 4.90, FALSE),
('som_tetra', 'som', 'É TETRA!', 'Grito icônico', 9.90, FALSE),
('som_meme', 'som', 'Pack Memes', 'Sons de memes virais', 14.90, FALSE),
-- Molduras
('moldura_dourada', 'moldura', 'Dourada Animada', 'Moldura dourada com brilho', 0, TRUE),
('moldura_fogo', 'moldura', 'Moldura de Fogo', 'Moldura com chamas animadas', 19.90, FALSE),
('moldura_diamante', 'moldura', 'Diamante', 'Moldura de diamante', 29.90, FALSE),
('moldura_neon', 'moldura', 'Neon Pulsante', 'Moldura neon animada', 24.90, FALSE),
-- Entradas
('entrada_normal', 'entrada', 'Entrada Normal', 'Entrada padrão', 0, TRUE),
('entrada_fogos', 'entrada', 'Entrada com Fogos', 'Fogos de artifício na entrada', 9.90, FALSE),
('entrada_real', 'entrada', 'Entrada Real', 'Entrada estilo realeza', 19.90, FALSE)
ON CONFLICT (id) DO NOTHING;
