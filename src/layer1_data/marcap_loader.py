"""marcap 데이터셋 로드 + 무결성 검증 (ADR-0002).

marcap = 날짜별 전종목 스냅샷.

핵심: 망해서 상장폐지된 회사도 자기 시절 행에 그대로 남아 있다.
지금 살아있는 종목만 모은 데이터로 백테스트를 하면 "망한 회사는 처음부터 안 샀다"는
뜻이 되어 수익률이 실제보다 부풀려진다 (= 살아남은 것만 보는 착시, survivorship bias).
같은 이유로 각 시점에 실제 거래되던 종목만 보이는 것도 중요하다 (point-in-time universe).

이 모듈은 그 전제가 실제로 성립하는지 검증한다. 성립하지 않으면 ADR-0002를 다시 연다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

MARCAP_DIR = Path("data/marcap/data")

# 백테스트 구간 (CLAUDE.md: 2017-01 ~ 현재)
BACKTEST_START = 2017

# Marcap = Close × Stocks 정합성 허용 오차 (부동소수점/반올림)
MARCAP_RTOL = 1e-6


def load_years(start: int, end: int, marcap_dir: Path = MARCAP_DIR) -> pd.DataFrame:
    """연도별 parquet을 읽어 하나로 합친다. end 포함."""
    frames = []
    for year in range(start, end + 1):
        path = marcap_dir / f"marcap-{year}.parquet"
        if not path.exists():
            continue
        frames.append(pd.read_parquet(path))
    if not frames:
        raise FileNotFoundError(f"{marcap_dir} 에 {start}~{end} parquet 없음")
    return pd.concat(frames, ignore_index=True)


def available_years(marcap_dir: Path = MARCAP_DIR) -> list[int]:
    return sorted(int(p.stem.split("-")[1]) for p in marcap_dir.glob("marcap-*.parquet"))


@dataclass
class DelistingEvidence:
    """망해서 사라진 회사의 흔적 — 어느 시점엔 있었는데 이후 사라진 종목."""

    total_codes: int
    survivors: int  # 마지막 날짜에도 살아있는 종목
    disappeared: int  # 중간에 사라진 종목 = 상폐 후보
    samples: pd.DataFrame


def find_delisted(df: pd.DataFrame) -> DelistingEvidence:
    """마지막 거래일 이전에 사라진 종목을 찾는다 = 망한 회사가 데이터에 남아 있는지 확인.

    disappeared > 0 이어야 한다. 0이면 지금 살아있는 종목만 담긴 데이터라는 뜻이고,
    그런 데이터로 낸 백테스트 수익률은 전부 부풀려져 있어 쓸 수 없다.
    """
    last_date = df["Date"].max()
    last_seen = df.groupby("Code")["Date"].max()
    alive = last_seen[last_seen == last_date].index

    gone = last_seen[last_seen < last_date]
    names = df.drop_duplicates("Code").set_index("Code")["Name"]
    samples = (
        pd.DataFrame({"last_date": gone}).join(names).sort_values("last_date", ascending=False)
    )

    return DelistingEvidence(
        total_codes=int(last_seen.size),
        survivors=int(alive.size),
        disappeared=int(gone.size),
        samples=samples,
    )


def check_marcap_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Marcap == Close × Stocks 인지 검증. 어긋난 행을 반환한다."""
    expected = df["Close"] * df["Stocks"]
    mismatch = ~pd.Series(
        (df["Marcap"] - expected).abs() <= (expected.abs() * MARCAP_RTOL),
        index=df.index,
    )
    return df.loc[mismatch, ["Date", "Code", "Name", "Close", "Stocks", "Marcap"]]


def check_nulls(df: pd.DataFrame) -> pd.Series:
    """백테스트에 필수인 컬럼의 결측 수."""
    required = ["Date", "Code", "Name", "Close", "Volume", "Amount", "Marcap", "Stocks", "Market"]
    return df[required].isna().sum()


def check_duplicates(df: pd.DataFrame) -> int:
    """같은 날짜에 같은 종목이 두 번 나오면 안 된다."""
    return int(df.duplicated(subset=["Date", "Code"]).sum())
