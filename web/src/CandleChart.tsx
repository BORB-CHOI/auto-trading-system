import { useEffect, useRef } from 'react'
import {
  createChart,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from 'lightweight-charts'
import type { Candle } from './api'

// 한국 관례: 상승 = 빨강, 하락 = 파랑.
const UP = '#e2483d'
const DOWN = '#3a7bd5'

export function CandleChart({ candles }: { candles: Candle[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null)

  // 차트는 한 번만 만든다.
  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: '#0e1116' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1b2027' },
        horzLines: { color: '#1b2027' },
      },
      rightPriceScale: { borderColor: '#2a2f3a' },
      timeScale: { borderColor: '#2a2f3a' },
    })

    candleRef.current = chart.addCandlestickSeries({
      upColor: UP,
      downColor: DOWN,
      borderUpColor: UP,
      borderDownColor: DOWN,
      wickUpColor: UP,
      wickDownColor: DOWN,
    })

    volumeRef.current = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    })
    volumeRef.current.priceScale().applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    })

    chartRef.current = chart
    return () => {
      chart.remove()
      chartRef.current = null
      candleRef.current = null
      volumeRef.current = null
    }
  }, [])

  // 데이터가 바뀌면 시리즈만 갱신한다.
  useEffect(() => {
    if (!candleRef.current || !volumeRef.current) return
    candleRef.current.setData(
      candles.map((c) => ({
        time: c.time as Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    )
    volumeRef.current.setData(
      candles.map((c) => ({
        time: c.time as Time,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(226,72,61,0.4)' : 'rgba(58,123,213,0.4)',
      })),
    )
    chartRef.current?.timeScale().fitContent()
  }, [candles])

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
}
