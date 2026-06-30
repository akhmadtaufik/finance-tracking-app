import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'
import { pinia } from './stores'
import '@aejkatappaja/phantom-ui'

import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(pinia)

const authStore = useAuthStore()
authStore.initialize().finally(() => {
  app.use(router)
  app.mount('#app')
})
