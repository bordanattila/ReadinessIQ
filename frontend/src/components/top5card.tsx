import { Link } from 'react-router-dom'
import type { Top5CardIcon, Top5Column } from './top5ColumnTypes'
import { RankingCell } from './rankingCell'
import styles from './top5card.module.css'

export type { Top5CardIcon, Top5Column } from './top5ColumnTypes'

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
      aria-hidden="true"
    >
       <path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 9 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.34-1.88l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3a2 2 0 1 1 4 0v.1A1.7 1.7 0 0 0 15 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.2.36.52.65.9.82.22.1.46.16.7.18H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
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

export function RankingHeaderIcon({ name }: { name: Top5CardIcon }) {
  return <CardIcon name={name} />
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
          <Link className={styles.viewAll} to={viewAllHref}>
            View all
          </Link>
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
                      <RankingCell col={col} row={item} />
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
