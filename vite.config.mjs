import { defineConfig } from 'vite';
import { resolve } from 'path';
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: "/static/", // must match STATIC_URL setting in settings 
  resolve : {
    alias : {
        '@': '/django_nominopolitan/static'
    }
  },
  build: {
    manifest: "manifest.json",
    outDir: resolve("nominopolitan/assets"),
    assetsDir: "django_assets",
    rollupOptions: {
      input: {
        nominopolitan: resolve('django_nominopolitan/static/js/main.js')
      }
    }
  },
  plugins: [
    tailwindcss(),
  ],
})

