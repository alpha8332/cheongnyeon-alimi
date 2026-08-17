import { Link } from 'react-router';
import type { AdminMetricCardVariant } from '@/utils/adminDashboard';

interface AdminMetricCardProps {
  label: string;
  value: string;
  description?: string;
  to?: string;
  variant?: AdminMetricCardVariant;
}

function metricCardClassName(variant: AdminMetricCardVariant): string {
  return `admin-metric-card admin-metric-card--${variant}`;
}

export default function AdminMetricCard({
  label,
  value,
  description,
  to,
  variant = 'default',
}: AdminMetricCardProps) {
  const className = metricCardClassName(variant);

  if (to) {
    return (
      <Link to={to} className={`${className} admin-metric-card--link`}>
        <span className="admin-metric-card__label">{label}</span>
        <span className="admin-metric-card__value">{value}</span>
        {description ? (
          <span className="admin-metric-card__description">{description}</span>
        ) : null}
        <span className="admin-metric-card__action">실행 상세 보기</span>
      </Link>
    );
  }

  return (
    <article className={className}>
      <span className="admin-metric-card__label">{label}</span>
      <span className="admin-metric-card__value">{value}</span>
      {description ? (
        <span className="admin-metric-card__description">{description}</span>
      ) : null}
    </article>
  );
}
