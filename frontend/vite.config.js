// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      devOptions: { enabled: false },        // ← ローカル開発でもSW有効化
      registerType: 'autoUpdate',           // 新ビルドで自動更新
      includeAssets: ['/favicon.svg', '/apple-touch-icon.png'],
      manifest: {
        name: 'EXMATCH',
        short_name: 'EXMATCH',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        theme_color: '#111111',
        background_color: '#ffffff',
        icons: [
          { src: '/192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: '/512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
        ]
      }
    })
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  css: {
    devSourcemap: true,
    preprocessorOptions: {
      scss: {
        sourceMap: true,
        // node_modules（bootstrap等）由来の警告を抑制
        quietDeps: true,
        // deprecation warning を種類ごと黙らせる（今回のログに出てるやつ）
        silenceDeprecations: ['import', 'global-builtin', 'color-functions'],
      },
    },
  },
})
