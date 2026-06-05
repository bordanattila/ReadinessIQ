import styles from './merticsCard.module.css'

function IconFillRate() {
    return (
        <svg width="96" height="96" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
            <title id="title">Fill Rate Clipboard Icon</title>
            <desc id="desc">Blue circular KPI icon with white clipboard checklist.</desc>
            <defs>
                <linearGradient id="bg" x1="16" y1="10" x2="82" y2="88" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#0B5FEA" />
                    <stop offset="1" stop-color="#0A47B8" />
                </linearGradient>
            </defs>
            <circle cx="48" cy="48" r="42" fill="url(#bg)" />
            <path d="M39 27H57" stroke="white" stroke-width="4" stroke-linecap="round" />
            <path d="M39 31C39 27.6863 41.6863 25 45 25H51C54.3137 25 57 27.6863 57 31V34H39V31Z" stroke="white" stroke-width="3" stroke-linejoin="round" />
            <rect x="31" y="32" width="34" height="40" rx="4" stroke="white" stroke-width="4" />
            <path d="M41 45L45 49L53 41" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M41 59L45 63L54 54" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
    )
}

function IconOnTimeDelivery() {
    return (
        <svg width="96" height="96" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
            <title id="title">On-Time Delivery Clock Icon</title>
            <desc id="desc">Green circular KPI icon with white clock.</desc>
            <defs>
                <linearGradient id="bg" x1="17" y1="12" x2="79" y2="84" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#3FA447" />
                    <stop offset="1" stop-color="#268638" />
                </linearGradient>
            </defs>
            <circle cx="48" cy="48" r="42" fill="url(#bg)" />
            <circle cx="48" cy="48" r="21" stroke="white" stroke-width="4" />
            <path d="M48 34V49L58 58" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
    )
}

function IconStockoutRate() {
    return (
        <svg width="96" height="96" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
            <title id="title">Stockout Rate Box Icon</title>
            <desc id="desc">Orange circular KPI icon with white package box.</desc>
            <defs>
                <linearGradient id="bg" x1="17" y1="10" x2="81" y2="85" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#FF8B22" />
                    <stop offset="1" stop-color="#FF6814" />
                </linearGradient>
            </defs>
            <circle cx="48" cy="48" r="42" fill="url(#bg)" />
            <path d="M48 27L67 38V60L48 71L29 60V38L48 27Z" stroke="white" stroke-width="4" stroke-linejoin="round" />
            <path d="M30 38L48 49L66 38" stroke="white" stroke-width="4" stroke-linejoin="round" />
            <path d="M48 49V70" stroke="white" stroke-width="4" stroke-linecap="round" />
            <path d="M39 32L58 43" stroke="white" stroke-width="3" stroke-linecap="round" />
        </svg>
    )
}

function IconOverallRiskScore() {
    return (
        <svg width="96" height="96" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
            <title id="title">Readiness Risk Shield Icon</title>
            <desc id="desc">Purple circular KPI icon with white warning shield.</desc>
            <defs>
                <linearGradient id="bg" x1="19" y1="12" x2="80" y2="85" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#7B54D9" />
                    <stop offset="1" stop-color="#5C3BBF" />
                </linearGradient>
            </defs>
            <circle cx="48" cy="48" r="42" fill="url(#bg)" />
            <path d="M48 25L66 32V47C66 59.5 58.5 68 48 72C37.5 68 30 59.5 30 47V32L48 25Z" stroke="white" stroke-width="4" stroke-linejoin="round" />
            <path d="M48 40V53" stroke="white" stroke-width="4" stroke-linecap="round" />
            <circle cx="48" cy="61" r="2.5" fill="white" />
        </svg>
    )
}

export type MetricsCardIcon = 'fill_rate' | 'on_time_delivery' | 'stockout_rate' | 'overall_risk_score'

function MetricsIcon({ name }: { name: MetricsCardIcon }) {
    switch (name) {
        case 'fill_rate':
            return <IconFillRate />
        case 'on_time_delivery':
            return <IconOnTimeDelivery />
        case 'stockout_rate':
            return <IconStockoutRate />
        case 'overall_risk_score':
            return <IconOverallRiskScore />
        default:
            return null
    }
}

export function RankingMetricsIcon({ name }: { name: MetricsCardIcon }) {
    return <MetricsIcon name={name} />
}

interface MetricsCardProps {
    title: string
    value: string
    icon: MetricsCardIcon
}

export default function MetricsCard({ title, value, icon }: MetricsCardProps) {
    return (
        <div className={styles.card}>
            <div className={styles.headerRow}>
                <span className={styles.icon}>
                    <MetricsIcon name={icon} />
                </span>
                <div className={styles.title}>{title}</div>
            </div>
            <div className={styles.value}>{value}</div>
        </div>
    )
}
