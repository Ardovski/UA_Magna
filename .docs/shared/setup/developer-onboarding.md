# Geliştirici Onboarding

## Önkoşullar
- **Python** ≥ 3.11
- **Node** ≥ 20 (`.nvmrc` → `nvm use`)
- **make**, **git**

## Kurulum (3 komuttan az)
```bash
git clone https://github.com/<kullanici>/umut-arda-ozdes-uretim-takip-case.git
cd umut-arda-ozdes-uretim-takip-case
make setup     # .env kopyalar + api venv + web npm kurar
```
`.env` içindeki `TARGET_API_KEY`'i gerçek key ile doldur (case'ten gelen).

## Çalıştırma
```bash
make dev       # web → http://localhost:3000   api → http://localhost:8000/docs
# veya ayrı ayrı:
make dev-api
make dev-web
```

## İlk Veri
```bash
# production_data.csv'i data/ altına koy (repo'da gelir), sonra:
make db-init   # şema
make seed      # CSV'i import et (opsiyonel, hızlı başlangıç)
```
Veya UI'dan: `/import` sayfasından CSV yükle.

## Sık Komutlar
| Komut | İş |
|-------|----|
| `make help` | tüm komutlar |
| `make test` | testler (özellikle validation) |
| `make lint` / `make format` | kalite |
| `make check` | lint+typecheck+test (commit öncesi) |
| `make db-reset` | DB sıfırla |
| `make clean` | venv/node_modules/cache sil |

## Nereye Bak
- Mimari → [`../architecture/overview.md`](../architecture/overview.md)
- Validasyon kuralları → [`validation-rules.md`](../domain/validation-rules.md)
- Plan/CHECKLIST → [`../../.roadmap/`](../../.roadmap/)
- Ortam değişkenleri → [`environment.md`](environment.md)
