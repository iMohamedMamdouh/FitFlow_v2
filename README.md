# FitFlow v2

**المنصة الذكية للصحة والتأهيل الرياضي** — أداة دعم قرار (Clinical Decision Support) للأخصائيين، تجمع بين التأهيل من الإصابات، وإدارة الوزن، والتغذية الشخصية، والتحليل الفسيولوجي.

> ⚠️ **تنبيه طبي:** هذه المنصة أداة دعم قرار ولا تُغني عن استشارة الطبيب أو الأخصائي المختص. أي خطة تأهيل لا تُفعَّل إلا بعد اعتماد أخصائي.

---

## البنية

النظام مبني على **ثلاث طبقات ذكاء** منفصلة بوضوح:

| الطبقة | الوظيفة | التقنية |
|--------|---------|---------|
| 1. قاعدة بيانات علمية | الأغذية، التمارين، بروتوكولات الإصابات | PostgreSQL 16 |
| 2. محرك القواعد | يتخذ **كل** القرارات وفق بروتوكولات علمية ثابتة | Python نقي |
| 3. الذكاء الاصطناعي | يشرح ويصيغ فقط — **لا يقرر** | Claude API |

القرار يأتي من محرك القواعد، والـ AI يشرح، والأخصائي يراجع ويعتمد. التفاصيل في [`docs/ADR.md`](docs/ADR.md).

## التقنيات

| | |
|---|---|
| **Backend** | Python 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic |
| **Database** | PostgreSQL 16 · Redis 7 |
| **Frontend** | Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 |
| **الجودة** | ruff · black · mypy (strict) · pytest · eslint · prettier |
| **النشر** | Docker · DigitalOcean + Coolify |

---

## التشغيل المحلي

**المتطلبات:** Docker + Docker Compose، و (للتطوير خارج الحاويات) Python 3.11 + [uv](https://docs.astral.sh/uv/) + Node.js 22.

```bash
# 1. انسخ ملف البيئة وعدّل القيم
cp .env.example .env

# 2. شغّل كل الخدمات
make up
```

| الخدمة | العنوان |
|--------|---------|
| الواجهة | http://localhost:3000 |
| توثيق الـ API | http://localhost:8000/docs |
| فحص الجاهزية | http://localhost:8000/health/ready |

### تطوير خارج الحاويات

```bash
make setup      # venv + node_modules + pre-commit
make check      # نفس الفحوصات اللي بتشغّلها CI
```

## الأوامر

```bash
make help       # عرض كل الأوامر
make up         # تشغيل الخدمات
make down       # إيقاف الخدمات
make clean      # إيقاف + حذف الـ volumes (يمسح قاعدة البيانات المحلية)
make logs       # متابعة السجلات
make lint       # فحص الأسلوب
make format     # تنسيق تلقائي
make typecheck  # mypy strict + tsc
make test       # الاختبارات
make check      # كل ما سبق
```

---

## هيكل المشروع

```
FitFlow_v2/
├── backend/              # FastAPI + محرك القواعد
│   ├── app/
│   │   ├── api/          # المسارات
│   │   ├── core/         # الإعدادات، قاعدة البيانات، محرك القواعد، طبقة الـ AI
│   │   ├── models/       # نماذج SQLAlchemy        (المرحلة 1)
│   │   └── schemas/      # مخططات Pydantic         (المرحلة 1)
│   ├── tests/
│   └── Dockerfile
├── frontend/             # Next.js — عربي RTL
│   └── src/app/
├── docs/
│   ├── PROJECT_PLAN.md   # الخطة المرجعية
│   ├── EXECUTION_PLAN.md # خطوات التنفيذ بالترتيب
│   └── ADR.md            # القرارات المعمارية الملزمة
├── docker-compose.yml
└── Makefile
```

## التوثيق

| الملف | المحتوى |
|-------|---------|
| [`docs/EXECUTION_PLAN.md`](docs/EXECUTION_PLAN.md) | خطوات التنفيذ بالترتيب مع معيار إنجاز لكل خطوة |
| [`docs/ADR.md`](docs/ADR.md) | القرارات المعمارية الملزمة وأسبابها |
| [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) | الخطة المرجعية الكاملة |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | طريقة العمل وقواعد الـ commits والمراجعة |

## حالة التنفيذ

- [x] **المرحلة 0** — التأسيس: monorepo، Docker، حواجز الجودة، CI
- [ ] **المرحلة 1** — قاعدة البيانات والمصادقة والأدوار وسجل التدقيق
- [ ] **المرحلة 2** — نموذج البيانات الكامل
- [ ] **المرحلة 3** — المحتوى العلمي (بالتوازي)
- [ ] **المرحلة 4** — محرك القواعد ⭐

الخريطة الكاملة في [`docs/EXECUTION_PLAN.md`](docs/EXECUTION_PLAN.md).
