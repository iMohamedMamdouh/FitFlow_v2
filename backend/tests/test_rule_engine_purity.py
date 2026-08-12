"""الاختبار المعماري: محرك القواعد يبقى نقيًا.

القاعدة معلنة في ADR-001، والاتفاق وحده لا يحفظها. أول ``from sqlalchemy
import`` يضاف "مؤقتًا" لتسهيل استعلام يربط المنطق السريري بقاعدة البيانات،
فيصبح اختباره مستحيلًا بلا خادم — وتضيع الميزة التي بُني عليها المحرك.

الفحص ثابت (يقرأ شجرة الكود) لا ديناميكي: لا يعتمد على ما استُورد فعليًا
أثناء التشغيل، فيكشف الاستيراد المؤجَّل داخل الدوال أيضًا.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).parent.parent / "app" / "core" / "rule_engine"

# أطر ممنوعة داخل المحرك — كل واحد منها يربط المنطق ببنية تحتية.
FORBIDDEN_ROOTS = frozenset(
    {
        "sqlalchemy",
        "fastapi",
        "starlette",
        "pydantic",
        "pydantic_settings",
        "alembic",
        "asyncpg",
        "redis",
        "httpx",
        "jwt",
        "argon2",
    }
)

# الوحدات الداخلية الوحيدة المسموح للمحرك أن يعتمد عليها.
ALLOWED_APP_MODULES = frozenset({"app.core.enums"})

ENGINE_FILES = sorted(path for path in ENGINE_DIR.glob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def test_the_engine_package_is_not_empty() -> None:
    """حارس: لو تغيّر مسار المحرك، لا يمر هذا الملف صامتًا."""
    assert ENGINE_FILES, f"لم يُعثر على وحدات المحرك في {ENGINE_DIR}"


@pytest.mark.parametrize("path", ENGINE_FILES, ids=lambda path: path.name)
def test_engine_module_imports_no_framework(path: Path) -> None:
    for module in _imported_modules(path):
        root = module.split(".")[0]
        assert (
            root not in FORBIDDEN_ROOTS
        ), f"{path.name} يستورد {module} — محرك القواعد لا يعتمد على أي إطار"


@pytest.mark.parametrize("path", ENGINE_FILES, ids=lambda path: path.name)
def test_engine_module_depends_only_on_pure_internals(path: Path) -> None:
    for module in _imported_modules(path):
        if not module.startswith("app."):
            continue
        is_internal = module.startswith("app.core.rule_engine")
        assert (
            is_internal or module in ALLOWED_APP_MODULES
        ), f"{path.name} يستورد {module} — المسموح: وحدات المحرك و{sorted(ALLOWED_APP_MODULES)}"


def test_the_shared_enum_module_is_itself_pure() -> None:
    """اعتماد المحرك على app.core.enums آمن فقط ما دامت هي نقية أيضًا."""
    for module in _imported_modules(ENGINE_DIR.parent / "enums.py"):
        assert (
            module.split(".")[0] not in FORBIDDEN_ROOTS
        ), f"app/core/enums.py يستورد {module} — يجب أن تبقى بلا اعتماديات"


def test_engine_can_be_imported_without_any_framework_installed() -> None:
    """فحص ديناميكي مكمّل: لا إطار يدخل sys.modules عند استيراد المحرك."""
    import subprocess
    import sys

    script = (
        "import sys\n"
        "import app.core.rule_engine  # noqa: F401\n"
        "loaded = {name.split('.')[0] for name in sys.modules}\n"
        "forbidden = loaded & {'sqlalchemy', 'fastapi', 'pydantic', 'asyncpg'}\n"
        "print(','.join(sorted(forbidden)))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(ENGINE_DIR.parent.parent.parent),
    )

    assert (
        result.stdout.strip() == ""
    ), f"استيراد المحرك حمّل أطرًا غير مسموحة: {result.stdout.strip()}"
