-- =============================================
-- ODINENX - Adicionar coluna plan às subscriptions
-- Execute no SQL Editor do Supabase
-- =============================================

-- Adicionar coluna plan se não existir
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'subscriptions' AND column_name = 'plan'
  ) THEN
    ALTER TABLE public.subscriptions ADD COLUMN plan TEXT DEFAULT 'basic';
  END IF;
END $$;

-- Atualizar registros existentes baseado no price_id
UPDATE public.subscriptions 
SET plan = CASE 
  WHEN price_id = 'price_1SvMedD3mufAbT6c994DmZYw' THEN 'basic'
  WHEN price_id = 'price_1SvMehD3mufAbT6cmjXFFHtA' THEN 'pro'
  WHEN price_id = 'price_1SvMemD3mufAbT6cRHEhLdAM' THEN 'elite'
  ELSE 'basic'
END
WHERE plan IS NULL OR plan = 'basic';

-- Verificar a estrutura
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'subscriptions';
