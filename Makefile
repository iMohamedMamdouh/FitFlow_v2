.DEFAULT_GOAL := help
SHELL := /bin/bash

BACKEND := backend
FRONTEND := frontend
VENV := $(BACKEND)/.venv/bin

# بعض الأجهزة فيها الإضافة الحديثة (docker compose) وبعضها الأداة القديمة
# المنفصلة (docker-compose)، وبعضها لا شيء. نكتشف المتاح بدل افتراض واحدة،
# لأن الافتراض الخاطئ ينتج رسالة "unknown flag" لا علاقة لها بالسبب.
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" \
	|| (command -v docker-compose >/dev/null 2>&1 && echo "docker-compose"))

.PHONY: help
help: ## عرض الأوامر المتاحة
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------ setup
.PHONY: setup
setup: ## تجهيز بيئة التطوير المحلية (venv + node_modules + .env)
	@test -f .env || (cp .env.example .env && echo "✓ تم إنشاء .env من .env.example")
	cd $(BACKEND) && uv venv .venv && uv pip install --python .venv -e ".[dev]"
	cd $(FRONTEND) && npm ci
	$(VENV)/pre-commit install || true
	@echo "✓ البيئة جاهزة — شغّل: make up"

# ------------------------------------------------------------------ docker
.PHONY: require-compose
require-compose:
	@if [ -z "$(COMPOSE)" ]; then \
		echo "✗ Docker Compose غير متاح على الجهاز."; \
		echo ""; \
		echo "  الحل الأسرع: ثبّت Docker Desktop (يشمل Compose)"; \
		echo "    https://www.docker.com/products/docker-desktop"; \
		echo ""; \
		echo "  أو شغّل المشروع بدون Docker:"; \
		echo "    make setup"; \
		echo "    make dev-backend        # تيرمنال أول"; \
		echo "    make dev-frontend       # تيرمنال ثانٍ"; \
		exit 1; \
	fi
	@docker info >/dev/null 2>&1 || { \
		echo "✗ خدمة Docker غير مشغّلة — افتح Docker Desktop وانتظر حتى تستقر."; \
		exit 1; \
	}

.PHONY: up
up: require-compose ## تشغيل كل الخدمات (postgres + redis + backend + frontend)
	$(COMPOSE) up --build -d
	@echo "Backend  → http://localhost:8000/docs"
	@echo "Frontend → http://localhost:3000"

.PHONY: down
down: require-compose ## إيقاف الخدمات
	$(COMPOSE) down

.PHONY: clean
clean: require-compose ## إيقاف الخدمات وحذف الـ volumes (يمسح قاعدة البيانات المحلية)
	$(COMPOSE) down -v

.PHONY: logs
logs: require-compose ## متابعة سجلات الخدمات
	$(COMPOSE) logs -f

# --------------------------------------------------------------- database
.PHONY: migrate
migrate: require-compose ## تطبيق آخر الـ migrations
	$(COMPOSE) exec backend alembic upgrade head

.PHONY: migration
migration: require-compose ## إنشاء migration جديدة — الاستخدام: make migration m="add table"
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"
	@echo "⚠️  راجع الملف المولَّد يدويًا قبل الـ commit — التوليد التلقائي ليس مضمونًا."

.PHONY: migrate-test
migrate-test: require-compose ## اختبار الـ migrations: upgrade → downgrade → upgrade (إلزامي قبل أي PR)
	$(COMPOSE) exec backend alembic upgrade head
	$(COMPOSE) exec backend alembic downgrade base
	$(COMPOSE) exec backend alembic upgrade head
	@echo "✓ الـ migrations قابلة للتراجع"

.PHONY: seed
seed: require-compose ## إنشاء أول حساب مدير
	$(COMPOSE) exec backend python -m app.cli.seed

.PHONY: openapi
openapi: ## تصدير مواصفة OpenAPI وتوليد أنواع الواجهة منها
	cd $(BACKEND) && .venv/bin/python -m app.cli.export_openapi openapi.json
	cd $(FRONTEND) && npm run gen:api
	@echo "✓ العقد محدَّث — راجع الفرق قبل الـ commit"

.PHONY: seed-catalog
seed-catalog: require-compose ## تحميل قاعدة البداية (أطعمة + أنواع إصابات)
	$(COMPOSE) exec backend python -m app.cli.seed_catalog

.PHONY: ps
ps: ## حالة الخدمات
	$(COMPOSE) ps

# ----------------------------------------------------------------- quality
.PHONY: lint
lint: ## فحص الأسلوب في الباك والفرونت
	cd $(BACKEND) && .venv/bin/ruff check .
	cd $(BACKEND) && .venv/bin/black --check .
	cd $(FRONTEND) && npm run lint && npm run format:check

.PHONY: format
format: ## تنسيق الكود تلقائيًا
	cd $(BACKEND) && .venv/bin/ruff check --fix . && .venv/bin/black .
	cd $(FRONTEND) && npm run format

.PHONY: typecheck
typecheck: ## فحص الأنواع (mypy strict + tsc)
	cd $(BACKEND) && .venv/bin/mypy app
	cd $(FRONTEND) && npm run typecheck

.PHONY: test
test: ## تشغيل الاختبارات
	cd $(BACKEND) && .venv/bin/python -m pytest

.PHONY: check
check: lint typecheck test ## تشغيل كل الفحوصات (نفس ما تشغّله CI)
	@echo "✓ كل الفحوصات نجحت"

# ------------------------------------------------------- تشغيل بدون Docker
.PHONY: dev-backend
dev-backend: ## تشغيل الباك اند مباشرة (migrations + seed + uvicorn)
	cd $(BACKEND) && .venv/bin/alembic upgrade head
	cd $(BACKEND) && .venv/bin/python -m app.cli.seed
	cd $(BACKEND) && .venv/bin/python -m app.cli.seed_catalog
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --port 8000

.PHONY: dev-frontend
dev-frontend: ## تشغيل الفرونت اند مباشرة
	cd $(FRONTEND) && npm run dev

.PHONY: doctor
doctor: ## فحص الأدوات المتاحة على الجهاز وسبب أي عطل
	@printf "%-16s" "docker:";        command -v docker >/dev/null 2>&1 && docker --version || echo "غير مثبّت"
	@printf "%-16s" "compose:";       test -n "$(COMPOSE)" && echo "$(COMPOSE)" || echo "غير متاح"
	@printf "%-16s" "docker daemon:"; docker info >/dev/null 2>&1 && echo "شغّالة" || echo "متوقفة"
	@printf "%-16s" "python:";        command -v python3 >/dev/null 2>&1 && python3 --version || echo "غير مثبّت"
	@printf "%-16s" "uv:";            command -v uv >/dev/null 2>&1 && uv --version || echo "غير مثبّت"
	@printf "%-16s" "node:";          command -v node >/dev/null 2>&1 && node --version || echo "غير مثبّت"
	@printf "%-16s" "postgres:";      command -v pg_isready >/dev/null 2>&1 && (pg_isready -q && echo "شغّالة" || echo "مثبّتة لكن متوقفة") || echo "غير مثبّت"
	@printf "%-16s" "redis:";         command -v redis-cli >/dev/null 2>&1 && (redis-cli ping >/dev/null 2>&1 && echo "شغّال" || echo "مثبّت لكن متوقف") || echo "غير مثبّت"
