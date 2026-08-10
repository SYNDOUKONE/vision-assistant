import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "0.0.0.0", //  IMPORTANT MOBILE
    port: 5173,
  },
  build: {
    outDir: "dist",
  },
});