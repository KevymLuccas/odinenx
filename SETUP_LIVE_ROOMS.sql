-- ================================================================
-- SISTEMA DE SALAS AO VIVO - ODINENX v2.0
-- Execute no SQL Editor do Supabase
-- ================================================================

-- ============================================
-- 0. LIMPAR TABELAS EXISTENTES
-- ============================================

DROP TABLE IF EXISTS public.room_reactions CASCADE;
DROP TABLE IF EXISTS public.user_odds CASCADE;
DROP TABLE IF EXISTS public.room_messages CASCADE;
DROP TABLE IF EXISTS public.room_users CASCADE;
DROP TABLE IF EXISTS public.game_rooms CASCADE;

-- ============================================
-- 1. CRIAR TODAS AS TABELAS PRIMEIRO
-- ============================================

-- game_rooms
CREATE TABLE public.game_rooms (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  fixture_id INTEGER,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_team_logo TEXT,
  away_team_logo TEXT,
  home_score INTEGER DEFAULT 0,
  away_score INTEGER DEFAULT 0,
  minute INTEGER DEFAULT 0,
  status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'halftime', 'finished', 'cancelled')),
  league TEXT,
  league_logo TEXT,
  start_time TIMESTAMPTZ,
  is_private BOOLEAN DEFAULT FALSE,
  private_code TEXT UNIQUE,
  owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  max_users INTEGER DEFAULT 500,
  chat_enabled BOOLEAN DEFAULT TRUE,
  viewers_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- room_users
CREATE TABLE public.room_users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  room_id UUID NOT NULL REFERENCES public.game_rooms(id) ON DELETE CASCADE,
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

-- room_messages
CREATE TABLE public.room_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  room_id UUID NOT NULL REFERENCES public.game_rooms(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  username TEXT NOT NULL,
  plan TEXT DEFAULT 'free',
  avatar_url TEXT,
  message TEXT NOT NULL,
  message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'gif', 'sticker', 'system', 'goal', 'reaction')),
  extras JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_odds
CREATE TABLE public.user_odds (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  room_id UUID NOT NULL REFERENCES public.game_rooms(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  odd_type TEXT NOT NULL,
  odd_pick TEXT NOT NULL,
  odd_value NUMERIC NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'won', 'lost', 'void')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  settled_at TIMESTAMPTZ
);

