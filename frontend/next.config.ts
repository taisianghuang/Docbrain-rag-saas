import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 開啟 React Strict Mode (建議)
  reactStrictMode: true,

  // --- 新增：設定 Proxy ---
  async rewrites() {
    return [
      {
        // 前端請求的路徑 (例如 /api/auth/login)
        source: "/api/:path*",
        // 轉發到的後端真實路徑
        // 注意：這裡是後端伺服器的位址，如果您是在本機跑 Docker，通常是 http://127.0.0.1:8000
        destination: "http://127.0.0.1:8000/api/:path*", 
      },
    ];
  },
};

export default nextConfig;
