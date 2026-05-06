/** @type {import('next').NextConfig} */
const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/+$/, "")

const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    if (!apiBase) return []

    return [
      // Proxy backend endpoints through the Vercel domain to avoid browser mixed-content issues
      // when the backend is served over plain HTTP (e.g. http://<VPS_IP>:8000).
      { source: "/health", destination: `${apiBase}/health` },
      { source: "/api/:path*", destination: `${apiBase}/api/:path*` },
    ]
  },
}

export default nextConfig
