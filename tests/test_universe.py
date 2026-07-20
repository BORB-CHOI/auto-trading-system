"""유니버스 제외 규칙 (ADR-0003).

식별 규칙은 종목명 정규식이라 오탐이 나기 쉽다. 실측에서 실제로 걸렸던
케이스를 회귀 테스트로 박아둔다 — 규칙을 손댈 때 이게 깨지면 되돌린다.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.layer1_data.universe import (
    DEFAULT_POLICY,
    ExclusionPolicy,
    apply_exclusions,
    exclusion_mask,
    exclusion_report,
    is_konex,
    is_preferred,
    is_reit,
    is_spac,
)


def frame(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Code", "Name", "Market"])


# ── 오탐 회귀: 이름에 부분 문자열이 들어가지만 해당 유형이 아닌 종목 ──


def test_메리츠는_리츠가_아니다() -> None:
    """'메리츠'의 '리츠'가 걸리면 대형 금융주 3개가 통째로 빠진다."""
    df = frame(
        [
            ("000060", "메리츠화재", "KOSPI"),
            ("138040", "메리츠금융지주", "KOSPI"),
            ("008560", "메리츠증권", "KOSPI"),
        ]
    )
    assert not is_reit(df).any()
    assert not exclusion_mask(df).any()


def test_진짜_리츠는_걸린다() -> None:
    df = frame([("330590", "롯데리츠", "KOSPI"), ("395400", "SK리츠", "KOSPI")])
    assert is_reit(df).all()


def test_아스팩오일은_스팩이_아니다() -> None:
    """이름 가운데 '스팩'이 들어가지만 정상 기업. (KONEX 종목이라 별도 규칙엔 걸린다)"""
    df = frame([("232360", "아스팩오일", "KOSDAQ")])
    assert not is_spac(df).any()
    assert not exclusion_mask(df).any()


def test_진짜_스팩은_걸린다() -> None:
    df = frame(
        [
            ("482680", "미래에셋비전스팩7호", "KOSDAQ"),
            ("123456", "KB제33호스팩", "KOSDAQ"),
            ("234567", "키움스팩4호", "KOSDAQ"),
        ]
    )
    assert is_spac(df).all()


# ── 기본 규칙 ──


def test_우선주는_코드_끝자리로_가른다() -> None:
    df = frame(
        [
            ("005930", "삼성전자", "KOSPI"),
            ("005935", "삼성전자우", "KOSPI"),
            ("005387", "현대차2우B", "KOSPI"),
        ]
    )
    assert is_preferred(df).tolist() == [False, True, True]


def test_konex는_시장으로_가른다() -> None:
    df = frame([("005930", "삼성전자", "KOSPI"), ("232360", "아스팩오일", "KONEX")])
    assert is_konex(df).tolist() == [False, True]


# ── 정책 스위치 ──


def test_정책을_끄면_제외되지_않는다() -> None:
    """CLAUDE.md: 임계값은 placeholder. drop-one 검증하려면 꺼져야 한다."""
    df = frame([("330590", "롯데리츠", "KOSPI"), ("005935", "삼성전자우", "KOSPI")])
    assert exclusion_mask(df, DEFAULT_POLICY).all()

    off = ExclusionPolicy(
        exclude_konex=False, exclude_spac=False, exclude_preferred=False, exclude_reit=False
    )
    assert not exclusion_mask(df, off).any()


def test_규칙별로_따로_끌_수_있다() -> None:
    df = frame([("330590", "롯데리츠", "KOSPI"), ("005935", "삼성전자우", "KOSPI")])
    only_reit = ExclusionPolicy(exclude_preferred=False, exclude_reit=True)
    assert exclusion_mask(df, only_reit).tolist() == [True, False]


def test_apply_exclusions는_보통주만_남긴다() -> None:
    df = frame(
        [
            ("005930", "삼성전자", "KOSPI"),
            ("005935", "삼성전자우", "KOSPI"),
            ("330590", "롯데리츠", "KOSPI"),
            ("232360", "아스팩오일", "KONEX"),
        ]
    )
    assert apply_exclusions(df)["Name"].tolist() == ["삼성전자"]


def test_리포트는_규칙별_종목수를_센다() -> None:
    df = frame(
        [
            ("005930", "삼성전자", "KOSPI"),
            ("005935", "삼성전자우", "KOSPI"),
            ("330590", "롯데리츠", "KOSPI"),
        ]
    )
    rep = exclusion_report(df).set_index("rule")["codes"]
    assert rep["우선주"] == 1
    assert rep["리츠"] == 1
    assert rep["스팩"] == 0


@pytest.mark.parametrize("name", ["삼성전자", "SK하이닉스", "메리츠화재", "아스팩오일"])
def test_정상_기업명은_스팩_리츠에_안_걸린다(name: str) -> None:
    df = frame([("000000", name, "KOSPI")])
    assert not is_spac(df).any()
    assert not is_reit(df).any()
