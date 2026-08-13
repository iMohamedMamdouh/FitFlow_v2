"""قاعدة بداية صغيرة: أطعمة شائعة وأنواع إصابات معروفة.

**هذه ليست المرحلة 3.** المرحلة 3 تبني قاعدة كاملة (USDA + أطعمة مصرية +
200-300 تمرين + بروتوكولات تأهيل) بمراجعة أخصائي حقيقي. ما هنا هو الحد
الأدنى الذي يجعل النظام قابلًا للتشغيل والاختبار من طرف إلى طرف: بدون
أطعمة لا تُولَّد أي خطة، وبدون أنواع إصابات لا يعمل فورم التقييم.

لذلك:

* **كل صف هنا غير مراجَع علميًا** (``reviewed_by`` يبقى فارغًا). الواجهة
  تعرض ذلك للمستخدم صراحةً، والمولّد التأهيلي (خطوة 4.6) لن يستخدم هذه
  الأنواع قبل مراجعتها.
* **``phases`` فارغة عمدًا.** كتابة مراحل تأهيل مخترعة هنا تخالف ADR-003
  مخالفة مباشرة: النص الموجود يُقرأ كبروتوكول معتمد بمجرد أن يظهر في
  الواجهة. الغياب أوضح من محتوى غير مراجَع.

قيم الأطعمة لكل 100 جرام، مصدرها جداول التركيب الغذائي الشائعة (USDA
FoodData Central وما يعادلها للأصناف المحلية)، وتحتاج تدقيقًا في المرحلة 3.
"""

from __future__ import annotations

from typing import Final, NamedTuple

from app.core.enums import Allergen, BodyRegion, FoodCategory

SOURCE: Final = "starter"


class StarterFood(NamedTuple):
    slug: str
    name_ar: str
    name_en: str
    category: FoodCategory
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    allergens: tuple[Allergen, ...] = ()


class StarterInjuryType(NamedTuple):
    slug: str
    name_ar: str
    name_en: str
    body_region: BodyRegion
    description_ar: str


