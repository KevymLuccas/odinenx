// Supabase Edge Function: process-alerts
// Processa alertas em tempo real e dispara notificações

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.4"

const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const supabase = createClient(supabaseUrl, supabaseServiceKey)

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('🔔 Processando alertas...')
    
    // 1. Buscar alertas ativos
    const { data: alerts, error: alertsError } = await supabase
      .from('alerts_config')
      .select('*')
      .eq('is_active', true)
    
    if (alertsError) {
      console.error('Erro ao buscar alertas:', alertsError)
      throw alertsError
    }
    
    console.log(`📊 ${alerts.length} alertas ativos encontrados`)
    
    let alertsTriggered = 0
    
    // 2. Processar cada alerta
    for (const alert of alerts) {
      try {
        const currentPrice = await getCurrentPrice(alert.type, alert.symbol)
        
        if (currentPrice === null) {
          console.log(`⚠️ Preço não encontrado para ${alert.symbol}`)
          continue
        }
        
        // Atualizar valor atual
        await supabase
          .from('alerts_config')
          .update({ 
            current_value: currentPrice,
            updated_at: new Date().toISOString()
          })
          .eq('id', alert.id)
        
        // Verificar condição
        const shouldTrigger = checkAlertCondition(alert, currentPrice)
        
        if (shouldTrigger) {
          await triggerAlert(alert, currentPrice)
          alertsTriggered++
          console.log(`🚨 Alerta disparado: ${alert.name} - ${alert.symbol} = ${currentPrice}`)
        }
        
      } catch (error) {
        console.error(`Erro ao processar alerta ${alert.id}:`, error)
      }
    }
    
    console.log(`✅ Processamento concluído. ${alertsTriggered} alertas disparados`)
    
    return new Response(
      JSON.stringify({ 
        success: true, 
        alertsProcessed: alerts.length,
        alertsTriggered,
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )
    
  } catch (error) {
    console.error('Erro no processamento de alertas:', error)
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        timestamp: new Date().toISOString()
      }),
      { 
        status: 500, 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )
  }
})

// ===== FUNÇÕES AUXILIARES =====

async function getCurrentPrice(type: string, symbol: string): Promise<number | null> {
  try {
    const baseUrl = 'https://odinenx.vercel.app'
    
    // Mapear tipo para endpoint da API
    const typeMap: { [key: string]: string } = {
      crypto: 'crypto',
      stock: 'acoes',
      forex: 'forex',
      bet: 'football' // Não tem preço, mas pode ter odds
    }
    
    if (type === 'bet') {
      // Para apostas, não temos "preço" mas podemos usar odds
      // Por enquanto retornar null para BET
      return null
    }
    
    const apiType = typeMap[type]
    if (!apiType) return null
    
    const response = await fetch(`${baseUrl}/api/market?type=${apiType}`)
    const data = await response.json()
    
    if (!data.success || !data.data) {
      return null
    }
    
    // Procurar o símbolo nos dados
    const item = data.data.find((d: any) => 
      d.simbolo?.toUpperCase() === symbol.toUpperCase()
    )
    
    return item?.preco || null
    
  } catch (error) {
    console.error(`Erro ao buscar preço ${type}/${symbol}:`, error)
    return null
  }
}

function checkAlertCondition(alert: any, currentPrice: number): boolean {
  const condition = alert.condition
  const targetValue = parseFloat(alert.target_value)
  
  switch (condition) {
    case 'price_above':
      return currentPrice > targetValue
      
    case 'price_below':
      return currentPrice < targetValue
      
    case 'price_change_up':
      // Variação percentual positiva (precisa do preço anterior)
      const changeUp = ((currentPrice - alert.current_value) / alert.current_value) * 100
      return changeUp >= targetValue
      
    case 'price_change_down':
      // Variação percentual negativa
      const changeDown = ((alert.current_value - currentPrice) / alert.current_value) * 100
      return changeDown >= targetValue
      
    default:
      return false
  }
}

async function triggerAlert(alert: any, triggeredValue: number) {
  try {
    // Gerar mensagem
    const message = generateAlertMessage(alert, triggeredValue)
    
    // 1. Salvar no histórico
    const { error: historyError } = await supabase
      .from('alerts_history')
      .insert([{
        alert_id: alert.id,
        user_id: alert.user_id,
        symbol: alert.symbol,
        condition: alert.condition,
        target_value: alert.target_value,
        triggered_value: triggeredValue,
        message: message
      }])
    
    if (historyError) {
      console.error('Erro ao salvar histórico:', historyError)
    }
    
    // 2. Atualizar contador do alerta
    await supabase
      .from('alerts_config')
      .update({
        triggered_count: (alert.triggered_count || 0) + 1,
        last_triggered_at: new Date().toISOString()
      })
      .eq('id', alert.id)
    
    // 3. TODO: Enviar notificação push (implementar depois)
    console.log(`📧 Notificação enviada para usuário ${alert.user_id}: ${message}`)
    
  } catch (error) {
    console.error('Erro ao disparar alerta:', error)
  }
}

function generateAlertMessage(alert: any, triggeredValue: number): string {
  const symbol = alert.symbol
  const condition = alert.condition
  const targetValue = parseFloat(alert.target_value)
  
  // Formatar valor
  const formatValue = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value)
  }
  
  switch (condition) {
    case 'price_above':
      return `🚨 ${symbol} ultrapassou ${formatValue(targetValue)}! Preço atual: ${formatValue(triggeredValue)}`
      
    case 'price_below':
      return `📉 ${symbol} caiu abaixo de ${formatValue(targetValue)}! Preço atual: ${formatValue(triggeredValue)}`
      
    case 'price_change_up':
      return `📈 ${symbol} subiu ${targetValue}%! Preço atual: ${formatValue(triggeredValue)}`
      
    case 'price_change_down':
      return `📉 ${symbol} caiu ${targetValue}%! Preço atual: ${formatValue(triggeredValue)}`
      
    default:
      return `🔔 Alerta ${alert.name} disparado para ${symbol}`
  }
}