import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/main.js'),
      name: 'RAGWidget',
      fileName: 'widget',
      formats: ['iife']
    },
    rollupOptions: {
      output: {
        // Keep bundle as small as possible
      }
    }
  }
})
