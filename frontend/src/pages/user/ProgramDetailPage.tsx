import { useParams } from 'react-router-dom';

export default function ProgramDetailPage() {
  const { id } = useParams<{ id: string }>();

  return <div>정책 상세 페이지 (/programs/{id})</div>;
}