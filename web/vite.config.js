import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      proxy: {
        '^/api': {
          target: env.VITE_API_URL || 'http://127.0.0.1:5050',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '/api')
        }
      },
      watch: {
        usePolling: true,
        ignored: ['**/node_modules/**', '**/dist/**'],
      },
      host: '0.0.0.0',
      port: 5173,               // optional: mirrors the compose file
      // 👇  allow the domain that Caddy / router forwards
      allowedHosts: ['yuknow.net', '.yuknow.net'], // second entry permits sub-domains
      // If you prefer to disable the check completely (dev only!):
      // allowedHosts: 'all',
    }
  }
})
