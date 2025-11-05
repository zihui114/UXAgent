import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './style.scss'
import App from './App.vue'
import naive from 'naive-ui'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: App },
  ],
})

createApp(App).use(naive).use(router).mount('#app')
