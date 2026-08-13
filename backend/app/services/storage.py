"""تخزين المرفقات الطبية على القرص.

المرفقات هنا صور أشعة وتقارير — أخطر ما يمكن رفعه إلى منصة صحية، لأن
الملف المرفوع يُخزَّن ثم يُعاد تقديمه لاحقًا لمتصفح. لذلك:

* **النوع يُحدَّد من محتوى الملف لا من ترويسته.** ``content_type`` قيمة
  يرسلها العميل ويستطيع الكذب فيها؛ البايتات الأولى لا تكذب.
* **اسم الملف الأصلي لا يُستخدم في المسار أبدًا.** المفتاح يُولَّد عندنا،
  فلا يوجد مدخل نصي يمكن أن يحمل ``../`` أو امتدادًا مزدوجًا.
* **القراءة تتحقق أن المسار داخل الجذر** بعد الحل الكامل، فحتى لو تسرّب
  مفتاح مشوّه إلى قاعدة البيانات لا يخرج عن مجلد التخزين.

الواجهة مقصودة لتكون قابلة للاستبدال بتخزين كائنات (S3) لاحقًا: كل ما
يحفظه النظام هو ``storage_key`` نصي.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Final

from app.core.enums import AttachmentType

# لكل نوع مسموح: البايتات الأولى المميزة والامتداد المعتمد.
# التنسيقات محصورة عمدًا فيما يمكن عرضه بأمان أو تنزيله كمستند.
_SIGNATURES: Final[dict[str, tuple[tuple[bytes, ...], str]]] = {
    "image/jpeg": ((b"\xff\xd8\xff",), "jpg"),
    "image/png": ((b"\x89PNG\r\n\x1a\n",), "png"),
    "image/webp": ((b"RIFF",), "webp"),
    "application/pdf": ((b"%PDF-",), "pdf"),
}

ALLOWED_CONTENT_TYPES: Final[frozenset[str]] = frozenset(_SIGNATURES)

# نوع المرفق الافتراضي حسب الامتداد — المستخدم يستطيع تصحيحه في الفورم.
_DEFAULT_TYPE: Final[dict[str, AttachmentType]] = {
    "application/pdf": AttachmentType.REPORT,
}


class AttachmentRejected(Exception):
    """الملف مرفوض — الرسالة تُعرض للمستخدم كما هي."""


def _sniff(data: bytes) -> str:
    """يرجّع نوع المحتوى المستنتَج من البايتات، أو يرفض الملف."""
    for content_type, (signatures, _) in _SIGNATURES.items():
        if any(data.startswith(signature) for signature in signatures):
            # RIFF بادئة مشتركة بين WebP وWAV وAVI — نتحقق من العلامة الثانية.
            if content_type == "image/webp" and data[8:12] != b"WEBP":
                continue
            return content_type
    raise AttachmentRejected("نوع الملف غير مدعوم — المسموح: JPEG أو PNG أو WebP أو PDF")


def default_attachment_type(content_type: str) -> AttachmentType:
    return _DEFAULT_TYPE.get(content_type, AttachmentType.PHOTO)


class AttachmentStorage:
    """تخزين محلي بسيط تحت مجلد جذر واحد."""

    def __init__(self, root: Path, *, max_bytes: int) -> None:
        self._root = root.resolve()
        self._max_bytes = max_bytes

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    def _absolute(self, storage_key: str) -> Path:
        path = (self._root / storage_key).resolve()
        # الحارس الأخير: مفتاح غير متوقع لا يخرج عن الجذر مهما كان محتواه.
        if not path.is_relative_to(self._root):
            raise AttachmentRejected("مسار ملف غير صالح")
        return path

    def save(self, data: bytes, *, injury_id: uuid.UUID) -> tuple[str, str]:
        """يحفظ الملف ويرجّع ``(storage_key, content_type)`` المستنتَج."""
        if not data:
            raise AttachmentRejected("الملف فارغ")
        if len(data) > self._max_bytes:
            limit_mb = self._max_bytes // (1024 * 1024)
            raise AttachmentRejected(f"حجم الملف يتجاوز الحد المسموح ({limit_mb} ميجابايت)")

        content_type = _sniff(data)
        extension = _SIGNATURES[content_type][1]
        storage_key = f"injuries/{injury_id}/{uuid.uuid4().hex}.{extension}"

        path = self._absolute(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return storage_key, content_type

    def read(self, storage_key: str) -> bytes:
        path = self._absolute(storage_key)
        if not path.is_file():
            raise AttachmentRejected("الملف غير موجود في التخزين")
        return path.read_bytes()

    def delete(self, storage_key: str) -> None:
        self._absolute(storage_key).unlink(missing_ok=True)


def get_storage() -> AttachmentStorage:
    """يُبنى عند الطلب لا عند الاستيراد، حتى تُقرأ الإعدادات بعد ضبط البيئة."""
    from app.core.config import get_settings

    settings = get_settings()
    return AttachmentStorage(
        settings.upload_path,
        max_bytes=settings.max_upload_mb * 1024 * 1024,
    )


__all__ = [
    "ALLOWED_CONTENT_TYPES",
    "AttachmentRejected",
    "AttachmentStorage",
    "default_attachment_type",
    "get_storage",
]
