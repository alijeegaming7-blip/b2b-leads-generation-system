import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Build output goes to backend's static folder for serving
  build: {
    outDir: "../../apps/api-python/static",
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    allowedHosts: [
      "localhost",
      ".ngrok-free.dev",
      ".ngrok-free.app",
      ".railway.app",
      ".up.railway.app",
      ".loca.lt",
    ],
    proxy: {
      "/api": {
        target: "http://localhost:3001",
        changeOrigin: true,
      },
    },
  },
});
