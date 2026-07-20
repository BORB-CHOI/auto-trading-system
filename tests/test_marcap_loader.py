"""marcap 무결성 검증 (ADR-0002).

데이터 실물이 필요하므로 slow 마크. `make test`(빠른 테스트)에서는 제외되고
`make test-all`에서만 돈다. data/marcap 이 없으면 skip.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.layer1_data.marcap_loader import (
    BACKTEST_START,
    MARCAP_DIR,
    available_years,
    check_duplicates,
    check_marcap_consistency,
    check_nulls,
    find_delisted,
    load_years,
)

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not MARCAP_DIR.exists(), reason="data/marcap 미조달 (ADR-0002)"),
]


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return load_years(BACKTEST_START, available_years()[-1])


def test_covers_backtest_window(df: pd.DataFrame) -> None:
    """백테스트 구간(2017-01~)을 실제로 덮는가."""
    assert df["Date"].min().year == BACKTEST_START
    assert df["Date"].max() >= pd.Timestamp("2026-01-01")


def test_망한_회사도_데이터에_남아있다(df: pd.DataFrame) -> None:
    """상폐 종목이 자기 시절 데이터에 남아 있어야 한다 — ADR-0002 채택의 핵심 전제.

    없으면 "망한 회사는 처음부터 안 샀다"는 백테스트가 되어 수익률이 전부 부풀려진다.
    (= 살아남은 것만 보는 착시, survivorship bias)
    """
    ev = find_delisted(df)
    assert ev.disappeared > 0, (
        "사라진 종목이 없다 = 지금 살아있는 종목만 담긴 데이터 = 백테스트 무효"
    )

    # 연도마다 고르게 있어야 한다. 특정 연도만 있으면 부분 수집을 의심.
    per_year = ev.samples["last_date"].dt.year.value_counts()
    covered = [y for y in range(BACKTEST_START, 2025) if per_year.get(y, 0) > 0]
    assert len(covered) >= 7, f"상폐가 일부 연도에만 존재: {sorted(per_year.index)}"


def test_종목코드는_항상_6자리다() -> None:
    """marcap은 2000-05-29 이전 코드를 숫자로 저장해 앞자리 0이 날아가 있다.

    보정하지 않으면 6자리 체계로 바뀌는 2000-05-29에 1,460개 종목이 한꺼번에
    "상장폐지"된 것처럼 보인다 (실제로는 코드만 바뀜). load_years 가 복원한다.
    """
    old = load_years(1999, 2000)
    assert (old["Code"].str.len() == 6).all()
    assert "005930" in set(old["Code"])  # 삼성전자, 보정 전에는 "5930"


def test_코드체계_변경이_상폐로_잡히지_않는다() -> None:
    """2000-05-29 코드 개편일에 대량 상폐가 잡히면 보정이 깨진 것."""
    ev = find_delisted(load_years(1999, 2001))
    on_switch = (ev.samples["last_date"] == pd.Timestamp("2000-05-26")).sum()
    assert on_switch < 50, f"코드 개편일에 {on_switch}개 소멸 — zfill 보정 확인 필요"


def test_marcap_equals_close_times_stocks(df: pd.DataFrame) -> None:
    """시총 = 종가 × 상장주식수. 어긋나면 시총 기반 universe filter를 믿을 수 없다."""
    assert check_marcap_consistency(df).empty


def test_no_nulls_in_required_columns(df: pd.DataFrame) -> None:
    assert check_nulls(df).sum() == 0


def test_no_duplicate_rows(df: pd.DataFrame) -> None:
    """(날짜, 종목) 중복이 있으면 집계가 이중 계상된다."""
    assert check_duplicates(df) == 0


def test_trading_days_are_plausible(df: pd.DataFrame) -> None:
    """한국 시장 거래일은 연 240~250일. 크게 벗어나면 누락을 의심."""
    per_year = df.groupby(df["Date"].dt.year)["Date"].nunique()
    complete = per_year[per_year.index < df["Date"].max().year]
    assert complete.between(235, 255).all(), f"거래일 수 이상: {complete.to_dict()}"
