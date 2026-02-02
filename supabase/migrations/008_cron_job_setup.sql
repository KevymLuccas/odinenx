-- =============================================
-- CONFIGURAÇÃO DE CRON JOB PARA VERIFICAÇÃO DE TRIAL
-- =============================================

-- Habilitar extensão pg_cron (se não estiver habilitada)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Agendar verificação diária às 00:00 UTC (21:00 Brasil)
SELECT cron.schedule(
  'daily-trial-check', -- nome do job
  '0 0 * * *',        -- todo dia à meia-noite UTC
  'SELECT check_trial_expiration();' -- função a executar
);

-- Verificar jobs agendados
SELECT * FROM cron.job;

-- =============================================
-- ALTERNATIVA: HTTP CRON com Edge Function
-- =============================================

-- Como o Supabase pode não ter pg_cron no plano gratuito,
-- também podemos usar serviços externos como:
-- 1. GitHub Actions (scheduled workflow)
-- 2. Vercel Cron Jobs
-- 3. Cron-job.org
-- 4. EasyCron

-- URL da Edge Function para chamada HTTP:
-- https://mzamszcpbverpadjelck.supabase.co/functions/v1/check-trial

-- Headers necessários:
-- Authorization: Bearer [SUPABASE_ANON_KEY]
-- Content-Type: application/json