FOODS: Final[tuple[StarterFood, ...]] = (
    # ------------------------------------------------------------- نشويات
    StarterFood(
        "white-rice",
        "أرز أبيض مطبوخ",
        "White rice, cooked",
        FoodCategory.GRAINS,
        130,
        2.7,
        28.2,
        0.3,
        0.4,
    ),
    StarterFood(
        "baladi-bread",
        "عيش بلدي",
        "Baladi bread",
        FoodCategory.GRAINS,
        265,
        9.0,
        51.0,
        1.6,
        4.0,
        (Allergen.GLUTEN,),
    ),
    StarterFood(
        "oats",
        "شوفان",
        "Rolled oats",
        FoodCategory.GRAINS,
        389,
        16.9,
        66.3,
        6.9,
        10.6,
        (Allergen.GLUTEN,),
    ),
    StarterFood(
        "pasta",
        "مكرونة مسلوقة",
        "Pasta, cooked",
        FoodCategory.GRAINS,
        158,
        5.8,
        30.9,
        0.9,
        1.8,
        (Allergen.GLUTEN,),
    ),
    StarterFood(
        "bulgur",
        "برغل مطبوخ",
        "Bulgur, cooked",
        FoodCategory.GRAINS,
        83,
        3.1,
        18.6,
        0.2,
        4.5,
        (Allergen.GLUTEN,),
    ),
    # ------------------------------------------------------------- بروتين
    StarterFood(
        "chicken-breast",
        "صدور دجاج مشوية",
        "Grilled chicken breast",
        FoodCategory.PROTEIN,
        165,
        31.0,
        0.0,
        3.6,
        0.0,
    ),
    StarterFood(
        "lean-beef",
        "لحم بقري قليل الدهن",
        "Lean beef",
        FoodCategory.PROTEIN,
        187,
        26.1,
        0.0,
        8.5,
        0.0,
    ),
    StarterFood(
        "tilapia",
        "سمك بلطي",
        "Tilapia",
        FoodCategory.PROTEIN,
        128,
        26.2,
        0.0,
        2.7,
        0.0,
        (Allergen.FISH,),
    ),
    StarterFood(
        "canned-tuna",
        "تونة معلّبة في الماء",
        "Canned tuna in water",
        FoodCategory.PROTEIN,
        116,
        25.5,
        0.0,
        0.8,
        0.0,
        (Allergen.FISH,),
    ),
    StarterFood(
        "boiled-egg",
        "بيض مسلوق",
        "Boiled egg",
        FoodCategory.PROTEIN,
        155,
        12.6,
        1.1,
        10.6,
        0.0,
        (Allergen.EGGS,),
    ),
    StarterFood(
        "shrimp",
        "جمبري",
        "Shrimp",
        FoodCategory.PROTEIN,
        99,
        20.9,
        0.2,
        1.4,
        0.0,
        (Allergen.SHELLFISH,),
    ),
    StarterFood(
        "chicken-liver", "كبد دجاج", "Chicken liver", FoodCategory.PROTEIN, 167, 24.5, 0.9, 6.5, 0.0
    ),
    # -------------------------------------------------------------- ألبان
    StarterFood(
        "greek-yogurt",
        "زبادي يوناني قليل الدسم",
        "Greek yogurt, low fat",
        FoodCategory.DAIRY,
        59,
        10.2,
        3.6,
        0.4,
        0.0,
        (Allergen.DAIRY,),
    ),
    StarterFood(
        "cottage-cheese",
        "جبنة قريش",
        "Cottage cheese",
        FoodCategory.DAIRY,
        98,
        11.1,
        3.4,
        4.3,
        0.0,
        (Allergen.DAIRY,),
    ),
    StarterFood(
        "low-fat-milk",
        "لبن قليل الدسم",
        "Low-fat milk",
        FoodCategory.DAIRY,
        50,
        3.4,
        4.9,
        2.0,
        0.0,
        (Allergen.DAIRY,),
    ),
    StarterFood(
        "white-cheese",
        "جبنة بيضاء خفيفة الملح",
        "Low-salt white cheese",
        FoodCategory.DAIRY,
        264,
        17.0,
        4.0,
        20.0,
        0.0,
        (Allergen.DAIRY,),
    ),
    # ------------------------------------------------------------ بقوليات
    StarterFood(
        "fava-beans",
        "فول مدمس",
        "Cooked fava beans",
        FoodCategory.LEGUMES,
        110,
        7.6,
        19.7,
        0.4,
        5.4,
    ),
    StarterFood(
        "lentils", "عدس مطبوخ", "Cooked lentils", FoodCategory.LEGUMES, 116, 9.0, 20.1, 0.4, 7.9
    ),
    StarterFood(
        "chickpeas", "حمص مسلوق", "Boiled chickpeas", FoodCategory.LEGUMES, 164, 8.9, 27.4, 2.6, 7.6
    ),
    StarterFood(
        "white-beans",
        "فاصوليا بيضاء",
        "White beans",
        FoodCategory.LEGUMES,
        139,
        9.7,
        25.1,
        0.5,
        6.3,
    ),
    # -------------------------------------------------------------- خضروات
    StarterFood(
        "boiled-potato",
        "بطاطس مسلوقة",
        "Boiled potato",
        FoodCategory.VEGETABLES,
        87,
        1.9,
        20.1,
        0.1,
        1.8,
    ),
    StarterFood("cucumber", "خيار", "Cucumber", FoodCategory.VEGETABLES, 15, 0.7, 3.6, 0.1, 0.5),
    StarterFood("tomato", "طماطم", "Tomato", FoodCategory.VEGETABLES, 18, 0.9, 3.9, 0.2, 1.2),
    StarterFood(
        "spinach", "سبانخ مطبوخة", "Cooked spinach", FoodCategory.VEGETABLES, 23, 3.0, 3.8, 0.3, 2.4
    ),
    StarterFood(
        "broccoli",
        "بروكلي مسلوق",
        "Boiled broccoli",
        FoodCategory.VEGETABLES,
        35,
        2.4,
        7.2,
        0.4,
        3.3,
    ),
    StarterFood("carrot", "جزر", "Carrot", FoodCategory.VEGETABLES, 41, 0.9, 9.6, 0.2, 2.8),
    StarterFood(
        "zucchini",
        "كوسة مطبوخة",
        "Cooked zucchini",
        FoodCategory.VEGETABLES,
        17,
        1.2,
        3.1,
        0.3,
        1.0,
    ),
    # --------------------------------------------------------------- فاكهة
    StarterFood("banana", "موز", "Banana", FoodCategory.FRUITS, 89, 1.1, 22.8, 0.3, 2.6),
    StarterFood("apple", "تفاح", "Apple", FoodCategory.FRUITS, 52, 0.3, 13.8, 0.2, 2.4),
    StarterFood("orange", "برتقال", "Orange", FoodCategory.FRUITS, 47, 0.9, 11.8, 0.1, 2.4),
    StarterFood("dates", "بلح", "Dates", FoodCategory.FRUITS, 282, 2.5, 75.0, 0.4, 8.0),
    StarterFood("strawberry", "فراولة", "Strawberry", FoodCategory.FRUITS, 32, 0.7, 7.7, 0.3, 2.0),
    StarterFood("watermelon", "بطيخ", "Watermelon", FoodCategory.FRUITS, 30, 0.6, 7.6, 0.2, 0.4),
    # ---------------------------------------------------------------- دهون
    StarterFood(
        "olive-oil", "زيت زيتون", "Olive oil", FoodCategory.FATS, 884, 0.0, 0.0, 100.0, 0.0
    ),
    StarterFood("avocado", "أفوكادو", "Avocado", FoodCategory.FATS, 160, 2.0, 8.5, 14.7, 6.7),
    StarterFood(
        "tahini",
        "طحينة",
        "Tahini",
        FoodCategory.FATS,
        595,
        17.0,
        21.2,
        53.8,
        9.3,
        (Allergen.SESAME,),
    ),
    StarterFood(
        "almonds",
        "لوز",
        "Almonds",
        FoodCategory.FATS,
        579,
        21.2,
        21.6,
        49.9,
        12.5,
        (Allergen.TREE_NUTS,),
    ),
    StarterFood(
        "walnuts",
        "عين جمل",
        "Walnuts",
        FoodCategory.FATS,
        654,
        15.2,
        13.7,
        65.2,
        6.7,
        (Allergen.TREE_NUTS,),
    ),
    StarterFood(
        "peanut-butter",
        "زبدة فول سوداني",
        "Peanut butter",
        FoodCategory.FATS,
        588,
        25.1,
        19.6,
        50.4,
        6.0,
        (Allergen.PEANUTS,),
    ),
)


