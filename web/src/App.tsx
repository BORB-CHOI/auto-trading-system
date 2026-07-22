import { useEffect, useState, type FormEvent } from 'react'
import { CandleChart } from './CandleChart'
import { fetchCandles, type CandlesResponse } from './api'
import './App.css'

export default function App() {
  const [code, setCode] = useState('005930')
  const [start, setStart] = useState('2026-01-01')
  const [end, setEnd] = useState('2026-07-16')
  const [data, setData] = useState<CandlesResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function load(e?: FormEvent) {
    e?.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetchCandles(code.trim(), start || undefined, end || undefined)
      setData(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  // 처음 한 번 자동으로 불러온다(삼성전자 기본).
  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="app">
      <header className="toolbar">
        <h1>케이스 검사기 <span className="sub">— 종목·구간 차트</span></h1>
        <form onSubmit={load} className="controls">
          <label>
            종목코드
            <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="005930" />
          </label>
          <label>
            시작
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          </label>
          <label>
            종료
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? '불러오는 중…' : '불러오기'}
          </button>
          <span className="status">
            {error ? (
              <span className="err">{error}</span>
            ) : data ? (
              <span>
                {data.name} ({data.code}) · {data.count}봉
              </span>
            ) : null}
          </span>
        </form>
      </header>
      <main className="chart-area">
        {data ? (
          <CandleChart candles={data.candles} />
        ) : (
          <div className="empty">{loading ? '' : '종목코드와 구간을 넣고 불러오기'}</div>
        )}
      </main>
    </div>
  )
}
