import Button from '@/components/common/Button';
import PolicyIcsDownloadButton from '@/components/user/PolicyIcsDownloadButton';
import type { PolicyDetailDto } from '@/types/policy';

interface PolicyDetailHeaderActionsProps {
  policy: PolicyDetailDto;
}

export default function PolicyDetailHeaderActions({
  policy,
}: PolicyDetailHeaderActionsProps) {
  const hasSourceUrl = Boolean(policy.source_url);

  return (
    <div className="policy-detail-summary__actions" aria-label="정책 상세 핵심 액션">
      <Button
        variant="gradient"
        className="policy-detail-summary__actions-apply"
        disabled={!hasSourceUrl}
        onClick={() => {
          if (policy.source_url) {
            window.open(policy.source_url, '_blank', 'noopener,noreferrer');
          }
        }}
      >
        공식 신청 사이트 바로가기 ↗
      </Button>
      <PolicyIcsDownloadButton
        policy={policy}
        className="policy-detail-summary__actions-ics"
        label="캘린더 (.ics) 다운로드 📅"
      />
    </div>
  );
}
