import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import Dashboard from './views/Dashboard.vue'
import IndicatorDetail from './views/IndicatorDetail.vue'
import Settings from './views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', component: { template: '<span />' } },
    { path: '/t/:tabId', name: 'dashboard', component: Dashboard, meta: { title: '仪表盘' } },
    { path: '/t/:tabId/i/:indicatorId', name: 'indicator-detail', component: IndicatorDetail, meta: { title: '指标详情' } },
    { path: '/settings', name: 'settings', component: Settings, meta: { title: '设置' } },
  ],
})

createApp(App).use(router).mount('#app')
