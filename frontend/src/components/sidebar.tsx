import { NavLink } from 'react-router-dom'
import logo from '../assets/readinessiq_logo.png'
import styles from './sidebar.module.css'

export default function Sidebar() {
  return (
    <div className={styles.sidebar}>
      <img src={logo} alt="ReadinessIQ" />
      <nav>
        <ul>
          <li>
            <NavLink to="/" end>
              Overview
            </NavLink>
          </li>
          <li>
            <NavLink to="/sites">Sites</NavLink>
          </li>
          <li>
            <NavLink to="/parts">Parts</NavLink>
          </li>
          <li>
            <NavLink to="/suppliers">Suppliers</NavLink>
          </li>
        </ul>
      </nav>
    </div>
  )
}
