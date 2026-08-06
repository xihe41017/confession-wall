import { createRouter, createWebHistory } from 'vue-router'
import WallView from '../views/WallView.vue'

const routes = [
  { path: '/', name: 'wall', component: WallView },
  { path: '/post', name: 'post', component: () => import('../views/PostView.vue') },
  { path: '/account', name: 'account', component: () => import('../views/AccountView.vue') },
  { path: '/admin', name: 'admin', component: () => import('../views/AdminView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
