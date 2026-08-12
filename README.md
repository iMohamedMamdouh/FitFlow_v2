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

لو Docker مش متاح أو مش عايزه:

```bash
make setup          # venv + node_modules + pre-commit
make dev-backend    # تيرمنال أول  — migrations + seed + uvicorn
make dev-frontend   # تيرمنال ثانٍ — next dev
```

بيحتاج PostgreSQL 16 شغّال محليًا وقاعدتَي بيانات `fitflow` و`fitflow_test`:

```bash
psql postgres -c "CREATE USER fitflow WITH PASSWORD 'fitflow' CREATEDB;"
createdb -O fitflow fitflow
createdb -O fitflow fitflow_test
```

ثم عدّل `POSTGRES_PASSWORD` في `.env` ليطابق كلمة السر أعلاه.

### استكشاف الأعطال

```bash
make doctor     # يعرض الأدوات المتاحة وحالتها ويحدد سبب أي عطل
```

| الرسالة | السبب والحل |
|---------|-------------|
| `unknown flag: --build` | Docker Compose غير مثبّت. ثبّت Docker Desktop، أو استخدم مسار "تطوير خارج الحاويات" أعلاه |
| `Cannot connect to the Docker daemon` | Docker Desktop مقفول — افتحه وانتظر حتى يستقر |
| `redis:"error"` في `/health/ready` | Redis غير مشغّل. متوقع خارج Docker ولا يعطّل شيئًا — مطلوب من المرحلة 9 |
| `SECRET_KEY لازم يكون 32 حرف` | لم يُنشأ `.env` — نفّذ `cp .env.example .env` |
| `connection refused` على 5432 | PostgreSQL متوقف، أو `POSTGRES_PASSWORD` في `.env` لا يطابق كلمة سر المستخدم |
| بورت مشغول | غيّر `BACKEND_PORT` أو `FRONTEND_PORT` في `.env` |

## الأوامر

```bash
make help          # عرض كل الأوامر
make up            # تشغيل الخدمات (يطبّق الـ migrations تلقائيًا)
make down          # إيقاف الخدمات
make clean         # إيقاف + حذف الـ volumes (يمسح قاعدة البيانات المحلية)
make logs          # متابعة السجلات
make seed          # إنشاء أول حساب مدير
make migrate       # تطبيق آخر الـ migrations
make migration m=".."  # إنشاء migration جديدة
make migrate-test  # اختبار التراجع: upgrade → downgrade → upgrade
make lint          # فحص الأسلوب
make format        # تنسيق تلقائي
make typecheck     # mypy strict + tsc
make test          # الاختبارات
make check         # كل ما سبق
```

## المصادقة والأدوار

| الدور | كيف يُنشأ |
|-------|-----------|
| `patient` | تسجيل عام عبر `POST /api/v1/auth/register` |
| `specialist` | يُنشئه مدير عبر `POST /api/v1/admin/users` |
| `admin` | أول واحد عبر `make seed`، والباقي من مدير |

**لا يوجد أي مسار عام يرفع الصلاحيات** — نموذج التسجيل لا يحتوي حقل `role` أصلًا.

| المسار | الوصف | الصلاحية |
|--------|-------|----------|
| `POST /api/v1/auth/register` | تسجيل مريض جديد | عام |
| `POST /api/v1/auth/login` | دخول → زوج رموز | عام |
| `POST /api/v1/auth/refresh` | تدوير الرمز | رمز تحديث صالح |
| `POST /api/v1/auth/logout` | إبطال الجلسة | رمز تحديث صالح |
| `GET /api/v1/users/me` | الملف الشخصي | أي مستخدم مسجّل |
| `GET /api/v1/admin/users` | قائمة المستخدمين | `admin` |
| `POST /api/v1/admin/users` | إنشاء أخصائي/مدير | `admin` |
| `GET,PUT /api/v1/me/profile` | الملف الشخصي | صاحبه |
| `POST /api/v1/me/profile/consent` | الموافقة على التنبيه الطبي | صاحبه |
| `GET,POST /api/v1/me/injuries` | الإصابات | صاحبها |
| `GET,POST /api/v1/me/readings` | القياسات | صاحبها |
| `GET /api/v1/me/plans` | **الخطط المعتمدة فقط** | صاحبها |
| `POST /api/v1/plans/generate` | توليد خطة (مسودة) | صاحبها أو أخصائيه |
| `POST /api/v1/plans/{id}/submit` | إرسال للمراجعة | صاحبها أو أخصائيه |
| `POST /api/v1/plans/{id}/approve` | اعتماد | `specialist` `admin` |
| `POST /api/v1/plans/{id}/request-changes` | طلب تعديل بسبب | `specialist` `admin` |
| `POST /api/v1/plans/{id}/activate` | تفعيل → تصبح مرئية | `specialist` `admin` |
| `GET /api/v1/specialist/patients` | **المرضى المسنَدون فقط** | `specialist` `admin` |
| `GET /api/v1/specialist/review-queue` | قائمة المراجعة | `specialist` `admin` |

### العزل بين المرضى

