#!/bin/bash

# =============================================
# SCRIPT COMPLETO PARA CONFIGURAR CRON DO TRIAL
# =============================================

echo "🕐 CONFIGURANDO SISTEMA DE CRON PARA VERIFICAÇÃO DE TRIALS"
echo "=========================================================="

# 1. Deploy da Edge Function no Supabase
echo ""
echo "1️⃣ DEPLOY DA EDGE FUNCTION:"
echo "Execute no terminal do Supabase CLI:"
echo ""
echo "supabase functions deploy check-trial --project-ref mzamszcpbverpadjelck"
echo ""

# 2. Configuração do GitHub Actions
echo "2️⃣ GITHUB ACTIONS (AUTOMÁTICO):"
echo "• Arquivo criado: .github/workflows/check-trials.yml"
echo "• Executa diariamente às 00:00 UTC"
echo "• NENHUMA configuração adicional necessária!"
echo ""

# 3. Alternativa com CRON-JOB.ORG
echo "3️⃣ CRON-JOB.ORG (MANUAL):"
echo "• Acesse: https://cron-job.org"
echo "• Crie conta gratuita"
echo "• Configure job com:"
echo "  - URL: https://mzamszcpbverpadjelck.supabase.co/functions/v1/check-trial"
echo "  - Method: POST"
echo "  - Schedule: 0 0 * * * (diário)"
echo "  - Header: Authorization: Bearer [SUPABASE_KEY]"
echo ""

# 4. SQL Cron no Supabase
echo "4️⃣ SUPABASE SQL CRON:"
echo "• Execute 008_cron_job_setup.sql no Supabase SQL Editor"
echo "• Requer plano pago (pg_cron extension)"
echo ""

echo "=========================================================="
echo "🎯 RECOMENDAÇÃO: Use GitHub Actions (opção 2)"
echo "   ✅ Gratuito"
echo "   ✅ Confiável" 
echo "   ✅ Já configurado"
echo "   ✅ Logs visíveis"
echo ""
echo "🌐 Monitore execuções em:"
echo "   https://github.com/KevymLuccas/odinenx/actions"