import { useEffect, useRef } from 'react'
import { registerIndicator, type KLineData } from 'klinecharts'
import {
  KLineChartPro,
  type Datafeed,
  type SymbolInfo,
  type Period,
} from '@klinecharts/pro'
import '@klinecharts/pro/dist/klinecharts-pro.css'

// 거래대금(turnover) 보조지표 — 내장엔 없어 전역 등록하면 Pro 지표 메뉴에도 뜬다.
let turnoverRegistered = false
function ensureTurnoverIndicator(): void {
  if (turnoverRegistered) return
  registerIndicator<{ turnover: number }>({
    name: 'TURNOVER',
    shortName: '거래대금',
    figures: [{ key: 'turnover', title: '거래대금: ', type: 'bar' }],
    calc: (dataList) => dataList.map((d) => ({ turnover: (d.turnover as number | undefined) ?? 0 })),
  })
  turnoverRegistered = true
}

function toDate(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10)
}

// 우리 FastAPI 백엔드를 Pro 데이터피드로 연결. 실시간 없음(과거 데이터만).
class ApiDatafeed implements Datafeed {
  async searchSymbols(search?: string): Promise<SymbolInfo[]> {
    const res = await fetch(`/api/symbols?q=${encodeURIComponent(search ?? '')}`)
    if (!res.ok) return []
    const { symbols } = (await res.json()) as {
      symbols: { ticker: string; name: string; market: string }[]
    }
    return symbols.map((s) => ({
      ticker: s.ticker,
      name: s.name,
      shortName: s.name,
      exchange: s.market,
      market: 'stocks',
      pricePrecision: 0,
      volumePrecision: 0,
      priceCurrency: 'krw',
    }))
  }

  async getHistoryKLineData(
    symbol: SymbolInfo,
    _period: Period,
    from: number,
    to: number,
  ): Promise<KLineData[]> {
    const params = new URLSearchParams({
      code: symbol.ticker,
      start: toDate(from),
      end: toDate(to),
    })
    const res = await fetch(`/api/candles?${params.toString()}`)
    if (!res.ok) return [] // 404(구간 데이터 없음) 등은 빈 배열
    const { candles } = (await res.json()) as {
      candles: {
        time: string
        open: number
        high: number
        low: number
        close: number
        volume: number
        amount: number
      }[]
    }
    return candles.map((c) => ({
      timestamp: new Date(`${c.time}T00:00:00`).getTime(),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.volume,
      turnover: c.amount,
    }))
  }

  // 과거 데이터만 — 실시간 구독 없음.
  subscribe(): void {
    // no-op
  }

  unsubscribe(): void {
    // no-op
  }
}

const DAY: Period = { multiplier: 1, timespan: 'day', text: 'D' }

// 한국식: 상승 = 빨강, 하락 = 파랑. 형광 말고 차분한 톤.
const RED = '#e01e1e'
const BLUE = '#1668d0'
const KOREAN_STYLES = {
  candle: {
    bar: {
      upColor: RED,
      downColor: BLUE,
      upBorderColor: RED,
      downBorderColor: BLUE,
      upWickColor: RED,
      downWickColor: BLUE,
    },
  },
}

export function ProChart() {
  const elRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<KLineChartPro | null>(null)

  useEffect(() => {
    const el = elRef.current
    if (!el) return
    ensureTurnoverIndicator()

    chartRef.current = new KLineChartPro({
      container: el,
      theme: 'light',
      styles: KOREAN_STYLES,
      locale: 'en-US',
      drawingBarVisible: true, // 추세선·피보나치 등 그리기 툴바
      symbol: {
        ticker: '005930',
        name: '삼성전자',
        shortName: '삼성전자',
        exchange: 'KOSPI',
        market: 'stocks',
        pricePrecision: 0,
        volumePrecision: 0,
        priceCurrency: 'krw',
      },
      period: DAY,
      periods: [DAY],
      mainIndicators: ['MA'], // 캔들 위 기본 이평선 (설정에서 기간 편집 가능)
      subIndicators: ['VOL'], // 거래량 창
      datafeed: new ApiDatafeed(),
    })

    // Pro 는 dispose API 가 없어 컨테이너를 비워 정리한다(StrictMode 중복 방지).
    return () => {
      el.innerHTML = ''
      chartRef.current = null
    }
  }, [])

  return <div ref={elRef} style={{ width: '100%', height: '100%' }} />
}
