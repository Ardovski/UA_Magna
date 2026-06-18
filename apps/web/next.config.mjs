/** @type {import('next').NextConfig} */
// Dev'de CORS'suz çağrı için /api/backend/* → FastAPI proxy.
// Frontend client base'i "/api/backend" veya NEXT_PUBLIC_API_URL olabilir.
const backend = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    return [{ source: "/api/backend/:path*", destination: `${backend}/:path*` }];
  },
};

export default nextConfig;
