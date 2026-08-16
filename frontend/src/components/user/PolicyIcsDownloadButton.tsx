import Button from '@/components/common/Button';
import type { PolicyDto } from '@/types/policy';
import {
  canDownloadPolicyIcs,
  downloadPolicyIcs,
} from '@/utils/policyIcs';

interface PolicyIcsDownloadButtonProps {
  policy: PolicyDto;
  className?: string;
  label?: string;
}

export default function PolicyIcsDownloadButton({
  policy,
  className,
  label = '캘린더 (.ics) 다운로드',
}: PolicyIcsDownloadButtonProps) {
  const enabled = canDownloadPolicyIcs(policy);

  return (
    <Button
      type="button"
      variant="secondary"
      className={className}
      disabled={!enabled}
      title={
        enabled
          ? '신청 마감일을 캘린더 파일(.ics)로 다운로드합니다.'
          : '신청 종료일이 없어 캘린더 파일을 만들 수 없습니다.'
      }
      onClick={() => {
        downloadPolicyIcs(policy);
      }}
    >
      {label}
    </Button>
  );
}
