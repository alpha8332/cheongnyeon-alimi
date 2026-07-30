import Card from '@/components/common/Card';

interface LoadingStateProps {
  message?: string;
}

export default function LoadingState({
  message = '데이터를 불러오는 중입니다.',
}: LoadingStateProps) {
  return (
    <Card>
      <p>{message}</p>
    </Card>
  );
}
