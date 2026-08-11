import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies API calls to the backend so the UI can use relative
// URLs (/api/...) in both dev and the nginx-served production build.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
      "/ready": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
