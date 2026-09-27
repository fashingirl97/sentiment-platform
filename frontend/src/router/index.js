import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '态势大盘' } },
      { path: 'workbench', name: 'workbench', component: () => import('../views/Workbench.vue'), meta: { title: '研判工作台' } },
      { path: 'report', name: 'report', component: () => import('../views/ReportCenter.vue'), meta: { title: '报告中心' } },
      { path: 'config', name: 'config', component: () => import('../views/Config.vue'), meta: { title: '监测配置' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'login' && !token) {
    next({ name: 'login' })
  } else if (to.name === 'login' && token) {
    next({ path: '/dashboard' })
  } else {
    next()
  }
})

export default router
