"""케이스 검사기 API (ADR-0005).

프런트(웹 차트)가 "이 종목, 이 구간"의 일봉을 받아 그릴 수 있게 marcap 을 내준다.

## 원칙 (CLAUDE.md)

- 이 서버는 **데이터를 보여주기만** 한다. BUY/SELL·포지션·주문은 여기 없다.
- 전략 로직의 정본은 파이썬(layer3)이다. 프런트는 결과를 그릴 뿐이다.
- 조회용 종목 마스터·유니버스 제외 규칙은 기존 layer1 코드를 그대로 재사용한다.

## 실행

    uvicorn api.main:app --reload --port 8000

프런트(Vite)는 dev 서버에서 `/api/*` 를 이 서버로 proxy 한다(web/vite.config.ts).
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.layer1_data.marcap_loader import available_years, load_years

# 차트에 필요한 최소 컬럼만 캐시에 담는다(메모리 절약).
_CANDLE_COLS = ["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"]

app = FastAPI(title="ATS 케이스 검사기 API", version="0.1.0")

# Vite dev 서버에서 직접 부를 때를 대비. proxy 를 쓰면 사실상 필요 없다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=8)
def _load_year_slim(year: int) -> pd.DataFrame:
    """연도별 일봉을 슬림 컬럼으로 캐시. 같은 해 재조회는 즉시 반환된다."""
    return load_years(year, year)[_CANDLE_COLS].copy()


def get_candles(code: str, start: str | None, end: str | None) -> pd.DataFrame:
    """한 종목의 일봉을 구간으로 잘라 날짜순으로 돌려준다.

    start/end 는 'YYYY-MM-DD'. 없으면 가장 최근 연도 전체를 기본 구간으로 쓴다.
    """
    code = code.strip().zfill(6)
    years = available_years()
    if not years:
        raise HTTPException(status_code=503, detail="marcap 데이터가 없습니다.")

    start_year = int(start[:4]) if start else years[-1]
    end_year = int(end[:4]) if end else years[-1]
    start_year = max(start_year, years[0])
    end_year = min(end_year, years[-1])

    frames = [_load_year_slim(y) for y in range(start_year, end_year + 1) if y in years]
    if not frames:
        return pd.DataFrame(columns=_CANDLE_COLS)

    df = pd.concat(frames, ignore_index=True)
    df = df[df["Code"] == code]
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    return df.dropna(subset=["Open", "High", "Low", "Close"]).sort_values("Date")


@app.get("/api/health")
def health() -> dict:
    years = available_years()
    return {"ok": True, "years": years}


@app.get("/api/candles")
def api_candles(
    code: str = Query(..., description="종목코드 6자리 (예: 005930)"),
    start: str | None = Query(None, description="시작일 YYYY-MM-DD"),
    end: str | None = Query(None, description="종료일 YYYY-MM-DD"),
) -> dict:
    df = get_candles(code, start, end)
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"'{code.strip().zfill(6)}' 종목의 {start or '전체'}~{end or '전체'} 구간 데이터가 없습니다.",
        )
    times = df["Date"].dt.strftime("%Y-%m-%d")
    candles = [
        {
            "time": t,
            "open": float(o),
            "high": float(h),
            "low": float(low),
            "close": float(c),
            "volume": float(v),
        }
        for t, o, h, low, c, v in zip(
            times, df["Open"], df["High"], df["Low"], df["Close"], df["Volume"], strict=True
        )
    ]
    return {
        "code": df["Code"].iloc[0],
        "name": str(df["Name"].iloc[-1]),
        "count": len(candles),
        "candles": candles,
    }
