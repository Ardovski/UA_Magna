# Ortam Değişkenleri (.env)

İki `.env` var: **backend** (kök `.env`, secret'lı) ve **frontend** (`frontend/.env.local`, public).
`make setup` ikisini de `.example`'dan kopyalar. Gerçek `.env` **asla** commit edilmez.

## Backend — kök `.env` (`.env.example`'dan)
| Değişken | Açıklama | Örnek |
|----------|----------|-------|
| `TARGET_API_URL` | Hedef MES API base | `http://89.252.189.91:8983` |
| `TARGET_API_SUBMIT_PATH` | Submit yolu | `/api/v1/submit` |
| `TARGET_API_KEY` | **Secret** — X-Production-Key | `***` |
| `TARGET_API_TIMEOUT_SECONDS` | İstek timeout | `15` |
| `TARGET_API_MAX_RETRIES` | Maks retry | `3` |
| `TARGET_API_BACKOFF_BASE_SECONDS` | Backoff tabanı | `2` |
| `TARGET_API_RATE_LIMIT_COOLDOWN_SECONDS` | 429 bekleme | `60` |
| `APP_ENV` | ortam | `development` |
| `LOG_LEVEL` | log seviyesi | `INFO` |
| `DATABASE_URL` | SQLite yolu (boşsa repo kökü `db/app.db`) | `sqlite:///./db/app.db` |
| `CORS_ALLOW_ORIGINS` | İzinli origin | `http://localhost:3000` |

## Frontend — `frontend/.env.local` (`.env.local.example`'dan)
| Değişken | Açıklama | Örnek |
|----------|----------|-------|
| `BACKEND_INTERNAL_URL` | Next rewrite proxy hedefi (`/api/v1/*` → FastAPI). `.env.local.example`'da aktif olan tek değişken; sıfır-config kurulum için yeterli. | `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` (opsiyonel) | Boşsa (varsayılan) client `/api/v1/...` relative çağırır → Next rewrite FastAPI'ye proxy'ler (CORS yok). Sadece doğrudan cross-origin için doldurulur. | (boş) / `http://localhost:8000` |

> `NEXT_PUBLIC_*` tarayıcıya gömülür → **buraya asla secret koyma**. Hedef API key sadece backend.

## Güvenlik Kuralları
- `.env`, `.env.local` gitignore'lu; sadece `*.example` paylaşılır.
- Key'i log'a, hata mesajına, frontend'e basma.
- Mock geliştirme: `TARGET_API_URL` → `https://webhook.site/<id>` ile test, sonra gerçeğe geç.
