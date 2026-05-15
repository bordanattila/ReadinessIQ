import styles from './top5card.module.css'

export type Top5Column =
  | { key: string; header: string; kind: 'text'; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'link'; idKey: string; path: string; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'badge'; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'criticality'; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'missionPriority'; headerAlign?: 'left' | 'right' }

export type Top5CardIcon = 'location' | 'gear' | 'building'

interface Top5CardProps {
  title: string
  icon: Top5CardIcon
  columns: Top5Column[]
  rows: Record<string, unknown>[]
  footer?: string
  viewAllHref?: string
  loading?: boolean
  error?: string | null
}

function IconLocation() {
  return (
    <svg className={styles.headerIcon} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 21s7-4.35 7-10a7 7 0 1 0-14 0c0 5.65 7 10 7 10zm0-13a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z"
      />
    </svg>
  )
}

function IconGear() {
  return (
    <svg
      className={styles.headerIcon}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
    </svg>
  )
}

function IconBuilding() {
  return (
    <svg className={styles.headerIcon} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 21V8l8-4 8 4v13M9 21v-8h6v8M4 21h16"
      />
    </svg>
  )
}

function CardIcon({ name }: { name: Top5CardIcon }) {
  switch (name) {
    case 'location':
      return <IconLocation />
    case 'gear':
      return <IconGear />
    case 'building':
      return <IconBuilding />
    default:
      return null
  }
}

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

function Cell({
  col,
  row,
}: {
  col: Top5Column
  row: Record<string, unknown>
}) {
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
        <a className={styles.cellLink} href={href}>
          {label}
        </a>
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

export default function Top5Card({
  title,
  icon,
  columns,
  rows,
  footer,
  viewAllHref,
  loading = false,
  error = null,
}: Top5CardProps) {
  return (
    <article className={styles.card}>
      <header className={styles.cardHeader}>
        <div className={styles.cardHeaderLeft}>
          <span className={styles.iconWrap}>
            <CardIcon name={icon} />
          </span>
          <h2 className={styles.title}>{title}</h2>
        </div>
        {viewAllHref ? (
          <a className={styles.viewAll} href={viewAllHref}>
            View all
          </a>
        ) : null}
      </header>

      {error ? (
        <p className={`${styles.message} ${styles.messageError}`}>{error}</p>
      ) : loading ? (
        <p className={styles.message}>Loading…</p>
      ) : rows.length === 0 ? (
        <p className={styles.message}>No data</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={col.headerAlign === 'right' ? styles.thRight : undefined}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((item, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={
                        col.kind === 'badge' || col.headerAlign === 'right'
                          ? styles.tdRight
                          : undefined
                      }
                    >
                      <Cell col={col} row={item} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {footer && !loading && !error && rows.length > 0 ? (
        <p className={styles.footer}>{footer}</p>
      ) : null}
    </article>
  )
}
