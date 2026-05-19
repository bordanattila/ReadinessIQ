import { Link } from 'react-router-dom'
import type { Top5Column } from './top5ColumnTypes'
import styles from './top5card.module.css'

function scoreBadgeClass(score: number): string {
  if (score >= 80) return styles.badgeHigh
  if (score >= 70) return styles.badgeMed
  if (score >= 60) return styles.badgeWarn
  return styles.badgeMuted
}

function criticalityDotClass(value: string): string {
  const v = value.toLowerCase()
  if (v.includes('mission') || v === 'critical') return styles.dotCritical
  if (v.includes('high')) return styles.dotHigh
  if (v.includes('medium')) return styles.dotMedium
  return styles.dotLow
}

function missionPriorityLabel(n: number): { label: string; dotClass: string } {
  if (n >= 5) return { label: 'High', dotClass: styles.dotCritical }
  if (n >= 4) return { label: 'Medium', dotClass: styles.dotHigh }
  if (n >= 3) return { label: 'Medium', dotClass: styles.dotMedium }
  if (n >= 2) return { label: 'Medium-Low', dotClass: styles.dotWarn }
  return { label: 'Low', dotClass: styles.dotLow }
}

export function RankingCell({ col, row }: { col: Top5Column; row: Record<string, unknown> }) {
  switch (col.kind) {
    case 'text': {
      const v = row[col.key]
      return <>{v != null ? String(v) : ''}</>
    }
    case 'link': {
      const id = String(row[col.idKey] ?? '')
      const label = row[col.key] != null ? String(row[col.key]) : ''
      const href = `${col.path.replace(/\/$/, '')}/${encodeURIComponent(id)}`
      return (
        <Link className={styles.cellLink} to={href}>
          {label}
        </Link>
      )
    }
    case 'badge': {
      const raw = row[col.key]
      const score = typeof raw === 'number' ? raw : Number(raw)
      const safe = Number.isFinite(score) ? score : 0
      return (
        <span className={`${styles.badge} ${scoreBadgeClass(safe)}`}>
          {safe.toFixed(1)}
        </span>
      )
    }
    case 'criticality': {
      const value = row[col.key] != null ? String(row[col.key]) : ''
      return (
        <span className={styles.dotRow}>
          <span className={`${styles.dot} ${criticalityDotClass(value)}`} aria-hidden />
          <span>{value}</span>
        </span>
      )
    }
    case 'missionPriority': {
      const raw = row[col.key]
      const n = typeof raw === 'number' ? raw : Number(raw)
      const { label, dotClass } = missionPriorityLabel(Number.isFinite(n) ? n : 0)
      return (
        <span className={styles.dotRow}>
          <span className={`${styles.dot} ${dotClass}`} aria-hidden />
          <span>{label}</span>
        </span>
      )
    }
    default:
      return null
  }
}
