import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // forward /run to Flask on 8000
      '/run': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      '/progress': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
    }
  }
})