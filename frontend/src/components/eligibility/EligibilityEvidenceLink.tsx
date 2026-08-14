import type { ItemEvidenceDto } from '@/types/eligibilitySummary';
import { formatEligibilityEvidenceCollectedAt } from '@/utils/eligibilitySummaryDisplay';

interface EligibilityEvidenceLinkProps {
  evidence: ItemEvidenceDto | null;
}

export default function EligibilityEvidenceLink({
  evidence,
}: EligibilityEvidenceLinkProps) {
  if (!evidence) {
    return (
      <p className="eligibility-evidence-link eligibility-evidence-link--missing">
        원문 근거가 없어 추가 확인이 필요합니다.
      </p>
    );
  }

  return (
    <div className="eligibility-evidence-link">
      <p className="eligibility-evidence-link__meta">
        출처 {evidence.source_id} · 수집{' '}
        {formatEligibilityEvidenceCollectedAt(evidence.collected_at)}
      </p>
      <a
        className="eligibility-evidence-link__anchor"
        href={evidence.source_url}
        target="_blank"
        rel="noopener noreferrer"
      >
        원문 근거 보기
      </a>
    </div>
  );
}
