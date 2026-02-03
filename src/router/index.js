import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Pricing from '../views/Pricing.vue'
import Dashboard from '../views/Dashboard.vue'
import CheckoutSuccess from '../views/CheckoutSuccess.vue'
import CheckoutCancel from '../views/CheckoutCancel.vue'
import BetModule from '../views/modules/BetModule.vue'
import TradeModule from '../views/modules/TradeModule.vue'
import CartolaModule from '../views/modules/CartolaModule.vue'
import PaperTrading from '../views/PaperTrading.vue'
import Admin from '../views/Admin.vue'
import Alerts from '../views/Alerts.vue'
import History from '../views/History.vue'
import Settings from '../views/Settings.vue'
import TrialExpired from '../views/TrialExpired.vue'
import Palpites from '../views/Palpites.vue'

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
    component: Pricing
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/bet',
    name: 'BetModule',
    component: BetModule,
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

export default router