| القاعدة | كيف تُفرض |
|---------|-----------|
| المريض يرى بياناته فقط | مسارات `/me/*` لا تقبل معرّف مستخدم أصلًا |
| المريض لا يرى خطة غير مفعّلة | فلترة على مستوى الاستعلام، لا بعد الجلب |
| الأخصائي يرى مرضاه المسنَدين فقط | كل استعلام يمر بـ `specialist_patients` |
| منع استكشاف المعرّفات | **404 موحّد** لغير الموجود ولغير المصرّح — 403 يؤكد الوجود |
| الاطلاع على سجل مريض | يُسجَّل في سجل التدقيق — المساءلة تشمل القراءة |

### عقد واحد بين الباك والفرونت

الـ CI يصدّر `openapi.json` من الباك اند ثم يولّد منه أنواع TypeScript للواجهة. تغيير حقل في مخطط Pydantic يكسر بناء الواجهة **فورًا** بدل أن يظهر كخطأ وقت تشغيل عند مستخدم.

### دورة اعتماد الخطة

```
draft ──▶ pending_review ──▶ approved ──▶ active ──▶ archived
  ▲             │
  └─ changes_requested ─┘
```

الانتقالات مفروضة على **مستويين**: قيود `CHECK` وtrigger في قاعدة البيانات، لا في التطبيق وحده. أي مسار API جديد أو سكربت صيانة يمر من نفس الحاجز.

| القاعدة | كيف تُفرض |
|---------|-----------|
| لا خطة معتمدة بلا معتمِد | `CHECK` على `plans` |
| لا مسودة تحمل بيانات اعتماد | `CHECK` على `plans` |
| خطة مفعّلة واحدة لكل مستخدم لكل نوع | فهرس فريد جزئي |
| لا قفز فوق المراجعة | trigger `BEFORE UPDATE` |
| لا خطة تحت 1200 سعرة (ADR-007) | `CHECK` على `nutrition_plans` |
| لا مانع تمرين يشير لإصابة غير موجودة | مفتاح أجنبي |
| لا إسناد مريض لغير أخصائي | مفتاح أجنبي مركّب على `users(id, role)` |

## محرك القواعد

**وحدة نقية** لا تستورد FastAPI ولا SQLAlchemy — يُفرض ذلك باختبار معماري يقرأ شجرة الكود، لا بالاتفاق. النتيجة: كل قرار سريري قابل للاختبار بلا قاعدة بيانات ولا خادم.

```python
profile  = ProfileSnapshot(age_years=30, gender=MALE, height_cm=180, weight_kg=90, ...)
decision = decide_priority(profile, injuries)      # REHAB_ONLY / WEIGHT_LOSS / ...
targets  = build_nutrition_targets(profile, decision.priority)
plan     = build_meal_plan(profile, targets, foods)
```

ترتيب حساب الطاقة، وكل خطوة موثّقة في `EnergyBreakdown` ليراجع الأخصائي الطريق لا النتيجة:

```
BMR (Mifflin-St Jeor) → TDEE → تعديل الهدف → سقف العجز 25% → أرضية السعرات
```

| الحاجز | القيمة | لماذا |
|--------|--------|-------|
| أرضية السعرات | 1200 إناث / 1500 ذكور | أقل من ذلك لا يضمن الاحتياجات الدقيقة |
| أقصى عجز | 25% من TDEE | العجز الأكبر يستهلك العضل ويخفض الأيض |
| الإصابة الحادة | لا عجز حراري إطلاقًا | الالتئام يحتاج طاقة كاملة |
| أقصى فقد أسبوعي | 1% من وزن الجسم | تجاوزه يرفع السعرات لا يكافأ |
| مدخل خارج النطاق | استثناء صريح | لا تصحيح صامت |

**42 حالة مرجعية** في `tests/golden/` محسوبة من المعادلات مباشرة بسكربت مستقل عن كود المحرك — لا مسجَّلة من ناتج تشغيله. أي فشل فيها يعني أن قرارًا سريريًا تغيّر، ويحتاج مراجعة أخصائي وزيادة `RULE_ENGINE_VERSION`.

خصائص أمنية مطبَّقة: تجزئة **Argon2id**، رموز وصول قصيرة + رموز تحديث قابلة للإبطال، **تدوير إلزامي** للرمز عند كل تحديث مع **كشف إعادة الاستخدام** (يُبطل كل جلسات المستخدم)، رسالة فشل دخول موحّدة، وزمن استجابة ثابت يمنع حصر البُرد المسجّلة.

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
- [x] **المرحلة 1** — قاعدة البيانات والمصادقة والأدوار وسجل التدقيق
- [x] **المرحلة 2** — نموذج البيانات الكامل وآلة حالات الاعتماد
- [ ] **المرحلة 3** — المحتوى العلمي (بالتوازي — يحتاج مراجعة أخصائي)
- [x] **المرحلة 4** — محرك القواعد ⭐ (مسار التغذية؛ التأهيل مؤجَّل بـ ADR-003)
- [x] **المرحلة 5** — واجهات API ودورة الاعتماد

الخريطة الكاملة في [`docs/EXECUTION_PLAN.md`](docs/EXECUTION_PLAN.md).