INJURY_TYPES: Final[tuple[StarterInjuryType, ...]] = (
    StarterInjuryType(
        "acl-tear",
        "قطع الرباط الصليبي الأمامي",
        "ACL tear",
        BodyRegion.KNEE,
        "إصابة رباط الركبة الأمامي، بجراحة أو بدونها.",
    ),
    StarterInjuryType(
        "meniscus-tear",
        "تمزّق الغضروف الهلالي",
        "Meniscus tear",
        BodyRegion.KNEE,
        "تمزّق في الغضروف الهلالي داخل مفصل الركبة.",
    ),
    StarterInjuryType(
        "patellofemoral-pain",
        "متلازمة الألم الرضفي الفخذي",
        "Patellofemoral pain syndrome",
        BodyRegion.KNEE,
        "ألم أمام الركبة يزداد مع الدرج والجلوس الطويل.",
    ),
    StarterInjuryType(
        "patellar-tendinopathy",
        "اعتلال الوتر الرضفي",
        "Patellar tendinopathy",
        BodyRegion.KNEE,
        "ألم أسفل الرضفة شائع في رياضات القفز.",
    ),
    StarterInjuryType(
        "ankle-sprain",
        "التواء الكاحل",
        "Ankle sprain",
        BodyRegion.ANKLE,
        "إصابة أربطة الكاحل، غالبًا بالجهة الخارجية.",
    ),
    StarterInjuryType(
        "plantar-fasciitis",
        "التهاب اللفافة الأخمصية",
        "Plantar fasciitis",
        BodyRegion.FOOT,
        "ألم أسفل القدم أشدّ ما يكون مع أول خطوات الصباح.",
    ),
    StarterInjuryType(
        "rotator-cuff-tendinopathy",
        "اعتلال أوتار الكفة المدوّرة",
        "Rotator cuff tendinopathy",
        BodyRegion.SHOULDER,
        "ألم كتف يزداد مع الحركات فوق مستوى الرأس.",
    ),
    StarterInjuryType(
        "shoulder-instability",
        "عدم ثبات الكتف",
        "Shoulder instability",
        BodyRegion.SHOULDER,
        "تكرار الخلع أو شبه الخلع في مفصل الكتف.",
    ),
    StarterInjuryType(
        "lateral-epicondylitis",
        "مرفق لاعب التنس",
        "Lateral epicondylitis",
        BodyRegion.ELBOW,
        "ألم الجهة الخارجية للمرفق مع القبض والرفع.",
    ),
    StarterInjuryType(
        "non-specific-low-back-pain",
        "ألم أسفل الظهر غير النوعي",
        "Non-specific low back pain",
        BodyRegion.LOWER_BACK,
        "ألم أسفل الظهر دون سبب بنيوي محدَّد.",
    ),
    StarterInjuryType(
        "lumbar-disc-herniation",
        "الانزلاق الغضروفي القطني",
        "Lumbar disc herniation",
        BodyRegion.LOWER_BACK,
        "بروز غضروفي قطني قد يصاحبه ألم مُشِعّ في الساق.",
    ),
    StarterInjuryType(
        "mechanical-neck-pain",
        "ألم الرقبة الميكانيكي",
        "Mechanical neck pain",
        BodyRegion.NECK,
        "ألم رقبة مرتبط بالوضعية والحمل المتكرر.",
    ),
    StarterInjuryType(
        "hamstring-strain",
        "شدّ العضلة المأبضية",
        "Hamstring strain",
        BodyRegion.OTHER,
        "إجهاد أو تمزّق في العضلات الخلفية للفخذ.",
    ),
)


__all__ = ["FOODS", "INJURY_TYPES", "SOURCE", "StarterFood", "StarterInjuryType"]
