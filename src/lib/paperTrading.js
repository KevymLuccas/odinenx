// =============================================
// PAPER TRADING - Sistema de Simulação 
// =============================================

import { supabase } from './supabase'

// ===== CARTEIRA VIRTUAL =====
export const getPaperWallet = async (userId) => {
  try {
    let { data, error } = await supabase
      .from('paper_wallet')
      .select('*')
      .eq('user_id', userId)
      .single()
    
    // Se não existe, criar carteira inicial
    if (error && error.code === 'PGRST116') {
      const { data: newWallet, error: createError } = await supabase
        .from('paper_wallet')
        .insert([{ user_id: userId, balance: 10000.00 }])
        .select()
        .single()
      
      if (createError) throw createError
      return newWallet
    }
    
    if (error) throw error
    return data
    
  } catch (error) {
    console.error('Erro ao carregar carteira:', error)
    throw error
  }
}

// ===== POSIÇÕES EM ABERTO =====
export const getPaperPositions = async (userId) => {
  try {
    const { data, error } = await supabase
      .from('paper_positions')
      .select('*')
      .eq('user_id', userId)
      .order('updated_at', { ascending: false })
    
    if (error) throw error
    return data || []
    
  } catch (error) {
    console.error('Erro ao carregar posições:', error)
    return []
  }
}

// ===== HISTÓRICO DE TRADES =====
export const getPaperTrades = async (userId, limit = 50) => {
  try {
    const { data, error } = await supabase
      .from('paper_trades')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(limit)
    
    if (error) throw error
    return data || []
    
  } catch (error) {
    console.error('Erro ao carregar trades:', error)
    return []
  }
}

// ===== EXECUTAR COMPRA =====
export const executeBuy = async (userId, { symbol, type, quantity, price, reason = '' }) => {
  try {
    // 1. Verificar saldo
    const wallet = await getPaperWallet(userId)
    const total = parseFloat(quantity) * parseFloat(price)
    
    if (wallet.balance < total) {
      throw new Error(`Saldo insuficiente. Necessário: R$ ${total.toFixed(2)}, Disponível: R$ ${wallet.balance.toFixed(2)}`)
    }
    
    // 2. Registrar trade
    const { data: trade, error: tradeError } = await supabase
      .from('paper_trades')
      .insert([{
        user_id: userId,
        symbol,
        type,
        action: 'BUY',
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        total,
        entry_reason: reason
      }])
      .select()
      .single()
    
    if (tradeError) throw tradeError
    
    // 3. Atualizar saldo
    const { error: walletError } = await supabase
      .from('paper_wallet')
      .update({ 
        balance: wallet.balance - total,
        total_invested: wallet.total_invested + total,
        updated_at: new Date().toISOString()
      })
      .eq('user_id', userId)
    
    if (walletError) throw walletError
    
    // 4. Atualizar/criar posição
    const existingPosition = await supabase
      .from('paper_positions')
      .select('*')
      .eq('user_id', userId)
      .eq('symbol', symbol)
      .eq('type', type)
      .single()
    
    if (existingPosition.data) {
      // Posição existente - calcular nova média
      const pos = existingPosition.data
      const newQuantity = pos.quantity + parseFloat(quantity)
      const newAvgPrice = ((pos.quantity * pos.avg_price) + total) / newQuantity
      
      await supabase
        .from('paper_positions')
        .update({
          quantity: newQuantity,
          avg_price: newAvgPrice,
          updated_at: new Date().toISOString()
        })
        .eq('id', pos.id)
        
    } else {
      // Nova posição
      await supabase
        .from('paper_positions')
        .insert([{
          user_id: userId,
          symbol,
          type,
          quantity: parseFloat(quantity),
          avg_price: parseFloat(price),
          current_price: parseFloat(price)
        }])
    }
    
    return trade
    
  } catch (error) {
    console.error('Erro ao executar compra:', error)
    throw error
  }
}

