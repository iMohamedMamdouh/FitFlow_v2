# طريقة العمل على المشروع

---

## 1. القواعد السبعة (إلزامية)

| # | القاعدة |
|---|---------|
| 1 | **شريحة رأسية** — كل خطوة تنتهي بشيء يعمل فعليًا من قاعدة البيانات للواجهة |
| 2 | **Contract-First** — يُعرَّف مخطط Pydantic قبل كتابة المنطق |
| 3 | **أنواع من طرف لطرف** — `mypy --strict` + TypeScript strict + أنواع مولَّدة من OpenAPI |
| 4 | **محرك القواعد = دوال نقية + Golden Tests** |
| 5 | **لا دمج بدون CI خضراء** |
| 6 | **كل Migration قابلة للتراجع ومختبَرة** |
| 7 | **تكافؤ البيئات** — نفس Docker محليًا وعلى Staging والإنتاج |

التفاصيل والأسباب في [`docs/EXECUTION_PLAN.md`](docs/EXECUTION_PLAN.md).

---

## 2. دورة العمل على خطوة

كل خطوة في خطة التنفيذ لها رقم ثابت (مثل `1.3`).

```bash
# 1. فرع جديد من main
git checkout main && git pull origin main
git checkout -b feat/1.3-authentication

# 2. اشتغل، وشغّل الفحوصات باستمرار
make check

# 3. commit + push
git push -u origin feat/1.3-authentication

# 4. افتح PR، واملأ القالب بمعيار الإنجاز الخاص بالخطوة
```

**الشرط:** لا يُدمج PR إلا بعد نجاح CI بالكامل.

### تسمية الفروع

| النوع | الصيغة | مثال |
|------|--------|------|
| ميزة | `feat/<رقم الخطوة>-<وصف>` | `feat/4.3-calorie-calculator` |
| إصلاح | `fix/<وصف>` | `fix/plan-approval-race` |
| بنية تحتية | `chore/<وصف>` | `chore/upgrade-postgres` |
| توثيق | `docs/<وصف>` | `docs/rehab-protocols` |

---

## 3. رسائل الـ Commit (Conventional Commits)

```
<type>(<scope>): <وصف مختصر بصيغة الأمر>

<شرح اختياري: ليه التغيير ده، مش إيه اللي اتغير>
```

**الأنواع:** `feat` · `fix` · `docs` · `refactor` · `test` · `chore` · `perf` · `ci`

**النطاقات (scopes):** `auth` · `db` · `rules` · `ai` · `api` · `ui` · `infra`

```
feat(rules): add Mifflin-St Jeor calorie calculator

يطبّق المعادلة المعتمدة مع الحدود الآمنة من ADR-007:
حد أدنى 1200/1500 سعرة وأقصى عجز 25% من TDEE.
```

⚠️ أي commit يمس محرك القواعد يجب أن يذكر صراحة أثره على الحدود الآمنة.

---

## 4. معايير الكود

### Backend

- `mypy --strict` يمر بدون أخطاء — بدون `# type: ignore` إلا مع تعليق يشرح السبب
- كل دالة عامة لها type hints كاملة
- محرك القواعد **ممنوع** يستورد أي شيء من FastAPI أو SQLAlchemy
- الأسرار من الإعدادات فقط — لا قيم مكتوبة في الكود أبدًا
- التعليقات بالعربي مسموحة ومرحّب بها للمنطق العلمي

### Frontend

- TypeScript strict — بدون `any`
- كل النصوص عبر ملفات الترجمة، لا نصوص مكتوبة مباشرة في المكوّنات
- الاتجاه RTL افتراضي — استخدم `ms-*`/`me-*` بدل `ml-*`/`mr-*`
- الأنواع الخاصة بالـ API تُولَّد من OpenAPI، لا تُكتب يدويًا

---

## 5. الاختبارات

| الجزء | الحد الأدنى للتغطية |
|------|---------------------|
| محرك القواعد | **95%** — مع Golden Tests |
| المصادقة والصلاحيات | **80%** |
| باقي الكود | حسب الحاجة، مع تغطية المسارات الحرجة |

**قاعدة:** أي إصلاح لخطأ يبدأ باختبار يعيد إنتاج الخطأ.

---

## 6. قواعد الأمان

- ممنوع رفع `.env` أو أي مفتاح — `pre-commit` يمنع ذلك، لكن المسؤولية عليك
- كل مسار يتعامل مع بيانات مريض يحتاج اختبار عزل صريح (مريض لا يرى بيانات غيره)
- كل تعديل على كيان حساس يُسجَّل في `audit_logs`
- ممنوع تسجيل بيانات صحية في السجلات (logs)

---

## 7. Migrations

```bash
# إنشاء migration
docker compose exec backend alembic revision --autogenerate -m "add users table"

# راجع الملف المولَّد يدويًا — التوليد التلقائي ليس مضمونًا

# اختبار إلزامي قبل الـ PR
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

⚠️ أي migration تحذف عمودًا أو جدولًا تحتاج موافقة صريحة في الـ PR.
