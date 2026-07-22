"""거래비용 모델 (§6.4 거래비용 다단계, ADR-0004).

정액률 모델이라 과거 데이터 없이 입력→출력만으로 검증된다.
§6.4 의 핵심 통찰("비용이 익절을 잡아먹는다")을 회귀로 박아둔다.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.layer4_execution.costs import (
    COST_LEVELS,
    DEFAULT_COST,
    LEVEL_0_IGNORE,
    LEVEL_1_FEES,
    LEVEL_2_REALISTIC,
    LEVEL_3_STRESS,
    CostModel,
)


def test_왕복비용은_체결금액_곱하기_비율() -> None:
    # 1,000만원을 왕복(사고팔기) → 0.5% = 5만원
    assert LEVEL_2_REALISTIC.round_trip_cost(10_000_000) == pytest.approx(50_000)


def test_왕복비용은_부호를_무시한다() -> None:
    """매도 포지션 등으로 notional 이 음수여도 비용은 금액 크기에만 붙는다."""
    assert LEVEL_2_REALISTIC.round_trip_cost(-10_000_000) == pytest.approx(50_000)


def test_수준0은_비용이_없다() -> None:
    assert LEVEL_0_IGNORE.round_trip_cost(10_000_000) == 0.0
    assert LEVEL_0_IGNORE.net_return(0.03) == pytest.approx(0.03)


def test_순수익률은_왕복비용률만큼_깎인다() -> None:
    # +3% 익절, 기본 비용(0.5%) → 실수익 +2.5%
    assert LEVEL_2_REALISTIC.net_return(0.03) == pytest.approx(0.025)


def test_비용이_익절을_잡아먹는다() -> None:
    """§6.4 통찰: 목표 수익이 비용률보다 작으면 실수익은 마이너스."""
    # +0.3% 짜리 잦은 익절을 현실 비용(0.5%)로 돌리면 남는 게 없다.
    assert LEVEL_2_REALISTIC.net_return(0.003) < 0
    # 스트레스(0.8%)에선 +0.5% 익절도 마이너스.
    assert LEVEL_3_STRESS.net_return(0.005) < 0


def test_수준은_비용_오름차순이다() -> None:
    rates = [
        LEVEL_0_IGNORE.round_trip_rate,
        LEVEL_1_FEES.round_trip_rate,
        LEVEL_2_REALISTIC.round_trip_rate,
        LEVEL_3_STRESS.round_trip_rate,
    ]
    assert rates == sorted(rates)
    assert len(set(rates)) == len(rates)  # 서로 다르다


def test_기본값은_수준2_현실() -> None:
    """§6.4: 백테스트 default 는 수준 2. 이걸 바꾸면 백테스트 전제가 통째로 바뀐다."""
    assert DEFAULT_COST is LEVEL_2_REALISTIC
    assert DEFAULT_COST.round_trip_rate == pytest.approx(0.005)


def test_채택게이트_목록은_수준0을_뺀다() -> None:
    """수준 0(현실 무시)은 판정에 넣지 않는다. 1·2·3 만 비용 오름차순."""
    levels = list(COST_LEVELS.values())
    assert LEVEL_0_IGNORE not in levels
    rates = [c.round_trip_rate for c in levels]
    assert rates == sorted(rates)
    assert rates == [0.003, 0.005, 0.008]


def test_costmodel은_불변이다() -> None:
    """frozen dataclass — 실수로 비용률을 바꿔치기 못 한다."""
    with pytest.raises(FrozenInstanceError):
        CostModel(round_trip_rate=0.005).round_trip_rate = 0.001  # type: ignore[misc]
