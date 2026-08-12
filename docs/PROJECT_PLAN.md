# خطة مشروع المنصة الذكية للصحة والتأهيل الرياضي
### AI-Powered Health & Rehabilitation Platform — Full Implementation Plan

> هذه هي وثيقة الخطة الأصلية (المرجع). خطوات التنفيذ العملية المرتّبة موجودة في `docs/EXECUTION_PLAN.md`.

---

## 1. نظرة عامة على المشروع

منصة ويب ذكية تعمل كأداة **دعم قرار (Clinical Decision Support)** للأخصائيين، تجمع بين:

- **التأهيل من الإصابات** (Rehabilitation)
- **إدارة السمنة وإنقاص الوزن** (Weight Management)
- **التغذية الشخصية** (Personalized Nutrition)
- **التحليل الفسيولوجي** (Physiological Analysis)

النظام مبني على **3 طبقات ذكاء** (وده أهم قرار معماري في المشروع):

| الطبقة | الوظيفة | التقنية |
|--------|---------|---------|
| 1. قاعدة بيانات علمية | الأغذية، التمارين، بروتوكولات الإصابات | PostgreSQL |
| 2. محرك القواعد (Rule Engine) | اتخاذ القرارات وفق بروتوكولات علمية ثابتة | كود Backend (Python) |
| 3. الذكاء الاصطناعي التوليدي | تفسير البيانات وصياغة التوصيات بلغة مفهومة | Claude API / OpenAI API |

> **مبدأ ذهبي:** الـ AI لا يتخذ القرار الطبي أبدًا. القرار يأتي من الـ Rule Engine المبني على بروتوكولات علمية، والـ AI يشرح ويصيغ فقط، والأخصائي يراجع ويعتمد.

---

## 2. التقنيات والأدوات (Tech Stack)

### أسهل مسار للتنفيذ (Recommended Stack)

| المكوّن | الأداة المقترحة | ليه؟ |
|---------|----------------|------|
| **Backend Framework** | **Python + FastAPI** | أسرع framework حديث، توثيق تلقائي (Swagger)، مناسب جدًا للحسابات العلمية والـ AI |
| **Database** | **PostgreSQL 16** | مطلوبك الأساسي — ممتاز للبيانات الطبية والعلاقات المعقدة + JSONB للبيانات المرنة |
| **ORM** | SQLAlchemy 2.0 + Alembic | إدارة الجداول والـ Migrations |
| **Frontend** | **Next.js 14 (React)** | SEO + سرعة + مكتبات UI جاهزة |
| **UI Library** | Tailwind CSS + shadcn/ui | تصميم احترافي بسرعة |
| **Authentication** | JWT + FastAPI Users (أو Supabase Auth) | أدوار متعددة: مستخدم / أخصائي / مدير |
| **AI Layer** | Anthropic Claude API | تفسير البيانات وتوليد التوصيات النصية |
| **File Storage** | S3-compatible (DigitalOcean Spaces) | تخزين صور الأشعة والتقارير الطبية |
| **Charts** | Recharts / Chart.js | رسوم بيانية للوزن والتقدم |
| **Background Jobs** | Celery + Redis (أو APScheduler للبداية) | إعادة التحليل اليومي وتعديل الخطط |
| **Hosting** | DigitalOcean Droplet + Docker | عندك خبرة فيه بالفعل (Coolify يسهّلها جدًا) |
| **PDF Reports** | WeasyPrint / ReportLab | تقارير PDF للمرحلة الثانية |
| **Notifications** | Web Push + Email (Brevo) | تنبيهات المتابعة اليومية |

### بديل أسهل وأسرع (لو عايز MVP في أسابيع قليلة)

- **Supabase** (PostgreSQL + Auth + Storage + Realtime جاهزين) بدل ما تبني كل حاجة من الصفر
- Backend مصغّر FastAPI للـ Rule Engine والـ AI فقط
- ده يوفر عليك 40-50% من وقت التطوير

