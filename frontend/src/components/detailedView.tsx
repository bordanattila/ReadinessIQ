import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Top5Column } from './top5ColumnTypes'
import { RankingCell } from './rankingCell'
import { RankingHeaderIcon } from './top5card'
import type { Top5CardIcon } from './top5ColumnTypes'
import { filterDetailTableRows, hasActiveDetailTableSearch } from './detailTableFilter'
import styles from './detailedView.module.css'

export type DetailMetric = { label: string; value: string }

export type DetailSection =
  | { kind: 'metrics'; title: string; metrics: DetailMetric[] }
  | {
      kind: 'table'
      title: string
      columns: Top5Column[]
      rows: Record<string, unknown>[]
      emptyMessage?: string
    }

export interface DetailedViewProps {
  icon: Top5CardIcon
  title: string
  subtitle?: string
  entityId?: string
  backHref: string
  backLabel?: string
  sections: DetailSection[]
  loading?: boolean
  error?: string | null
}

function FilterableDetailTable({
  columns,
  rows,
  emptyMessage = 'No data',
  sectionTitle,
}: {
  columns: Top5Column[]
  rows: Record<string, unknown>[]
  emptyMessage?: string
  sectionTitle: string
}) {
  const [search, setSearch] = useState('')
  const filteredRows = useMemo(
    () => filterDetailTableRows(columns, rows, search),
    [columns, rows, search],
  )
  const searchId = `detail-search-${sectionTitle.replace(/\s+/g, '-').toLowerCase()}`

  if (rows.length === 0) {
    return <p className={styles.empty}>{emptyMessage}</p>
  }

  return (
    <div className={styles.tablePanel}>
      <div className={styles.tableToolbar}>
        <label className={styles.searchLabel} htmlFor={searchId}>
          Search
        </label>
        <input
          id={searchId}
          className={styles.searchInput}
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search all columns…"
          aria-label={`Search ${sectionTitle}`}
        />
        <span className={styles.resultCount} aria-live="polite">
          {filteredRows.length} of {rows.length} rows
        </span>
        {hasActiveDetailTableSearch(search) ? (
          <button type="button" className={styles.clearFilters} onClick={() => setSearch('')}>
            Clear search
          </button>
        ) : null}
      </div>

      {filteredRows.length === 0 ? (
        <p className={styles.empty}>No rows match your search.</p>
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
              {filteredRows.map((row, rowIndex) => (
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
                      <RankingCell col={col} row={row} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function DetailedView({
  icon,
  title,
  subtitle,
  entityId,
  backHref,
  backLabel = '← Back to list',
  sections,
  loading = false,
  error = null,
}: DetailedViewProps) {
  return (
    <article className={styles.card} aria-labelledby="detail-view-title">
      <div className={styles.toolbar}>
        <Link className={styles.back} to={backHref}>
          {backLabel}
        </Link>
      </div>

      <header className={styles.header}>
        <span className={styles.iconWrap}>
          <RankingHeaderIcon name={icon} />
        </span>
        <div className={styles.headerText}>
          <h1 id="detail-view-title" className={styles.title}>
            {title}
          </h1>
          {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
          {entityId ? <p className={styles.entityId}>{entityId}</p> : null}
        </div>
      </header>

      {error ? (
        <p className={`${styles.message} ${styles.messageError}`} role="alert">
          {error}
        </p>
      ) : loading ? (
        <p className={styles.message}>Loading…</p>
      ) : (
        <div className={styles.sections}>
          {sections.map((section) => (
            <section key={section.title} className={styles.section}>
              <h2 className={styles.sectionTitle}>{section.title}</h2>
              {section.kind === 'metrics' ? (
                <div className={styles.metricsGrid}>
                  {section.metrics.map((metric) => (
                    <div key={metric.label} className={styles.metricCard}>
                      <span className={styles.metricLabel}>{metric.label}</span>
                      <span className={styles.metricValue}>{metric.value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <FilterableDetailTable
                  sectionTitle={section.title}
                  columns={section.columns}
                  rows={section.rows}
                  emptyMessage={section.emptyMessage}
                />
              )}
            </section>
          ))}
        </div>
      )}
    </article>
  )
}
