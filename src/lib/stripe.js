import { loadStripe } from '@stripe/stripe-js'
import { supabase } from './supabase'

// Stripe instance
let stripePromise = null

export const getStripe = () => {
  if (!stripePromise) {
    stripePromise = loadStripe('pk_live_51SvLiVD3mufAbT6c8d9o66HLbOmyOsmFdhpqT3GAWXy6ywAkzXHtYW8weaqcKny0f9xRKynkL7o8JasAjmQR95O300z07aKdK6')
  }
  return stripePromise
}

// Planos disponíveis
export const plans = {
  free: {
    id: 'free',
    name: 'Free',
    price: 0,
    interval: 'month',
    features: [
      '3 análises por dia',
      'Dashboard básico',
      'Histórico 7 dias'
    ],
    limits: {
      analysisPerDay: 3,
      historyDays: 7
    }
  },
  basic: {
    id: 'basic',
    name: 'Basic',
    price: 79,
    interval: 'month',
    stripePriceId: 'price_1SvMedD3mufAbT6c994DmZYw',
    features: [
      'Análises ilimitadas',
      'Dashboard completo',
      'Histórico 30 dias',
      'Filtros de risco'
    ],
    limits: {
      analysisPerDay: -1,
      historyDays: 30
    }
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    price: 199,
    interval: 'month',
    stripePriceId: 'price_1SvMehD3mufAbT6cmjXFFHtA',
    popular: true,
    features: [
      'Tudo do Basic',
      'Cartola FC',
      'Histórico 90 dias',
      'Paper Trading',
      'Sistema de Alertas',
      'Suporte prioritário'
    ],
    limits: {
      analysisPerDay: -1,
      historyDays: 90,
      paperTrading: true,
      cartola: true,
      alerts: true
    }
  },
  elite: {
    id: 'elite',
    name: 'Elite',
    price: 399,
    interval: 'month',
    stripePriceId: 'price_1SvMemD3mufAbT6cRHEhLdAM',
    features: [
      'Tudo do Pro',
      'Histórico ilimitado',
      'Painel Administrativo',
      'Relatórios avançados',
      'Suporte prioritário'
    ],
    limits: {
      analysisPerDay: -1,
      historyDays: -1,
      paperTrading: true,
      cartola: true,
      alerts: true,
      admin: true,
      reports: true
    }
  }
}

// Mapeamento de price_id para plan_id
export const priceIdToPlan = {
  'price_1SvMedD3mufAbT6c994DmZYw': 'basic',
  'price_1SvMehD3mufAbT6cmjXFFHtA': 'pro',
  'price_1SvMemD3mufAbT6cRHEhLdAM': 'elite'
}

// Verificar se usuário tem acesso a um recurso específico
export const hasAccess = async (subscription, feature, userId = null) => {
  const planId = subscription?.plan || 'free'
  const plan = plans[planId] || plans.free
  
  // Para usuários free, verificar se trial expirou
  if (planId === 'free' && userId) {
    const trialStatus = await getTrialStatus(userId)
    if (trialStatus.expired) {
      // Trial expirado: só pode acessar páginas básicas
      return ['bet'].includes(feature)
    }
  }
  
  // Verificar limites específicos
  switch (feature) {
    case 'bet':
      return true // Todos podem acessar BET básico
    case 'trade':
      return ['pro', 'elite'].includes(planId) // Só Pro/Elite
    case 'cartola':
      return plan.limits?.cartola === true // Só Pro/Elite
    case 'alerts':
      return plan.limits?.alerts === true // Só Pro/Elite
    case 'paperTrading':
      return plan.limits?.paperTrading === true // Só Pro/Elite
    case 'admin':
      return plan.limits?.admin === true // Só Elite
    case 'analysisUnlimited':
      return plan.limits?.analysisPerDay === -1 // Basic+
    case 'fullHistory':
      return plan.limits?.historyDays === -1 // Elite
    case 'iaAvancada':
      return ['pro', 'elite'].includes(planId)
    default:
      return false
  }
}

// Versão síncrona para compatibilidade (sem verificação de trial)
export const hasAccessSync = (subscription, feature) => {
  const planId = subscription?.plan || 'free'
  const plan = plans[planId] || plans.free
  
  switch (feature) {
    case 'bet':
      return true
    case 'trade':
      return ['pro', 'elite'].includes(planId)
    case 'cartola':
      return plan.limits?.cartola === true
    case 'alerts':
      return plan.limits?.alerts === true
    case 'paperTrading':
      return plan.limits?.paperTrading === true
    case 'admin':
      return plan.limits?.admin === true
    case 'analysisUnlimited':
      return plan.limits?.analysisPerDay === -1
    case 'fullHistory':
      return plan.limits?.historyDays === -1
    case 'iaAvancada':
      return ['pro', 'elite'].includes(planId)
    default:
      return false
  }
}

