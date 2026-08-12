"""تصدير مواصفة OpenAPI إلى ملف.

    python -m app.cli.export_openapi [المسار]

تُستخدم في الـ CI لتوليد أنواع TypeScript للواجهة من نفس المصدر. النتيجة:
تغيير حقل في مخطط Pydantic يكسر بناء الواجهة فورًا بدل أن يظهر كخطأ وقت
تشغيل عند مستخدم.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.main import create_app

DEFAULT_OUTPUT = Path("openapi.json")


def export(destination: Path = DEFAULT_OUTPUT) -> Path:
    spec = create_app().openapi()
    destination.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    path = export(target)
    print(f"✓ صُدّرت المواصفة إلى {path}")
