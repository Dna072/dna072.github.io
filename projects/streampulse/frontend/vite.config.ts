import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// The API base is injected at build/runtime via VITE_API_BASE_URL.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: true,
    port: 5173,
  },
  preview: {
    host: true,
    port: 8080,
  },
});