// Verificar status do trial de 3 dias
export const getTrialStatus = async (userId) => {
  try {
    // Buscar dados do trial na tabela profiles
    const { data: profile, error } = await supabase
      .from('profiles')
      .select('trial_start, trial_used_days, trial_expired, created_at')
      .eq('id', userId)
      .single()
    
    if (error && error.code === 'PGRST116') {
      // Profile não existe, criar um novo
      const { data: newProfile, error: insertError } = await supabase
        .from('profiles')
        .insert([{
          id: userId,
          trial_start: new Date().toISOString().split('T')[0],
          trial_used_days: 0,
          trial_expired: false
        }])
        .select()
        .single()
      
      if (insertError) {
        console.error('Erro ao criar profile:', insertError)
        return { daysRemaining: 3, expired: false, startDate: new Date().toISOString() }
      }
      
      return {
        daysRemaining: 3,
        expired: false,
        startDate: newProfile.trial_start,
        daysUsed: 0
      }
    }
    
    if (error) {
      console.error('Erro ao buscar profile:', error)
      return { daysRemaining: 0, expired: true, startDate: null }
    }
    
    // Calcular dias baseado nos dados do banco
    const startDate = new Date(profile.trial_start)
    const currentDate = new Date()
    const diffTime = currentDate.getTime() - startDate.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    const daysRemaining = Math.max(0, 3 - diffDays)
    const expired = profile.trial_expired || diffDays >= 3
    
    return {
      daysRemaining,
      expired,
      startDate: profile.trial_start,
      daysUsed: Math.min(diffDays, 3)
    }
    
  } catch (error) {
    console.error('Erro ao verificar trial:', error)
    return { daysRemaining: 0, expired: true, startDate: null }
  }
}

// Calcular dias restantes do trial
const calculateTrialDays = (createdAt) => {
  const startDate = new Date(createdAt)
  const currentDate = new Date()
  const diffTime = currentDate.getTime() - startDate.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  const daysRemaining = Math.max(0, 3 - diffDays)
  const expired = diffDays >= 3
  
  return {
    daysRemaining,
    expired,
    startDate: createdAt,
    daysUsed: Math.min(diffDays, 3)
  }
}

// Verificar limite de análises por dia
export const checkAnalysisLimit = async (userId, subscription) => {
  const planId = subscription?.plan || 'free'
  const plan = plans[planId] || plans.free
  
  // Verificar trial para usuários free
  if (planId === 'free') {
    const trialStatus = await getTrialStatus(userId)
    if (trialStatus.expired) {
      return {
        allowed: false,
        remaining: 0,
        limit: 0,
        trialExpired: true,
        message: 'Trial de 3 dias expirado. Assine um plano para continuar.'
      }
    }
  }
  
  if (plan.limits.analysisPerDay === -1) {
    return { allowed: true, remaining: -1 }
  }
  
  // Para plano Free, verificar uso do dia
  const today = new Date().toISOString().split('T')[0]
  const storageKey = `analysis_count_${userId}_${today}`
  const count = parseInt(localStorage.getItem(storageKey) || '0')
  
  return {
    allowed: count < plan.limits.analysisPerDay,
    remaining: plan.limits.analysisPerDay - count,
    limit: plan.limits.analysisPerDay
  }
}

// Incrementar contagem de análises
export const incrementAnalysisCount = (userId) => {
  const today = new Date().toISOString().split('T')[0]
  const storageKey = `analysis_count_${userId}_${today}`
  const count = parseInt(localStorage.getItem(storageKey) || '0')
  localStorage.setItem(storageKey, (count + 1).toString())
}

// Criar checkout session via Supabase Edge Function
export const createCheckoutSession = async (planId, userId, userEmail) => {
  try {
    const plan = plans[planId]
    if (!plan || !plan.stripePriceId) {
      throw new Error('Plano inválido')
    }

    const { data, error } = await supabase.functions.invoke('create-checkout', {
      body: {
        priceId: plan.stripePriceId,
        userId: userId,
        userEmail: userEmail,
        planId: planId
      }
    })

    if (error) throw error
    return data
  } catch (error) {
    console.error('Erro ao criar checkout:', error)
    throw error
  }
}

// Redirecionar para checkout do Stripe
export const redirectToCheckout = async (planId) => {
  try {
    const { data: { user } } = await supabase.auth.getUser()
    
    if (!user) {
      throw new Error('Usuário não autenticado')
    }

    const data = await createCheckoutSession(planId, user.id, user.email)
    
    // Usar redirecionamento direto para a URL (novo método)
    if (data.url) {
      window.location.href = data.url
    } else {
      throw new Error('URL de checkout não retornada')
    }
  } catch (error) {
    console.error('Erro no checkout:', error)
    throw error
  }
}

// Portal do cliente para gerenciar assinatura
export const createCustomerPortal = async () => {
  try {
    const { data, error } = await supabase.functions.invoke('customer-portal', {
      body: {}
    })

    if (error) throw error
    window.location.href = data.url
  } catch (error) {
    console.error('Erro ao abrir portal:', error)
    throw error
  }
}

// Verificar status da assinatura do usuário
export const getSubscriptionStatus = async (userId) => {
  try {
    const { data, error } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'active')
      .maybeSingle()

    // Ignora erros de tabela não existente ou sem dados
    if (error && error.code !== 'PGRST116' && error.code !== '42P01' && error.code !== 'PGRST301') {
      console.warn('Aviso subscriptions:', error.code)
    }
    return data || { plan: 'free', status: 'active' }
  } catch (error) {
    // Silencia erros - retorna plano free
    return { plan: 'free', status: 'active' }
  }
}

// Cancelar assinatura
export const cancelSubscription = async () => {
  try {
    const { data, error } = await supabase.functions.invoke('cancel-subscription', {
      body: {}
    })

    if (error) throw error
    return data
  } catch (error) {
    console.error('Erro ao cancelar:', error)
    throw error
  }
}
