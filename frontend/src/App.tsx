import { Outlet, Route, Routes } from 'react-router-dom'
import MetricsCardDashboard from './components/merticsCardDashboard'
import RootCauseSummaryChart from './components/rootCauseSummaryChart'
import Sidebar from './components/sidebar'
import Top5Dashboard from './components/top5dashboard'
import EntityDetailPage from './pages/EntityDetailPage'
import LoginPage from './pages/LoginPage'
import RankingViewAllPage from './pages/RankingViewAllPage'
import RegisterPage from './pages/RegisterPage'
import styles from './App.module.css'
import DateRangePicker from './components/dateRangePicker'

function AppShell() {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.headerTop}>
            <div>
              <h1 className={styles.title}>
                Readiness<span className={styles.title_blue}>IQ</span>
              </h1>
              <p className={styles.subtitle}>
                Defense Logistics Readiness and Supply Visibility Platform
              </p>
            </div>
            <div className={styles.dateRangePicker}>
              <DateRangePicker />
            </div>
          </div>
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
      <div className={styles.overviewRow}>
        <div className={styles.overviewChart}>
          <RootCauseSummaryChart />
        </div>
        <aside className={styles.overviewMetrics} aria-label="Key metrics">
          <MetricsCardDashboard />
        </aside>
      </div>
      <Top5Dashboard />
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<AppShell />}>
        <Route index element={<OverviewPage />} />
        <Route path="sites" element={<RankingViewAllPage category="sites" />} />
        <Route path="sites/:siteId" element={<EntityDetailPage category="sites" />} />
        <Route path="parts" element={<RankingViewAllPage category="parts" />} />
        <Route path="parts/:partId" element={<EntityDetailPage category="parts" />} />
        <Route path="suppliers" element={<RankingViewAllPage category="suppliers" />} />
        <Route path="suppliers/:supplierId" element={<EntityDetailPage category="suppliers" />} />
      </Route>
    </Routes>
  )
}