-- room_reactions
CREATE TABLE public.room_reactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  room_id UUID NOT NULL REFERENCES public.game_rooms(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  reaction TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. CRIAR ÍNDICES
-- ============================================

CREATE INDEX idx_game_rooms_status ON public.game_rooms(status);
CREATE INDEX idx_game_rooms_fixture ON public.game_rooms(fixture_id);
CREATE INDEX idx_game_rooms_private_code ON public.game_rooms(private_code);
CREATE INDEX idx_game_rooms_owner ON public.game_rooms(owner_id);

CREATE INDEX idx_room_users_room ON public.room_users(room_id);
CREATE INDEX idx_room_users_user ON public.room_users(user_id);
CREATE INDEX idx_room_users_online ON public.room_users(is_online);

CREATE INDEX idx_room_messages_room ON public.room_messages(room_id);
CREATE INDEX idx_room_messages_created ON public.room_messages(created_at);

CREATE INDEX idx_user_odds_room ON public.user_odds(room_id);
CREATE INDEX idx_user_odds_user ON public.user_odds(user_id);

CREATE INDEX idx_room_reactions_room ON public.room_reactions(room_id);

-- ============================================
-- 3. HABILITAR RLS EM TODAS AS TABELAS
-- ============================================

ALTER TABLE public.game_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.room_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.room_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.room_reactions ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 4. CRIAR POLÍTICAS RLS
-- ============================================

-- game_rooms policies
CREATE POLICY "game_rooms_select_public" ON public.game_rooms
  FOR SELECT USING (
    is_private = FALSE 
    OR owner_id = auth.uid() 
    OR id IN (SELECT room_id FROM public.room_users WHERE user_id = auth.uid())
  );

CREATE POLICY "game_rooms_insert_authenticated" ON public.game_rooms
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "game_rooms_update_owner" ON public.game_rooms
  FOR UPDATE USING (owner_id = auth.uid());

-- room_users policies
CREATE POLICY "room_users_select_all" ON public.room_users
  FOR SELECT USING (TRUE);

CREATE POLICY "room_users_insert_own" ON public.room_users
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "room_users_update_own" ON public.room_users
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "room_users_delete_own" ON public.room_users
  FOR DELETE USING (auth.uid() = user_id);

-- room_messages policies
CREATE POLICY "room_messages_select_all" ON public.room_messages
  FOR SELECT USING (TRUE);

CREATE POLICY "room_messages_insert_authenticated" ON public.room_messages
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- user_odds policies
CREATE POLICY "user_odds_select_all" ON public.user_odds
  FOR SELECT USING (TRUE);

CREATE POLICY "user_odds_insert_own" ON public.user_odds
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_odds_update_own" ON public.user_odds
  FOR UPDATE USING (auth.uid() = user_id);

-- room_reactions policies
CREATE POLICY "room_reactions_select_all" ON public.room_reactions
  FOR SELECT USING (TRUE);

CREATE POLICY "room_reactions_insert_authenticated" ON public.room_reactions
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================
-- 5. INSERIR JOGOS DE DEMONSTRAÇÃO
-- ============================================

INSERT INTO public.game_rooms (fixture_id, home_team, away_team, home_team_logo, away_team_logo, home_score, away_score, minute, status, league, viewers_count, start_time)
VALUES 
  (1001, 'Flamengo', 'Palmeiras', 
   'https://media.api-sports.io/football/teams/127.png', 
   'https://media.api-sports.io/football/teams/121.png',
   2, 1, 67, 'live', 'Brasileirão Série A', 342, NOW()),
  
  (1002, 'Real Madrid', 'Barcelona', 
   'https://media.api-sports.io/football/teams/541.png', 
   'https://media.api-sports.io/football/teams/529.png',
   1, 1, 34, 'live', 'La Liga', 1523, NOW()),
  
  (1003, 'Manchester City', 'Liverpool', 
   'https://media.api-sports.io/football/teams/50.png', 
   'https://media.api-sports.io/football/teams/40.png',
   0, 0, 0, 'scheduled', 'Premier League', 0, NOW() + INTERVAL '2 hours'),
  
  (1004, 'Corinthians', 'São Paulo', 
   'https://media.api-sports.io/football/teams/131.png', 
   'https://media.api-sports.io/football/teams/126.png',
   0, 0, 0, 'scheduled', 'Brasileirão Série A', 0, NOW() + INTERVAL '4 hours');

-- ============================================
-- 6. FUNÇÕES E TRIGGERS
-- ============================================

CREATE OR REPLACE FUNCTION generate_private_code()
RETURNS TEXT AS $$
DECLARE
  chars TEXT := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  result TEXT := '';
  i INTEGER;
BEGIN
  FOR i IN 1..6 LOOP
    result := result || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
  END LOOP;
  RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_viewers_count()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.game_rooms
  SET viewers_count = (
    SELECT COUNT(*) FROM public.room_users 
    WHERE room_id = COALESCE(NEW.room_id, OLD.room_id) AND is_online = TRUE
  )
  WHERE id = COALESCE(NEW.room_id, OLD.room_id);
  
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_viewers ON public.room_users;
CREATE TRIGGER trigger_update_viewers
  AFTER INSERT OR UPDATE OR DELETE ON public.room_users
  FOR EACH ROW EXECUTE FUNCTION update_viewers_count();

-- ============================================
-- 7. HABILITAR REALTIME
-- ============================================

DO $$
BEGIN
  ALTER PUBLICATION supabase_realtime ADD TABLE public.game_rooms;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  ALTER PUBLICATION supabase_realtime ADD TABLE public.room_users;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  ALTER PUBLICATION supabase_realtime ADD TABLE public.room_messages;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  ALTER PUBLICATION supabase_realtime ADD TABLE public.room_reactions;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================
-- PRONTO! Verificar salas criadas
-- ============================================

SELECT id, home_team, away_team, status, minute, viewers_count 
FROM public.game_rooms 
ORDER BY status, start_time;