---

## 3. تصميم قاعدة البيانات (PostgreSQL Schema)

### الجداول الأساسية

```sql
-- المستخدمين والأدوار
users (id, email, password_hash, role, created_at)
  -- role: patient / specialist / admin

user_profiles (
  user_id, age, gender, height_cm, weight_kg,
  medical_history JSONB, chronic_diseases JSONB,
  medications JSONB, food_allergies JSONB,
  activity_level, goal, created_at
)

-- الإصابات
injuries (
  id, user_id, injury_type_id, location, injury_date,
  pain_level INT,          -- 0-10
  range_of_motion JSONB,   -- قياسات ROM لكل مفصل
  had_surgery BOOLEAN, surgery_date,
  status                   -- acute / subacute / chronic / recovered
)

injury_attachments (id, injury_id, file_url, file_type, uploaded_at)
  -- صور الأشعة والتقارير

-- القاعدة العلمية
injury_types (id, name_ar, name_en, body_region, phases JSONB)
  -- كل نوع إصابة له مراحل تأهيل موثقة

exercises (
  id, name_ar, name_en, category, target_muscles JSONB,
  difficulty, equipment, video_url,
  contraindications JSONB   -- ممنوع مع أي إصابات
)

foods (
  id, name_ar, name_en, calories_per_100g,
  protein, carbs, fat, fiber,
  category, allergens JSONB
)

-- البيانات الفسيولوجية
physiological_readings (
  id, user_id, reading_date,
  weight_kg, bmi, body_fat_pct, muscle_mass_kg,
  resting_hr, source          -- manual / smartwatch / device
)

-- الخطط
plans (
  id, user_id, plan_type,     -- rehab / nutrition / training / combined
  status,                      -- draft / pending_review / approved / active
  generated_by,                -- rule_engine version
  ai_summary TEXT,
  approved_by_specialist_id, approved_at
)

nutrition_plans (id, plan_id, daily_calories, protein_g, carbs_g, fat_g,
                 selected_foods JSONB, meals JSONB)

rehab_plans (id, plan_id, injury_id, phase, goals JSONB,
             exercises JSONB)  -- [{exercise_id, sets, reps, intensity}]

training_plans (id, plan_id, weekly_schedule JSONB)

-- المتابعة اليومية
daily_logs (
  id, user_id, log_date,
  weight_kg, pain_level,
  diet_adherence_pct, exercise_adherence_pct,
  notes
)

-- تواصل الأخصائي
specialist_notes (id, specialist_id, patient_id, plan_id, note, created_at)
specialist_patients (specialist_id, patient_id)  -- ربط الأخصائي بمرضاه
```

---

## 4. محرك القواعد (Rule Engine) — قلب المشروع

ده الجزء اللي بيفرّق مشروعك عن أي تطبيق سعرات عادي. يُبنى كـ Python module داخل الـ Backend.

### أمثلة على القواعد:

```python
# قرار الأولوية: تأهيل ولا تخسيس ولا الاثنين؟
def decide_priority(user):
    if user.has_active_injury:
        if user.injury.status == "acute":
            return "REHAB_ONLY"          # الإصابة الحادة أولًا
        elif user.bmi >= 30:
            return "REHAB_PLUS_DIET"     # تأهيل + دايت بدون تمارين مجهدة
    elif user.bmi >= 30:
        return "WEIGHT_LOSS"
    return "FITNESS"

# حساب السعرات (Mifflin-St Jeor — المعادلة العلمية المعتمدة)
def calculate_calories(profile):
    if profile.gender == "male":
        bmr = 10*profile.weight + 6.25*profile.height - 5*profile.age + 5
    else:
        bmr = 10*profile.weight + 6.25*profile.height - 5*profile.age - 161
    tdee = bmr * ACTIVITY_MULTIPLIERS[profile.activity_level]
    if profile.goal == "weight_loss":
        return tdee - 500   # عجز آمن = نص كيلو أسبوعيًا
    return tdee

# التعديل التلقائي (Plateau Detection)
def check_plateau(user):
    last_14_days = get_weight_readings(user, days=14)
    if weight_change(last_14_days) > -0.3:  # الوزن واقف
        return adjust_plan(reduce_calories=100, or_increase_activity=True)

# فلترة التمارين حسب الإصابة
def safe_exercises(user, exercises):
    return [e for e in exercises
            if user.injury_type not in e.contraindications]
```