// ===== EXECUTAR VENDA =====
export const executeSell = async (userId, { symbol, type, quantity, price, reason = '' }) => {
  try {
    // 1. Verificar posição
    const { data: position, error: posError } = await supabase
      .from('paper_positions')
      .select('*')
      .eq('user_id', userId)
      .eq('symbol', symbol)
      .eq('type', type)
      .single()
    
    if (posError || !position) {
      throw new Error(`Posição não encontrada para ${symbol}`)
    }
    
    if (position.quantity < parseFloat(quantity)) {
      throw new Error(`Quantidade insuficiente. Disponível: ${position.quantity}, Solicitado: ${quantity}`)
    }
    
    // 2. Calcular lucro/prejuízo
    const sellTotal = parseFloat(quantity) * parseFloat(price)
    const buyTotal = parseFloat(quantity) * position.avg_price
    const profitLoss = sellTotal - buyTotal
    
    // 3. Registrar trade
    const { data: trade, error: tradeError } = await supabase
      .from('paper_trades')
      .insert([{
        user_id: userId,
        symbol,
        type,
        action: 'SELL',
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        total: sellTotal,
        profit_loss: profitLoss,
        exit_reason: reason
      }])
      .select()
      .single()
    
    if (tradeError) throw tradeError
    
    // 4. Atualizar saldo e lucro total
    const wallet = await getPaperWallet(userId)
    await supabase
      .from('paper_wallet')
      .update({ 
        balance: wallet.balance + sellTotal,
        total_profit: wallet.total_profit + profitLoss,
        updated_at: new Date().toISOString()
      })
      .eq('user_id', userId)
    
    // 5. Atualizar posição
    const remainingQuantity = position.quantity - parseFloat(quantity)
    
    if (remainingQuantity <= 0.00001) {
      // Fechar posição completamente
      await supabase
        .from('paper_positions')
        .delete()
        .eq('id', position.id)
    } else {
      // Reduzir quantidade
      await supabase
        .from('paper_positions')
        .update({
          quantity: remainingQuantity,
          updated_at: new Date().toISOString()
        })
        .eq('id', position.id)
    }
    
    return trade
    
  } catch (error) {
    console.error('Erro ao executar venda:', error)
    throw error
  }
}

// ===== ATUALIZAR PREÇOS DAS POSIÇÕES =====
export const updatePositionPrices = async (userId) => {
  try {
    const positions = await getPaperPositions(userId)
    
    for (const position of positions) {
      let currentPrice = 0
      
      // Buscar preço atual baseado no tipo
      try {
        const response = await fetch(`/api/market?type=${position.type}`)
        const data = await response.json()
        
        if (data.success) {
          const item = data.data.find(d => 
            d.simbolo?.toUpperCase() === position.symbol.toUpperCase()
          )
          
          if (item) {
            currentPrice = item.preco || 0
            
            const marketValue = position.quantity * currentPrice
            const profitLoss = marketValue - (position.quantity * position.avg_price)
            const profitLossPct = ((currentPrice - position.avg_price) / position.avg_price) * 100
            
            // Atualizar posição
            await supabase
              .from('paper_positions')
              .update({
                current_price: currentPrice,
                market_value: marketValue,
                profit_loss: profitLoss,
                profit_loss_pct: profitLossPct,
                updated_at: new Date().toISOString()
              })
              .eq('id', position.id)
          }
        }
      } catch (error) {
        console.error(`Erro ao atualizar preço de ${position.symbol}:`, error)
      }
    }
    
  } catch (error) {
    console.error('Erro ao atualizar preços:', error)
  }
}

// ===== ESTATÍSTICAS =====
export const getPaperStats = async (userId) => {
  try {
    const [wallet, positions, trades] = await Promise.all([
      getPaperWallet(userId),
      getPaperPositions(userId),
      getPaperTrades(userId, 1000)
    ])
    
    // Calcular patrimônio total
    const positionsValue = positions.reduce((acc, pos) => acc + (pos.market_value || 0), 0)
    const totalPortfolio = wallet.balance + positionsValue
    
    // Trades stats
    const totalTrades = trades.length
    const buyTrades = trades.filter(t => t.action === 'BUY').length
    const sellTrades = trades.filter(t => t.action === 'SELL').length
    const profitableTrades = trades.filter(t => t.action === 'SELL' && t.profit_loss > 0).length
    const winRate = sellTrades > 0 ? (profitableTrades / sellTrades) * 100 : 0
    
    // Lucro/prejuízo não realizado
    const unrealizedPL = positions.reduce((acc, pos) => acc + (pos.profit_loss || 0), 0)
    
    return {
      balance: wallet.balance,
      totalPortfolio,
      positionsValue,
      totalInvested: wallet.total_invested,
      totalProfit: wallet.total_profit,
      unrealizedPL,
      totalReturn: ((totalPortfolio - 10000) / 10000) * 100,
      totalTrades,
      buyTrades,
      sellTrades,
      winRate,
      openPositions: positions.length
    }
    
  } catch (error) {
    console.error('Erro ao calcular estatísticas:', error)
    return null
  }
}