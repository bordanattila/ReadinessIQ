import logo from '../assets/readinessiq_logo.png'
import styles from './sidebar.module.css'

export default function Sidebar() {
  return (
    <div className={styles.sidebar}>
      <img src={logo} alt="ReadinessIQ" />
      <nav>
        <ul>
            <li>
                <a href="/">Overview</a>
            </li>
            <li>
                <a href="/">Sites</a>
            </li>
            <li>
                <a href="/">Parts</a>
            </li>
            <li>
                <a href="/">Suppliers</a>
            </li>
        </ul>
      </nav>
    </div>
  )
}