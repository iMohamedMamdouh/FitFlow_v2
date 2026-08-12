"""اختبارات مسارات فحص الصحة."""

from __future__ import annotations

from httpx import AsyncClient


async def test_liveness_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "FitFlow"}


async def test_readiness_reports_unavailable_dependencies(client: AsyncClient) -> None:
    """بدون Postgres و Redis شغالين، لازم يرجّع 503 — مش 200.

    ده يحمي من أسوأ سيناريو: حاوية تُعلن نفسها جاهزة وهي مقطوعة عن قاعدة
    البيانات، فيوجّه لها الـ load balancer طلبات تفشل.
    """
    response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert set(body["dependencies"]) == {"postgres", "redis"}
