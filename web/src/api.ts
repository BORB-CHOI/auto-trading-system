// 백엔드(api/main.py) 응답 타입과 fetch 헬퍼.
// 여기서 매매 판단은 하지 않는다 — 데이터를 받아 그리기만 한다.

export type Candle = {
  time: string // 'YYYY-MM-DD'
  open: number
  high: number
  low: number
  close: number
  volume: number // 거래량(주)
  amount: number // 거래대금(원) → KLineChart turnover
}

export type CandlesResponse = {
  code: string
  name: string
  count: number
  candles: Candle[]
}

export async function fetchCandles(
  code: string,
  start?: string,
  end?: string,
): Promise<CandlesResponse> {
  const params = new URLSearchParams({ code })
  if (start) params.set('start', start)
  if (end) params.set('end', end)

  const res = await fetch(`/api/candles?${params.toString()}`)
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? `요청 실패 (${res.status})`)
  }
  return (await res.json()) as CandlesResponse
}
