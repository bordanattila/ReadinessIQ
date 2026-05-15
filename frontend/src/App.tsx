import Sidebar from './components/sidebar'
import Top5Dashboard from './components/top5dashboard'
import styles from './App.module.css'

function App() {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.title}>Readiness<span className={styles.title_blue}>IQ</span></h1>
          <p className={styles.subtitle}>Defense Logistics Readiness and Supply Visibility Platform</p>
          <div className={styles.meta}>
            <span>v0.1.0</span>
          </div>
        </div>
      </header>

      <div className={styles.body}>
        <Sidebar />
        <main className={styles.main}>
          <Top5Dashboard />
        </main>
      </div>
    </div>
  )
}

export default App
