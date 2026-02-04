/**
 * 📝 Tipos do ODINENX v2.0
 * Definições TypeScript para o sistema de salas ao vivo
 */

// Planos
export type PlanId = 'free' | 'basic' | 'pro' | 'elite'

export interface Plan {
  id: PlanId
  name: string
  price: number
  priceId: string
  features: string[]
  limits: {
    analyses: number | 'unlimited'
    historyDays: number | 'unlimited'
    dashboard: 'basic' | 'full'
    aiAdvanced: boolean
    alerts: boolean
    paperTrading: boolean
    cartola: boolean
    priority: boolean
  }
  v2: {
    gifs: boolean
    stickers: boolean
    salasPrivadas: number
    celebracao: 'basic' | 'confetti' | 'confetti_stars' | 'full'
    loja: boolean
  }
  badgeEmoji?: string
  popular?: boolean
}

// Usuário
export interface User {
  id: string
  email: string
  username: string
  plan: PlanId
  avatar_url?: string
  created_at: string
}

// Sala de Jogo
export interface GameRoom {
  id: string
  fixture_id: number
  home_team: string
  away_team: string
  home_logo?: string
  away_logo?: string
  home_score: number
  away_score: number
  minute: number
  status: 'scheduled' | 'live' | 'halftime' | 'finished' | 'postponed'
  league: string
  is_private: boolean
  private_code?: string
  owner_id?: string
  max_users: number
  created_at: string
}

// Usuário na Sala
export interface RoomUser {
  id: string
  room_id: string
  user_id: string
  username: string
  plan: PlanId
  avatar_url?: string
  joined_at: string
  is_online: boolean
}

// Mensagem do Chat
export interface RoomMessage {
  id: string
  room_id: string
  user_id: string
  username: string
  plan: PlanId
  content: string
  message_type: 'text' | 'emoji' | 'gif' | 'sticker' | 'system'
  created_at: string
}

// Odds do Usuário
export interface UserOdds {
  id: string
  room_id: string
  user_id: string
  odds_data: OddsSelection[]
  status: 'pending' | 'won' | 'lost'
  created_at: string
}

export interface OddsSelection {
  market: string
  selection: string
  odds: number
  bookmaker: string
}

// Reação
export interface RoomReaction {
  id: string
  room_id: string
  user_id: string
  username: string
  plan: PlanId
  emoji: string
  created_at: string
}

// Customização
export interface UserCustomization {
  user_id: string
  coins: number
  owned_items: string[]
  equipped_items: EquippedItems
  created_at: string
  updated_at: string
}

export interface EquippedItems {
  effects?: string
  colors?: string
  frames?: string
  celebrations?: string
  sounds?: string
}

// Item da Loja
export interface StoreItem {
  id: string
  category: 'effects' | 'colors' | 'frames' | 'celebrations' | 'sounds'
  name: string
  description: string
  price: number
  preview: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  is_active: boolean
}

// Eventos do Jogo
export interface MatchEvent {
  time: {
    elapsed: number
    extra?: number
  }
  team: {
    id: number
    name: string
    logo?: string
  }
  player: {
    id: number
    name: string
  }
  assist?: {
    id: number
    name: string
  }
  type: 'Goal' | 'Card' | 'subst' | 'Var'
  detail: string
  comments?: string
}

// Replay de Gol
export interface GoalReplay {
  id: string
  title: string
  competition: string
  thumbnail: string
  embed: string
  date: string
  teams: {
    home: { name: string; logo?: string }
    away: { name: string; logo?: string }
  }
}

// Celebração
export interface CelebrationEffect {
  type: 'basic' | 'confetti' | 'confetti_stars' | 'full'
  duration: number
  colors?: string[]
  particles?: number
}

// Odds API Response
export interface OddsResponse {
  id: string
  sport: string
  homeTeam: string
  awayTeam: string
  startTime: string
  bookmakers: Bookmaker[]
}

export interface Bookmaker {
  name: string
  markets: Market[]
}

export interface Market {
  type: string
  lastUpdate: string
  outcomes: Outcome[]
}

export interface Outcome {
  name: string
  price: number
  point?: number
}

// Fixture API Response
export interface FixtureResponse {
  id: number
  date: string
  timestamp: number
  venue: {
    id: number
    name: string
    city: string
  }
  status: {
    short: string
    long: string
    elapsed: number
  }
  league: {
    id: number
    name: string
    country: string
    logo: string
    round: string
  }
  teams: {
    home: Team
    away: Team
  }
  goals: {
    home: number
    away: number
  }
  events: MatchEvent[]
}

export interface Team {
  id: number
  name: string
  logo: string
  winner?: boolean
}
