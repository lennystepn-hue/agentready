import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'
import './assets/main.css'
import { initAuth } from './auth.js'

const app = createApp(App)
app.use(router)

initAuth().finally(() => {
  app.mount('#app')
})
