import Card from '@/components/common/Card';

interface EmptyStateProps {
  message?: string;
}

export default function EmptyState({
  message = '표시할 정책이 없습니다.',
}: EmptyStateProps) {
  return (
    <Card compact>
      <p className="state-message state-message--empty">{message}</p>
    </Card>
  );
}
