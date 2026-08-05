import Button from '@/components/common/Button';
import type { PolicySearchErrorPresentation } from '@/types/policySearchErrors';
import './PolicySearchShell.css';

interface PolicySearchErrorShellProps {
  presentation: PolicySearchErrorPresentation;
  onRetry?: () => void;
}

export default function PolicySearchErrorShell({
  presentation,
  onRetry,
}: PolicySearchErrorShellProps) {
  return (
    <section
      className="policy-search-shell policy-search-shell--error"
      role="alert"
      aria-label="검색 오류"
    >
      <div className="policy-search-shell__icon" aria-hidden="true">
        ⚠️
      </div>
      <h2 className="policy-search-shell__title">{presentation.title}</h2>
      <p className="policy-search-shell__message">{presentation.message}</p>
      {presentation.retryable && onRetry ? (
        <div className="policy-search-shell__actions">
          <Button variant="primary" onClick={onRetry}>
            다시 시도
          </Button>
        </div>
      ) : null}
    </section>
  );
}
