import { Outlet, Route, Routes } from 'react-router-dom'
import RootCauseSummaryChart from './components/rootCauseSummaryChart'
import Sidebar from './components/sidebar'
import Top5Dashboard from './components/top5dashboard'
import RankingViewAllPage from './pages/RankingViewAllPage'
import styles from './App.module.css'

function AppShell() {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.title}>
            Readiness<span className={styles.title_blue}>IQ</span>
          </h1>
          <p className={styles.subtitle}>
            Defense Logistics Readiness and Supply Visibility Platform
          </p>
          <div className={styles.meta}>
            <span>v0.1.0</span>
          </div>
        </div>
      </header>

      <div className={styles.body}>
        <Sidebar />
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function OverviewPage() {
  return (
    <>
      <RootCauseSummaryChart />
      <Top5Dashboard />
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<OverviewPage />} />
        <Route path="sites" element={<RankingViewAllPage category="sites" />} />
        <Route path="parts" element={<RankingViewAllPage category="parts" />} />
        <Route path="suppliers" element={<RankingViewAllPage category="suppliers" />} />
      </Route>
    </Routes>
  )
}
