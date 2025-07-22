import { defineConfig } from 'vite';
import { resolve } from 'path';
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: "/static/",
  server: {
    host: '0.0.0.0',    // Add this
    port: 5174,
    cors: true,         // Add this
    allowedHosts: [
      'django_nominopolitan_vite_dev',  // Add container name
      'localhost'                       // Keep localhost for local access
    ],
    watch: {
      usePolling: true  // Add this
    }
  },
  resolve : {
    alias : {
        '@': '/config/static'
    }
  },
  build: {
    manifest: "manifest.json",
    outDir: resolve("nominopolitan/assets"),
    assetsDir: "django_assets",
    rollupOptions: {
      input: {
        nominopolitan: resolve('config/static/js/main.js')
      }
    }
  },
  plugins: [
    tailwindcss(),
  ],
})

