-- =============================================
-- PAPER TRADING - Sistema de Simulação
-- =============================================

-- Tabela de carteira virtual
CREATE TABLE IF NOT EXISTS paper_wallet (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  balance DECIMAL(15,2) DEFAULT 10000.00, -- Saldo inicial R$ 10.000
  total_invested DECIMAL(15,2) DEFAULT 0,
  total_profit DECIMAL(15,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de operações (trades)
CREATE TABLE IF NOT EXISTS paper_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol VARCHAR(20) NOT NULL, -- PETR4, BTCUSDT, USDBRL, etc
  type VARCHAR(10) NOT NULL, -- crypto, stock, forex
  action VARCHAR(4) NOT NULL, -- BUY, SELL
  quantity DECIMAL(15,8) NOT NULL,
  price DECIMAL(15,8) NOT NULL,
  total DECIMAL(15,2) NOT NULL, -- quantity * price
  status VARCHAR(10) DEFAULT 'open', -- open, closed
  entry_reason TEXT,
  exit_reason TEXT,
  profit_loss DECIMAL(15,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  closed_at TIMESTAMPTZ NULL
);

-- Tabela de posições em aberto
CREATE TABLE IF NOT EXISTS paper_positions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol VARCHAR(20) NOT NULL,
  type VARCHAR(10) NOT NULL, -- crypto, stock, forex
  quantity DECIMAL(15,8) NOT NULL,
  avg_price DECIMAL(15,8) NOT NULL,
  current_price DECIMAL(15,8) DEFAULT 0,
  market_value DECIMAL(15,2) DEFAULT 0,
  profit_loss DECIMAL(15,2) DEFAULT 0,
  profit_loss_pct DECIMAL(5,2) DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, symbol, type)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_paper_wallet_user ON paper_wallet(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_user ON paper_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol ON paper_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_paper_positions_user ON paper_positions(user_id);

-- RLS (Row Level Security)
ALTER TABLE paper_wallet ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_positions ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own paper wallet" ON paper_wallet FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own paper wallet" ON paper_wallet FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own paper wallet" ON paper_wallet FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own trades" ON paper_trades FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own trades" ON paper_trades FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own trades" ON paper_trades FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own positions" ON paper_positions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own positions" ON paper_positions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own positions" ON paper_positions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own positions" ON paper_positions FOR DELETE USING (auth.uid() = user_id);

-- Função para criar carteira inicial
CREATE OR REPLACE FUNCTION create_initial_paper_wallet()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO paper_wallet (user_id, balance)
  VALUES (NEW.id, 10000.00)
  ON CONFLICT (user_id) DO NOTHING;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para criar carteira quando usuário se cadastra
DROP TRIGGER IF EXISTS on_auth_user_created_paper_wallet ON auth.users;
CREATE TRIGGER on_auth_user_created_paper_wallet
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION create_initial_paper_wallet();

-- Comentários
COMMENT ON TABLE paper_wallet IS 'Carteira virtual para simulação de trading';
COMMENT ON TABLE paper_trades IS 'Histórico de todas as operações simuladas';
COMMENT ON TABLE paper_positions IS 'Posições atualmente em aberto';