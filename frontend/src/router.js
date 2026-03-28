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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