### دور الـ AI (Claude API) بعد الـ Rule Engine:

```
Input للـ AI:  قرارات الـ Rule Engine + بيانات المستخدم
Output من الـ AI: شرح الخطة بالعربي بلغة بسيطة + إجابة أسئلة المستخدم
                  + مسودة ملاحظات للأخصائي
```

---

## 5. مراحل التنفيذ (Roadmap)

### المرحلة 0: التأسيس (أسبوع 1-2)
- [ ] إعداد الـ Repo + Docker + CI/CD
- [ ] إعداد PostgreSQL + Migrations الأولية
- [ ] نظام التسجيل والدخول بالأدوار الثلاثة (Patient / Specialist / Admin)

### المرحلة 1: البيانات الأساسية (أسبوع 3-4)
- [ ] فورم التسجيل الكامل (البيانات الشخصية + التاريخ المرضي)
- [ ] فورم تقييم الإصابة + رفع صور الأشعة (S3)
- [ ] إدخال البيانات الفسيولوجية يدويًا
- [ ] تعبئة قاعدة البيانات العلمية:
  - قاعدة أغذية (ابدأ بـ USDA FoodData Central — مجانية — وترجمها/كمّلها بالأغذية المصرية والعربية)
  - مكتبة تمارين (200-300 تمرين مع الفيديوهات والـ contraindications)
  - بروتوكولات 10-15 إصابة شائعة (كتف، ركبة ACL، كاحل، أسفل الظهر...) **بمراجعة أخصائي تأهيل حقيقي**

### المرحلة 2: محرك القواعد (أسبوع 5-7) ⭐ الأهم
- [ ] قرار الأولوية (تأهيل / تخسيس / دمج)
- [ ] حاسبة السعرات والماكروز (Mifflin-St Jeor)
- [ ] مولّد النظام الغذائي من الأطعمة المختارة فقط (خوارزمية توزيع الماكروز على الوجبات)
- [ ] مولّد برنامج التأهيل حسب مرحلة الإصابة
- [ ] مولّد برنامج اللياقة للأصحاء
- [ ] منطق التعديل التلقائي (Plateau + تقدم الإصابة)

### المرحلة 3: طبقة الذكاء الاصطناعي (أسبوع 8-9)
- [ ] ربط Claude API لشرح الخطط بالعربي
- [ ] Chat مساعد يجيب على أسئلة المستخدم (في حدود خطته فقط)
- [ ] توليد ملخص الحالة للأخصائي

### المرحلة 4: المتابعة اليومية (أسبوع 10-11)
- [ ] فورم التسجيل اليومي (وزن، ألم، التزام)
- [ ] Dashboard المستخدم برسوم بيانية (الوزن، الألم، الالتزام)
- [ ] Cron Job يومي يعيد التحليل ويقترح تعديلات

### المرحلة 5: لوحة الأخصائي (أسبوع 12-13)
- [ ] قائمة المرضى + حالة كل مريض
- [ ] مراجعة واعتماد/تعديل خطط الـ AI (**Approval Workflow** — الخطة لا تصل للمريض إلا بعد الاعتماد)
- [ ] إرسال ملاحظات
- [ ] استخراج تقارير

### المرحلة 6: لوحة المدير (أسبوع 14-15)
- [ ] إدارة المستخدمين والأخصائيين
- [ ] إدارة قواعد البيانات (أغذية / تمارين / إصابات) بواجهة CRUD
- [ ] إحصائيات عامة

