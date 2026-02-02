-- =============================================
-- VERSÃO SIMPLIFICADA: WEBHOOK PARA CRON
-- =============================================

-- Como a Edge Function pode não estar deployada, 
-- vamos criar uma função que pode ser chamada via HTTP

-- Função que pode ser executada via webhook
CREATE OR REPLACE FUNCTION public.daily_trial_check()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
    total_users integer;
    expired_count integer;
    active_count integer;
BEGIN
    -- Executar verificação de expiração
    PERFORM check_trial_expiration();
    
    -- Obter estatísticas
    SELECT COUNT(*) INTO total_users
    FROM profiles 
    WHERE trial_start IS NOT NULL;
    
    SELECT COUNT(*) INTO expired_count
    FROM profiles 
    WHERE trial_expired = true;
    
    active_count := total_users - expired_count;
    
    -- Retornar resultado
    result := json_build_object(
        'success', true,
        'message', 'Trial check completed successfully',
        'timestamp', NOW(),
        'stats', json_build_object(
            'totalUsers', total_users,
            'activeTrials', active_count,
            'expiredUsers', expired_count
        )
    );
    
    RETURN result;
END;
$$;

-- Permitir acesso público à função (para webhooks)
GRANT EXECUTE ON FUNCTION public.daily_trial_check() TO anon;
GRANT EXECUTE ON FUNCTION public.daily_trial_check() TO authenticated;

-- URL para chamada via webhook:
-- https://mzamszcpbverpadjelck.supabase.co/rest/v1/rpc/daily_trial_check

COMMENT ON FUNCTION public.daily_trial_check() IS 'Função para verificação diária de trials via webhook';