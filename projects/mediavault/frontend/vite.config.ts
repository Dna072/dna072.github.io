import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// The dev server proxies API calls to the backend so the SPA and API share an
// origin in development (mirrors the CloudFront-in-front-of-API production model).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});
