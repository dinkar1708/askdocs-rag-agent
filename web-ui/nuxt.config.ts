// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: ['@nuxtjs/tailwindcss'],

  runtimeConfig: {
    public: {
      // REQUIRED: Must be set via NUXT_PUBLIC_API_BASE environment variable
      // Development: http://localhost:8000
      // Testing: http://localhost:8001
      // Production: Set in deployment environment
      apiBase: process.env.NUXT_PUBLIC_API_BASE || (() => {
        throw new Error('NUXT_PUBLIC_API_BASE environment variable is required. Set it in your environment or .env file.')
      })(),
      // API Key for backend authentication
      // Development/Testing: test-api-key-not-for-production
      // Production: Set via NUXT_PUBLIC_API_KEY environment variable
      apiKey: process.env.NUXT_PUBLIC_API_KEY || 'test-api-key-not-for-production'
    }
  },

  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        prependPath: true
      }
    }
  }
})
