# ============================================================================
# Üretim Performans Takip Uygulaması — Makefile
# backend (FastAPI)  +  frontend (Next.js)
# Kullanım: `make help`
# ============================================================================

# --- Yapılandırma ---------------------------------------------------------
API_DIR   := backend
WEB_DIR   := frontend
VENV      := $(API_DIR)/.venv
PY        := $(VENV)/bin/python
PIP       := $(VENV)/bin/pip
UVICORN   := $(VENV)/bin/uvicorn
PYTEST    := $(VENV)/bin/pytest
RUFF      := $(VENV)/bin/ruff
API_PORT  := 8000
WEB_PORT  := 3000

# Renkler (printf %b ile yazdırılır)
C_RESET  := \033[0m
C_BOLD   := \033[1m
C_CYAN   := \033[36m
C_GREEN  := \033[32m
C_YELLOW := \033[33m
C_GREY   := \033[90m

.DEFAULT_GOAL := help
.PHONY: help setup setup-api setup-web env dev dev-api dev-web dev-stop \
        build prod prod-stop db-init db-reset seed test test-api test-web \
        lint lint-api lint-web format typecheck check clean clean-db ai-sync \
        hooks ai-prompt ai-backup doctor

# --- Yardım ---------------------------------------------------------------
help: ## Bu yardım menüsünü göster (kategorize)
	@printf "\n$(C_BOLD)Üretim Performans Takip — komutlar$(C_RESET)\n\n"
	@printf "$(C_BOLD)  Kurulum & Geliştirme$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" setup    ".env kopyala + api & web bağımlılıkları + git hooks"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" env      ".env örneklerini kopyala (varsa dokunmaz)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev      "api (:8000) + web (:3000) birlikte çalıştır"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev-api  "Sadece FastAPI (reload, :8000)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev-web  "Sadece Next.js (:3000)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev-stop ":8000 ve :3000'ü tutan süreçleri öldür (stale port hataları için)"
	@printf "\n$(C_BOLD)  Production$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" build   "Frontend üretim build'i (.next/standalone)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" prod    "★ Üretim sunucusu: build + api (:8000) + web (:3000) — dev yavaşlığı yok"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" prod-stop "production süreçlerini durdur (:8000, :3000)"
	@printf "\n$(C_BOLD)  Veritabanı$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" db-init  "SQLite şemasını oluştur"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" db-reset "DB'yi sil + yeniden oluştur"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" seed     "data/production_data.csv'i import et"
	@printf "\n$(C_BOLD)  Kalite$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" test     "★ Tüm sistemi test et (pytest + ruff + tsc + eslint)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" lint     "ruff + eslint"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" format   "ruff format + prettier"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" typecheck "mypy (py) + tsc (ts)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" check    "lint + typecheck + test (CI eşdeğeri)"
	@printf "\n$(C_BOLD)  Temizlik$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" clean-db "Runtime SQLite DB'yi sil"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" clean    "node_modules, venv, cache, build artefaktları sil"
	@printf "\n$(C_BOLD)  AI Kullanım Şeffaflığı (Case §8)$(C_RESET)\n"
	@printf "    $(C_GREEN)%-12s$(C_RESET) %s\n" ai-prompt  "Yeni prompt log şablonu oluştur (name=<konu>)"
	@printf "    $(C_GREEN)%-12s$(C_RESET) %s\n" ai-sync    "AGENTS.md → CLAUDE.md senkron"
	@printf "    $(C_GREEN)%-12s$(C_RESET) ★ §8: AI sohbet geçmişini ai_usage/ altına topla (git yok)\n" ai-backup
	@printf "\n$(C_BOLD)  Araçlar$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" hooks   "Git hook'larını kur (.githooks)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" doctor  "Ortam kontrolü (python, node, npm sürümleri)"
	@printf "\n$(C_GREY)  web → http://localhost:$(WEB_PORT)   api → http://localhost:$(API_PORT)/docs$(C_RESET)\n\n"

# --- Kurulum --------------------------------------------------------------
setup: env setup-api setup-web hooks ## .env kopyala + api & web bağımlılıkları + git hooks
	@printf "$(C_BOLD)$(C_GREEN)✓ Kurulum tamam.$(C_RESET) 'make dev' ile başlat.\n"

env: ## .env örneklerini kopyala (varsa dokunmaz)
	@printf "$(C_CYAN)→$(C_RESET) .env örnekleri kopyalanıyor\n"
	@[ -f .env ] || cp .env.example .env && echo "  .env hazır"
	@[ -f $(WEB_DIR)/.env.local ] || cp $(WEB_DIR)/.env.local.example $(WEB_DIR)/.env.local && echo "  web/.env.local hazır"

setup-api: ## Python venv oluştur + backend bağımlılıkları
	@printf "$(C_CYAN)→$(C_RESET) Python venv oluşturuluyor: $(VENV)\n"
	@python3 -m venv $(VENV)
	@printf "$(C_GREEN)  ✓ venv hazır$(C_RESET)\n"
	@printf "$(C_CYAN)→$(C_RESET) pip güncelleniyor ($(VENV)/bin/pip)\n"
	@$(PIP) install --upgrade pip
	@printf "$(C_GREEN)  ✓ pip güncellendi$(C_RESET)\n"
	@printf "$(C_CYAN)→$(C_RESET) backend bağımlılıkları indiriliyor: $(API_DIR)/requirements*.txt\n"
	@$(PIP) install -r $(API_DIR)/requirements.txt -r $(API_DIR)/requirements-dev.txt
	@printf "$(C_GREEN)  ✓ backend bağımlılıkları kuruldu$(C_RESET)\n"

setup-web: ## Frontend bağımlılıkları (npm install)
	@printf "$(C_CYAN)→$(C_RESET) npm bağımlılıkları indiriliyor: $(WEB_DIR)/package.json\n"
	@cd $(WEB_DIR) && npm install --no-audit --no-fund --loglevel=error
	@printf "$(C_GREEN)  ✓ frontend bağımlılıkları kuruldu$(C_RESET)\n"

# --- Geliştirme -----------------------------------------------------------
dev: ## api (:8000) + web (:3000) birlikte çalıştır
	@printf "$(C_BOLD)→$(C_RESET) Başlatılıyor: api→:$(API_PORT)  web→:$(WEB_PORT)  (Ctrl-C ile dur)\n"
	@trap 'kill 0' INT TERM; \
	( cd $(API_DIR) && ../$(UVICORN) app.main:app --reload --port $(API_PORT) ) & \
	( cd $(WEB_DIR) && npm run dev ) & \
	wait

dev-api: ## Sadece FastAPI (reload, :8000)
	@printf "$(C_CYAN)→$(C_RESET) FastAPI: http://localhost:$(API_PORT) (reload)\n"
	@cd $(API_DIR) && ../$(UVICORN) app.main:app --reload --port $(API_PORT)

dev-web: ## Sadece Next.js (:3000)
	@printf "$(C_CYAN)→$(C_RESET) Next.js: http://localhost:$(WEB_PORT)\n"
	@cd $(WEB_DIR) && npm run dev

dev-stop: ## :8000 ve :3000 portlarını tutan süreçleri öldür (stale port hatası çözümü)
	@for port in $(API_PORT) $(WEB_PORT); do \
		pids=$$(ss -ltnp 2>/dev/null | awk -v p="$$port" '$$4 ~ ":"p" " {match($$6, /pid=([0-9]+)/, m); if (m[1]) print m[1]}'); \
		if [ -n "$$pids" ]; then \
			echo "  killing port $$port (pid: $$pids)"; \
			for pid in $$pids; do kill -9 $$pid 2>/dev/null || true; done; \
		else \
			echo "  port $$port zaten boş"; \
		fi; \
	done

# --- Production ------------------------------------------------------------
build: ## Frontend üretim build'i (.next/standalone, optimize edilmiş bundle)
	@printf "$(C_CYAN)→$(C_RESET) frontend build (.next/) başlatıldı\n"
	@cd $(WEB_DIR) && npm run build
	@printf "$(C_GREEN)  ✓ frontend build tamam$(C_RESET)\n"

prod: build ## ★ Üretim sunucusu: build sonrası api + web (dev compile yavaşlığı yok)
	@printf "$(C_BOLD)→$(C_RESET) Üretim başlatılıyor: api→:$(API_PORT)  web→:$(WEB_PORT)  (Ctrl-C ile dur)\n"
	@trap 'kill 0' INT TERM; \
	( cd $(API_DIR) && ../$(UVICORN) app.main:app --host 0.0.0.0 --port $(API_PORT) ) & \
	( cd $(WEB_DIR) && npm run start -- -p $(WEB_PORT) ) & \
	wait

prod-stop: dev-stop ## production süreçlerini durdur (:8000, :3000)

# --- Veritabanı -----------------------------------------------------------
db-init: ## SQLite şemasını oluştur
	@cd $(API_DIR) && ../$(PY) -m app.db.init_db
	@printf "$(C_GREEN)  ✓ DB şeması hazır$(C_RESET)\n"

db-reset: clean-db db-init ## DB'yi sil + yeniden oluştur

seed: ## data/production_data.csv'i import et (geliştirme kolaylığı)
	@cd $(API_DIR) && ../$(PY) -m app.features.ingestion.seed ../data/production_data.csv

# --- Kalite ---------------------------------------------------------------
test: ## Tüm sistemi test et: backend pytest + ruff + frontend tsc + eslint
	@printf "$(C_BOLD)→ Tüm sistem testi$(C_RESET)\n"
	@printf "  $(C_CYAN)[1/4]$(C_RESET) backend pytest\n"
	@cd $(API_DIR) && ../$(PYTEST) -v
	@printf "  $(C_CYAN)[2/4]$(C_RESET) backend ruff check\n"
	@$(RUFF) check $(API_DIR)
	@printf "  $(C_CYAN)[3/4]$(C_RESET) frontend tsc --noEmit\n"
	@cd $(WEB_DIR) && npx tsc --noEmit
	@printf "  $(C_CYAN)[4/4]$(C_RESET) frontend eslint\n"
	@cd $(WEB_DIR) && npx eslint . --max-warnings=0
	@printf "$(C_GREEN)✓ Tüm testler geçti$(C_RESET)\n"

test-api: ## Backend testleri (pytest) — özellikle validation
	@cd $(API_DIR) && ../$(PYTEST) -q

test-web: ## Frontend testleri
	@cd $(WEB_DIR) && npm test --silent --if-present

lint: lint-api lint-web ## ruff + eslint

lint-api: ## ruff check
	@$(RUFF) check $(API_DIR) || true

lint-web: ## eslint
	@cd $(WEB_DIR) && npm run lint --if-present

format: ## ruff format (py) + prettier (ts)
	@$(RUFF) format $(API_DIR) || true
	@cd $(WEB_DIR) && npm run format --if-present

typecheck: ## mypy (py) + tsc (ts)
	@cd $(WEB_DIR) && npx tsc --noEmit || true

check: lint typecheck test ## CI eşdeğeri: lint + typecheck + test

# --- Temizlik -------------------------------------------------------------
clean-db: ## Runtime SQLite DB'yi sil
	@rm -f db/*.db
	@echo "  ✓ DB silindi"

clean: ## node_modules, venv, cache, build artefaktları sil
	@rm -rf $(VENV) $(WEB_DIR)/node_modules $(WEB_DIR)/.next
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "  ✓ temizlendi"

# --- AI bağlam ------------------------------------------------------------
ai-sync: ## AGENTS.md'yi CLAUDE.md'ye kopyala (tek kaynak → MiniMax + Claude)
	@cp AGENTS.md CLAUDE.md
	@echo "  ✓ AGENTS.md → CLAUDE.md"

hooks: ## Git hook'larını kur (.githooks) — AI-bağımsız pre-commit
	@chmod +x .githooks/* .claude/hooks/*.sh scripts/*.sh 2>/dev/null || true
	@git config core.hooksPath .githooks
	@echo "  ✓ git hook'ları kuruldu (.githooks/pre-commit)"
	@echo "  i  Claude hook'ları (opsiyonel): cp .claude/settings.json.example .claude/settings.json"

ai-prompt: ## Yeni AI prompt log dosyası oluştur (name=<konu>)
	@scripts/new-ai-prompt.sh "$(name)"

ai-backup: ## §8: AI sohbet geçmişini ai_usage/transcripts/<kaynak>/ altına topla
	@printf "$(C_BOLD)→ AI sohbet geçmişi toplama (git yok)$(C_RESET)\n"
	@scripts/backup-sessions.sh

doctor: ## Ortam kontrolü (python, node, npm sürümleri)
	@echo "python3: $$(python3 --version 2>&1)"
	@echo "node:    $$(node --version 2>&1)"
	@echo "npm:     $$(npm --version 2>&1)"