### المرحلة 7: الإطلاق التجريبي (أسبوع 16)
- [ ] اختبار مع 10-20 مستخدم حقيقي تحت إشراف أخصائي
- [ ] Bug fixes + تحسين الـ Rule Engine بناءً على الملاحظات

### التوسعات المستقبلية (Phase 2)
- ربط الساعات الذكية (Google Fit API / Apple HealthKit / Fitbit API)
- تقارير PDF (WeasyPrint)
- حجز جلسات + استشارات فيديو (Cal.com مفتوح المصدر + Daily.co / Jitsi)
- تطبيق موبايل (React Native — يعيد استخدام نفس الـ API)
- لوحة تحكم للأندية ومراكز العلاج الطبيعي (Multi-tenancy)

---

## 6. هيكل المشروع (Project Structure)

```
health-platform/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routes
│   │   │   ├── auth.py
│   │   │   ├── patients.py
│   │   │   ├── specialists.py
│   │   │   ├── admin.py
│   │   │   └── plans.py
│   │   ├── core/
│   │   │   ├── rule_engine/    # ⭐ محرك القواعد
│   │   │   │   ├── priority.py
│   │   │   │   ├── nutrition.py
│   │   │   │   ├── rehab.py
│   │   │   │   └── training.py
│   │   │   └── ai/             # طبقة Claude API
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── jobs/           # Celery / cron tasks
│   ├── alembic/            # DB migrations
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── (patient)/      # واجهة المريض
│   │   ├── (specialist)/   # لوحة الأخصائي
│   │   └── (admin)/        # لوحة المدير
│   └── components/
├── docker-compose.yml      # postgres + redis + backend + frontend
└── README.md
```

---

## 7. أسهل طريقة للتنفيذ — خلاصة عملية

1. **ابدأ بـ Supabase** (PostgreSQL + Auth + Storage جاهزين) → توفر شهر تطوير كامل
2. **FastAPI صغير** يحتوي الـ Rule Engine + استدعاءات Claude API فقط
3. **Next.js + shadcn/ui** للواجهات الثلاثة
4. **انشر على DigitalOcean بـ Coolify** (نفس setup بتاع Qodeva)
5. **لا تبني كل حاجة مرة واحدة** — MVP الأول = تسجيل + تقييم + خطة غذائية ذكية + لوحة أخصائي بسيطة. التأهيل بعدها.
6. **أهم استثمار مش في الكود** — في **المحتوى العلمي**: بروتوكولات الإصابات وقاعدة التمارين لازم أخصائي حقيقي يراجعها، لأنها أساس مصداقية المنصة كلها

---

## 8. تكلفة تقديرية شهرية (تشغيل)

| البند | التكلفة |
|-------|---------|
| DigitalOcean Droplet (4GB) | ~$24 |
| DigitalOcean Spaces (تخزين ملفات) | ~$5 |
| Claude API (حسب الاستخدام) | $20-100 |
| Domain + SSL | ~$1 (SSL مجاني Let's Encrypt) |
| Supabase (لو استخدمته) | مجاني حتى → $25 Pro |
| **الإجمالي التقريبي للبداية** | **$50-150/شهر** |

---

## 9. نقاط قانونية وأمان مهمة ⚠️

- المنصة **أداة دعم قرار وليست بديلًا عن الطبيب** — لازم Disclaimer واضح + موافقة المستخدم
- **Approval Workflow إجباري**: أي خطة تأهيل لا تُفعّل إلا بعد اعتماد الأخصائي
- تشفير البيانات الطبية (at rest + in transit) — البيانات الصحية حساسة
- Backups يومية تلقائية لقاعدة البيانات
- سجل تدقيق (Audit Log) لكل تعديل على الخطط — مين عدّل إيه وامتى
