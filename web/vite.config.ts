import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  build: {
    rollupOptions: {
      input: { main: path.resolve(__dirname, "index.html"), docs: path.resolve(__dirname, "docs/index.html") },
    },
  },
  server: { proxy: { "/api": backend, "/files": backend } },
});
