import Card from '@/components/common/Card';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { useProgramsQuery } from '@/hooks/useProgramsQuery';

export default function DataQualityPage() {
  const { data: programs = [], isLoading, isError, refetch } = useProgramsQuery();

  if (isLoading) {
    return (
      <div>
        <h2>데이터 품질 (관리자)</h2>
        <LoadingState />
      </div>
    );
  }

  if (isError) {
    return (
      <div>
        <h2>데이터 품질 (관리자)</h2>
        <ErrorState
          message="품질 데이터를 불러오지 못했습니다."
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  return (
    <div>
      <h2>데이터 품질 (관리자)</h2>
      <p>provenance와 품질 상태는 관리자·디버깅 화면에서만 표시합니다.</p>

      {programs.map((program) => (
        <Card key={`${program.source_id}-${program.external_id}`}>
          <h3>{program.title}</h3>
          <p>
            식별: {program.source_id} / {program.external_id}
          </p>
          <p>품질 상태: {program.data_quality_status}</p>
          <div>
            <strong>provenance</strong>
            <ul>
              {program.provenance.map((entry) => (
                <li key={`${entry.raw_document_id}-${entry.document_role}`}>
                  {entry.document_role} / {entry.raw_document_id} /{' '}
                  {entry.collected_at}
                </li>
              ))}
            </ul>
          </div>
        </Card>
      ))}
    </div>
  );
}
