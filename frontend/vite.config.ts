import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite 开发服务器配置：端口与后端跨域来源保持一致
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,              // 与后端 CORS_ORIGINS 中的 5173 对应
    proxy: {
      // 前端把 /api 请求代理到后端，避免浏览器跨域
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
