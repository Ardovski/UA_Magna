/**
 * Ortam değişkenleri erişimi (tek nokta).
 * NEXT_PUBLIC_* tarayıcıya gömülür → burada ASLA secret olmaz (hedef API key sadece backend).
 */
export const env = {
  /**
   * FastAPI backend base URL.
   * Varsayılan boş → same-origin: client "/api/v1/..." çağırır, Next rewrite
   * (next.config.mjs) bunu FastAPI'ye proxy'ler (CORS gerekmez, sıfır-config).
   * Doğrudan bağlanmak için NEXT_PUBLIC_API_URL=http://localhost:8000 set et.
   */
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "",
} as const;
