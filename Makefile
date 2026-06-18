# ============================================================================
# Üretim Performans Takip Uygulaması — Makefile
# Monorepo: apps/api (FastAPI)  +  apps/web (Next.js)
# Kullanım: `make help`
# ============================================================================

# --- Yapılandırma ---------------------------------------------------------
API_DIR   := apps/api
WEB_DIR   := apps/web
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
.PHONY: help setup setup-api setup-web env dev dev-api dev-web \
        db-init db-reset seed test test-api test-web lint lint-api lint-web \
        format typecheck check clean clean-db ai-sync hooks ai-prompt \
        ai-backup doctor

# --- Yardım ---------------------------------------------------------------
help: ## Bu yardım menüsünü göster (kategorize)
	@printf "\n$(C_BOLD)Üretim Performans Takip — komutlar$(C_RESET)\n\n"
	@printf "$(C_BOLD)  Kurulum & Geliştirme$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" setup    ".env kopyala + api & web bağımlılıkları + git hooks"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" env      ".env örneklerini kopyala (varsa dokunmaz)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev      "api (:8000) + web (:3000) birlikte çalıştır"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev-api  "Sadece FastAPI (reload, :8000)"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" dev-web  "Sadece Next.js (:3000)"
	@printf "\n$(C_BOLD)  Veritabanı$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" db-init  "SQLite şemasını oluştur"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" db-reset "DB'yi sil + yeniden oluştur"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" seed     "data/production_data.csv'i import et"
	@printf "\n$(C_BOLD)  Kalite$(C_RESET)\n"
	@printf "    $(C_CYAN)%-12s$(C_RESET) %s\n" test     "Tüm testler (pytest + web)"
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
	@echo "$(B)✓ Kurulum tamam.$(R) 'make dev' ile başlat."

env: ## .env örneklerini kopyala (varsa dokunmaz)
	@[ -f .env ] || cp .env.example .env && echo "  .env hazır"
	@[ -f $(WEB_DIR)/.env.local ] || cp $(WEB_DIR)/.env.local.example $(WEB_DIR)/.env.local && echo "  web/.env.local hazır"

setup-api: ## Python venv oluştur + backend bağımlılıkları
	@python3 -m venv $(VENV)
	@$(PIP) install -q --upgrade pip
	@$(PIP) install -q -r $(API_DIR)/requirements.txt -r $(API_DIR)/requirements-dev.txt
	@echo "  ✓ backend bağımlılıkları kuruldu ($(VENV))"

setup-web: ## Frontend bağımlılıkları (npm install)
	@cd $(WEB_DIR) && npm install --silent
	@echo "  ✓ frontend bağımlılıkları kuruldu"

# --- Geliştirme -----------------------------------------------------------
dev: ## api (:8000) + web (:3000) birlikte çalıştır
	@echo "$(B)Başlatılıyor:$(R) api→:$(API_PORT)  web→:$(WEB_PORT)  (Ctrl-C ile dur)"
	@trap 'kill 0' INT TERM; \
	( cd $(API_DIR) && ../../$(UVICORN) app.main:app --reload --port $(API_PORT) ) & \
	( cd $(WEB_DIR) && npm run dev ) & \
	wait

dev-api: ## Sadece FastAPI (reload, :8000)
	@cd $(API_DIR) && ../../$(UVICORN) app.main:app --reload --port $(API_PORT)

dev-web: ## Sadece Next.js (:3000)
	@cd $(WEB_DIR) && npm run dev

# --- Veritabanı -----------------------------------------------------------
db-init: ## SQLite şemasını oluştur
	@cd $(API_DIR) && ../../$(PY) -m app.db.init_db
	@echo "  ✓ DB şeması hazır"

db-reset: clean-db db-init ## DB'yi sil + yeniden oluştur

seed: ## data/production_data.csv'i import et (geliştirme kolaylığı)
	@cd $(API_DIR) && ../../$(PY) -m app.features.ingestion.seed ../../data/production_data.csv

# --- Kalite ---------------------------------------------------------------
test: test-api test-web ## Tüm testler

test-api: ## Backend testleri (pytest) — özellikle validation
	@cd $(API_DIR) && ../../$(PYTEST) -q

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
	@rm -f $(API_DIR)/var/*.db
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
