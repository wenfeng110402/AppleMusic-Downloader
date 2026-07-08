import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  typescript: { ignoreBuildErrors: true },
  allowedDevOrigins: ["192.168.100.170"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      }
    ]
  }
};

export default nextConfig;