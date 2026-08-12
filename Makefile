.DEFAULT_GOAL := help
SHELL := /bin/bash

BACKEND := backend
FRONTEND := frontend
VENV := $(BACKEND)/.venv/bin

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
.PHONY: up
up: ## تشغيل كل الخدمات (postgres + redis + backend + frontend)
	docker compose up --build -d
	@echo "Backend  → http://localhost:8000/docs"
	@echo "Frontend → http://localhost:3000"

.PHONY: down
down: ## إيقاف الخدمات
	docker compose down

.PHONY: clean
clean: ## إيقاف الخدمات وحذف الـ volumes (يمسح قاعدة البيانات المحلية)
	docker compose down -v

.PHONY: logs
logs: ## متابعة سجلات الخدمات
	docker compose logs -f

# --------------------------------------------------------------- database
.PHONY: migrate
migrate: ## تطبيق آخر الـ migrations
	docker compose exec backend alembic upgrade head

.PHONY: migration
migration: ## إنشاء migration جديدة — الاستخدام: make migration m="add table"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"
	@echo "⚠️  راجع الملف المولَّد يدويًا قبل الـ commit — التوليد التلقائي ليس مضمونًا."

.PHONY: migrate-test
migrate-test: ## اختبار الـ migrations: upgrade → downgrade → upgrade (إلزامي قبل أي PR)
	docker compose exec backend alembic upgrade head
	docker compose exec backend alembic downgrade base
	docker compose exec backend alembic upgrade head
	@echo "✓ الـ migrations قابلة للتراجع"

.PHONY: seed
seed: ## إنشاء أول حساب مدير
	docker compose exec backend python -m app.cli.seed

.PHONY: ps
ps: ## حالة الخدمات
	docker compose ps

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
