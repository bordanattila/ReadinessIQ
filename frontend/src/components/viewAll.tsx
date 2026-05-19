import { Link } from 'react-router-dom'
import type { Top5CardIcon, Top5Column } from './top5ColumnTypes'
import { RankingCell } from './rankingCell'
import { RankingHeaderIcon } from './top5card'
import styles from './viewAll.module.css'

export interface ViewAllProps {
  title: string
  subtitle?: string
  icon: Top5CardIcon
  columns: Top5Column[]
  rows: Record<string, unknown>[]
  footer?: string
  loading?: boolean
  error?: string | null
  /** e.g. "128 sites" shown under the title */
  meta?: string
}

export default function ViewAll({
  title,
  subtitle,
  icon,
  columns,
  rows,
  footer,
  loading = false,
  error = null,
  meta,
}: ViewAllProps) {
  return (
    <article className={styles.card} aria-labelledby="view-all-title">
      <div className={styles.toolbar}>
        <Link className={styles.back} to="/">
          ← Overview
        </Link>
      </div>

      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.iconWrap}>
            <RankingHeaderIcon name={icon} />
          </span>
          <div className={styles.headerText}>
            <h1 id="view-all-title" className={styles.title}>
              {title}
            </h1>
            {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
            {meta ? <p className={styles.meta}>{meta}</p> : null}
          </div>
        </div>
      </header>

      {error ? (
        <p className={`${styles.message} ${styles.messageError}`}>{error}</p>
      ) : loading ? (
        <p className={styles.message}>Loading…</p>
      ) : rows.length === 0 ? (
        <p className={styles.message}>No data</p>
      ) : (
        <div className={styles.tableScroll}>
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
