import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.exchangerate-api\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'currency-rates',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 // 1 day
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      },
      manifest: {
        name: 'WanderWise AI Travel Companion',
        short_name: 'WanderWise',
        description: 'AI-Powered Smart Travel Ecosystem',
        theme_color: '#185FA5',
        background_color: '#e4f1fb',
        display: 'standalone',
        icons: [
          {
            src: 'https://placehold.co/192x192/185FA5/FFFFFF?text=W',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'https://placehold.co/512x512/185FA5/FFFFFF?text=W',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
})