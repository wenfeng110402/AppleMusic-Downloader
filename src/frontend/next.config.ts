import type { NextConfig } from "next";

const backendPort = process.env.API_PORT || process.env.PORT || process.env.BACKEND_PORT || "8000";
const backendUrl = process.env.AMDL_API_URL || `http://127.0.0.1:${backendPort}`;

const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      }
    ]
  }
};

export default nextConfig;