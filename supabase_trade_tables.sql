-- =====================================================
-- TABELAS DO MÓDULO TRADE - ODINENX
-- Execute este SQL no Supabase SQL Editor
-- =====================================================

-- 1. TABELA DE OPERAÇÕES DE TRADE
CREATE TABLE IF NOT EXISTS trade_operacoes (
  id BIGINT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('COMPRA', 'VENDA')),
  ativo VARCHAR(20) NOT NULL,
  categoria VARCHAR(20) NOT NULL CHECK (categoria IN ('crypto', 'acoes', 'forex')),
  preco_entrada DECIMAL(20, 8) NOT NULL,
  preco_saida DECIMAL(20, 8),
  quantidade DECIMAL(20, 8) NOT NULL,
  stop_loss DECIMAL(20, 8),
  take_profit DECIMAL(20, 8),
  plataforma VARCHAR(50),
  status VARCHAR(20) DEFAULT 'ABERTA' CHECK (status IN ('ABERTA', 'FECHADA')),
  resultado DECIMAL(20, 2) DEFAULT 0,
  observacao TEXT,
  data TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_trade_operacoes_user ON trade_operacoes(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_operacoes_status ON trade_operacoes(status);
CREATE INDEX IF NOT EXISTS idx_trade_operacoes_data ON trade_operacoes(data DESC);
CREATE INDEX IF NOT EXISTS idx_trade_operacoes_categoria ON trade_operacoes(categoria);

-- RLS (Row Level Security) - Cada usuário só vê suas operações
ALTER TABLE trade_operacoes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own operations" ON trade_operacoes;
CREATE POLICY "Users can view own operations" ON trade_operacoes
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own operations" ON trade_operacoes;
CREATE POLICY "Users can insert own operations" ON trade_operacoes
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own operations" ON trade_operacoes;
CREATE POLICY "Users can update own operations" ON trade_operacoes
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own operations" ON trade_operacoes;
CREATE POLICY "Users can delete own operations" ON trade_operacoes
  FOR DELETE USING (auth.uid() = user_id);


-- 2. TABELA DE CONFIGURAÇÃO DE RISCO
CREATE TABLE IF NOT EXISTS trade_config_risco (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  capital_total DECIMAL(20, 2) DEFAULT 10000,
  risco_por_operacao DECIMAL(5, 2) DEFAULT 2,
  max_operacoes_dia INTEGER DEFAULT 5,
  max_perda_dia DECIMAL(5, 2) DEFAULT 5,
  alavancagem_max INTEGER DEFAULT 10,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS para config de risco
ALTER TABLE trade_config_risco ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own config" ON trade_config_risco;
CREATE POLICY "Users can view own config" ON trade_config_risco
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own config" ON trade_config_risco;
CREATE POLICY "Users can insert own config" ON trade_config_risco
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own config" ON trade_config_risco;
CREATE POLICY "Users can update own config" ON trade_config_risco
  FOR UPDATE USING (auth.uid() = user_id);


-- 3. TABELA DE DIÁRIO DE TRADING (opcional, para notas do dia)
CREATE TABLE IF NOT EXISTS trade_diario (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  data DATE NOT NULL,
  nota TEXT,
  humor VARCHAR(20),
  aprendizados TEXT,
  erros TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, data)
);

-- RLS para diário
ALTER TABLE trade_diario ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own diary" ON trade_diario;
CREATE POLICY "Users can manage own diary" ON trade_diario
  FOR ALL USING (auth.uid() = user_id);


-- =====================================================
-- VERIFICAÇÃO
-- =====================================================
SELECT 'Tabelas criadas com sucesso!' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'trade_%';
