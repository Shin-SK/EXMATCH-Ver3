// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  css: {
    devSourcemap: true,                // ★ 開発時のCSSソースマップを有効化
    preprocessorOptions: {
      scss: { sourceMap: true },       // ★ 念のためSass側もON
    },
  },
})
