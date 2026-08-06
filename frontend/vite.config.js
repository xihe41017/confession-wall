import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发环境代理：/api 转发到本地后端 8000 端口
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 上传的图片/视频静态资源
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
