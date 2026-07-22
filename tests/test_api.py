"""케이스 검사기 API (ADR-0005).

실제 marcap 데이터가 있어야 도는 통합 테스트라 slow 로 표시한다.
데이터가 없으면 skip — 데이터 경로(요청→marcap→JSON)가 살아있는지 확인하는 용도.
"""

from __future__ import annotations

import pytest
from api.main import app
from fastapi.testclient import TestClient

from src.layer1_data.marcap_loader import available_years

pytestmark = pytest.mark.slow

client = TestClient(app)


@pytest.fixture(autouse=True)
def _require_data() -> None:
    if not available_years():
        pytest.skip("marcap 데이터 없음")


def test_health_returns_years() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert len(body["years"]) > 0


def test_candles_samsung_shape() -> None:
    r = client.get(
        "/api/candles", params={"code": "005930", "start": "2026-01-01", "end": "2026-07-16"}
    )
    assert r.status_code == 200
    j = r.json()
    assert j["name"] == "삼성전자"
    assert j["count"] > 0
    assert set(j["candles"][0]) == {"time", "open", "high", "low", "close", "volume", "amount"}
    # 날짜 오름차순이어야 차트가 제대로 그려진다.
    times = [c["time"] for c in j["candles"]]
    assert times == sorted(times)


def test_code_zfill_normalizes() -> None:
    """'5930' 처럼 앞자리 0 이 빠진 코드도 삼성전자로 정규화된다(ADR-0003)."""
    r = client.get(
        "/api/candles", params={"code": "5930", "start": "2026-07-01", "end": "2026-07-16"}
    )
    assert r.status_code == 200
    assert r.json()["code"] == "005930"


def test_unknown_code_returns_404() -> None:
    r = client.get(
        "/api/candles", params={"code": "000000", "start": "2026-01-01", "end": "2026-02-01"}
    )
    assert r.status_code == 404


def _min_overnight_ratio(candles: list[dict]) -> float:
    closes = [c["close"] for c in candles]
    return min(b / a for a, b in zip(closes[:-1], closes[1:], strict=False))


def test_split_adjustment_removes_cliff() -> None:
    """삼성전자 2018-05-04 50:1 분할이 보정으로 연속이 된다(ADR-0006)."""
    params = {"code": "005930", "start": "2018-04-30", "end": "2018-05-08"}
    raw = client.get("/api/candles", params={**params, "adjust": "false"}).json()
    adj = client.get("/api/candles", params={**params, "adjust": "true"}).json()

    # 원주가엔 분할 절벽(하루 -98%), 보정하면 연속.
    assert _min_overnight_ratio(raw["candles"]) < 0.1
    assert _min_overnight_ratio(adj["candles"]) > 0.8
    # 분할 전 보정가 ≈ 원주가 / 50
    assert abs(adj["candles"][0]["close"] - raw["candles"][0]["close"] / 50) < 1.0


def test_recent_window_unchanged_by_adjust() -> None:
    """분할 없는 최근 구간은 보정해도 원주가와 같다."""
    params = {"code": "005930", "start": "2026-07-01", "end": "2026-07-16"}
    raw = client.get("/api/candles", params={**params, "adjust": "false"}).json()
    adj = client.get("/api/candles", params={**params, "adjust": "true"}).json()
    raw_c = [round(c["close"], 2) for c in raw["candles"]]
    adj_c = [round(c["close"], 2) for c in adj["candles"]]
    assert raw_c == adj_c
