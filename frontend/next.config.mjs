/** @type {import('next').NextConfig} */
// Dev'de CORS'suz, sıfır-config çağrı için /api/v1/* → FastAPI proxy.
// Client same-origin "/api/v1/..." çağırır; burada FastAPI'ye yönlendirilir.
// Doğrudan (cross-origin) bağlanmak istersen NEXT_PUBLIC_API_URL set et (örn. http://localhost:8000).
const backend = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Ağır UI kütüphanelerini tree-shake et → bundle küçülür, ilk yükleme hızlanır.
  // recharts: tüm grafik tiplerini import etmek yerine yalnız kullanılanları çek.
  experimental: {
    optimizePackageImports: ["recharts", "@tanstack/react-table", "lucide-react"],
  },
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` }];
  },
};

export default nextConfig;
