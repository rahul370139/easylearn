/** @type {import('next').NextConfig} */
// Use a server-side env var for the backend target so we can proxy HTTP backends
// without exposing the URL to the browser (and without triggering mixed content).
const apiBase = (process.env.API_PROXY_TARGET || process.env.NEXT_PUBLIC_API_BASE_URL || "")
  .replace(/\/+$/, "")
  .replace(/\/api$/i, "")

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
    ]
  },
}

export default nextConfig
