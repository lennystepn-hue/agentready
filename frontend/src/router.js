import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('./pages/Landing.vue'),
  },
  {
    path: '/scan/:id',
    name: 'ScanProgress',
    component: () => import('./pages/ScanProgress.vue'),
  },
  {
    path: '/report/:id',
    name: 'Report',
    component: () => import('./pages/Report.vue'),
  },
  {
    path: '/badge/:id',
    name: 'Badge',
    component: () => import('./pages/Badge.vue'),
  },
  {
    path: '/pricing',
    name: 'Pricing',
    component: () => import('./pages/Pricing.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('./pages/Login.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('./pages/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('./pages/Compare.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/monitoring',
    name: 'Monitoring',
    component: () => import('./pages/Monitoring.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/history/:domain?',
    name: 'History',
    component: () => import('./pages/History.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout/success',
    name: 'CheckoutSuccess',
    component: () => import('./pages/CheckoutSuccess.vue'),
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: () => import('./pages/Privacy.vue'),
  },
  {
    path: '/terms',
    name: 'Terms',
    component: () => import('./pages/Terms.vue'),
  },
  {
    path: '/imprint',
    name: 'Imprint',
    component: () => import('./pages/Imprint.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('agentcheck_token')
    if (!token) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  next()
})

export default router
