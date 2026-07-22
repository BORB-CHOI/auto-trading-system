import { ProChart } from './ProChart'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header className="appbar">
        케이스 검사기 <span className="sub">— KLineChart Pro</span>
      </header>
      <main className="chart-area">
        <ProChart />
      </main>
    </div>
  )
}
