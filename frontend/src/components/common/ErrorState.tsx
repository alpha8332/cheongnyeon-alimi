import Card from '@/components/common/Card';
import Button from '@/components/common/Button';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message = '정책 데이터를 불러오지 못했습니다.',
  onRetry,
}: ErrorStateProps) {
  return (
    <Card compact>
      <p className="state-message state-message--error">{message}</p>
      {onRetry ? (
        <div style={{ marginTop: '12px' }}>
          <Button variant="secondary" onClick={onRetry}>
            다시 시도
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
