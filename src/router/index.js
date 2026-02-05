import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import CheckoutSuccess from '../views/CheckoutSuccess.vue'
import CheckoutCancel from '../views/CheckoutCancel.vue'
import TradeModule from '../views/modules/TradeModule.vue'
import CartolaModule from '../views/modules/CartolaModule.vue'
import PaperTrading from '../views/PaperTrading.vue'
import Admin from '../views/Admin.vue'
import Alerts from '../views/Alerts.vue'
import History from '../views/History.vue'
import Settings from '../views/Settings.vue'
import TrialExpired from '../views/TrialExpired.vue'
import Palpites from '../views/Palpites.vue'
import OddsComparator from '../views/OddsComparator.vue'
// v2.0 - Live Rooms
import LiveRooms from '../views/LiveRooms.vue'
import GameRoom from '../views/GameRoom.vue'
import PricingV2 from '../views/PricingV2.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/palpites',
    name: 'Palpites',
    component: Palpites
  },
  {
    path: '/odds',
    name: 'OddsComparator',
    component: OddsComparator,
    meta: { requiresAuth: true }
  },
  {
    path: '/bet',
    name: 'Bet',
    component: OddsComparator,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/pricing',
    name: 'Pricing',
    component: PricingV2
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/trade',
    name: 'TradeModule',
    component: TradeModule,
    meta: { requiresAuth: true }
  },
  {
    path: '/cartola',
    name: 'CartolaModule',
    component: CartolaModule,
    meta: { requiresAuth: true }
  },
  {    path: '/paper-trading',
    name: 'PaperTrading',
    component: PaperTrading,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: Alerts,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: History,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/trial-expired',
    name: 'TrialExpired',
    component: TrialExpired,
    meta: { requiresAuth: true }
  },
  {
    path: '/checkout/success',
    name: 'CheckoutSuccess',
    component: CheckoutSuccess
  },
  {
    path: '/checkout/cancel',
    name: 'CheckoutCancel',
    component: CheckoutCancel
  },
  // v2.0 - Salas ao Vivo
  {
    path: '/live',
    name: 'LiveRooms',
    component: LiveRooms,
    meta: { requiresAuth: true }
  },
  {
    path: '/live/:roomId',
    name: 'GameRoom',
    component: GameRoom,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0 }
  }
})

// Guard de autenticação global
import { supabase } from '../lib/supabase'

router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  if (requiresAuth) {
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      // Não autenticado - redireciona para login
      return next({ 
        path: '/login', 
        query: { redirect: to.fullPath } 
      })
    }
  }
  
  next()
})

export default router
