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
    <Card>
      <p>{message}</p>
      {onRetry ? <Button onClick={onRetry}>다시 시도</Button> : null}
    </Card>
  );
}
