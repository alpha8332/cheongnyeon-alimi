import { Link, useParams } from 'react-router';
import CollectionRunStatusBadge from '@/components/admin/CollectionRunStatusBadge';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useAdminUnauthorizedRedirect } from '@/hooks/useAdminUnauthorizedRedirect';
import { useCollectionRunDetailQuery } from '@/hooks/useCollectionRunsQuery';
import type { CollectionRunDetailDto } from '@/types/collectionRun';
import {
  formatAdminTimestamp,
  getCollectionRunTriggerTypeLabel,
  getCollectionRunTypeLabel,
} from '@/utils/collectionRunDisplay';

const DETAIL_COUNT_FIELDS: Array<{
  key: keyof CollectionRunDetailDto;
  label: string;
}> = [
  { key: 'requested_count', label: 'requested' },
  { key: 'raw_document_count', label: 'raw_document' },
  { key: 'extracted_count', label: 'extracted' },
  { key: 'accepted_count', label: 'accepted' },
  { key: 'partial_count', label: 'partial' },
  { key: 'invalid_count', label: 'invalid' },
  { key: 'duplicate_count', label: 'duplicate' },
  { key: 'rejected_count', label: 'rejected' },
  { key: 'inserted_count', label: 'inserted' },
  { key: 'updated_count', label: 'updated' },
  { key: 'unchanged_count', label: 'unchanged' },
  { key: 'skipped_count', label: 'skipped' },
  { key: 'failed_count', label: 'failed' },
];

export default function CollectionRunDetailPage() {
  const { runId = '' } = useParams();
  const { accessToken } = useAdminSession();
  const { data: run, isLoading, isError, error, refetch } = useCollectionRunDetailQuery(
    runId,
    accessToken,
  );

  useAdminUnauthorizedRedirect({
    error,
    onRetry: () => void refetch(),
  });

  const errorMessage =
    error instanceof AdminApiError
      ? error.detail
      : error instanceof Error
        ? error.message
        : '실행 상세를 불러오지 못했습니다.';

  const isNotFound = !isLoading && !isError && run === null;

  return (
    <div className="page collection-run-detail-page">
      <p className="detail-back">
        <Link to={ADMIN_APP_ROUTES.runs}>← 실행 기록 목록</Link>
      </p>

      {isLoading ? (
        <LoadingState message="실행 상세를 불러오는 중입니다." />
      ) : null}

      {isNotFound ? (
        <section className="collection-run-not-found" role="alert">
          <h1 className="collection-run-not-found__title">
            실행 기록을 찾을 수 없습니다
          </h1>
          <p className="collection-run-not-found__message">
            run id <code>{runId}</code>에 해당하는 CollectionRun이 없습니다.
          </p>
        </section>
      ) : null}

      {isError && !(error instanceof AdminApiError) ? (
        <ErrorState message={errorMessage} />
      ) : null}

      {!isLoading && !isError && run ? (
        <>
          <header className="collection-run-detail-page__header">
            <h1 className="detail-title">실행 상세</h1>
            <CollectionRunStatusBadge status={run.status} isStale={run.is_stale} />
          </header>

          <dl className="collection-run-detail-grid">
            <div className="collection-run-detail-grid__item">
              <dt>run_id</dt>
              <dd>
                <code>{run.run_id}</code>
              </dd>
            </div>
            <div className="collection-run-detail-grid__item">
              <dt>source_id</dt>
              <dd>{run.source_id ?? '—'}</dd>
            </div>
            <div className="collection-run-detail-grid__item">
              <dt>run_type</dt>
              <dd>{getCollectionRunTypeLabel(run.run_type)}</dd>
            </div>
            <div className="collection-run-detail-grid__item">
              <dt>trigger_type</dt>
              <dd>{getCollectionRunTriggerTypeLabel(run.trigger_type)}</dd>
            </div>
            <div className="collection-run-detail-grid__item">
              <dt>started_at</dt>
              <dd>{formatAdminTimestamp(run.started_at)}</dd>
            </div>
            <div className="collection-run-detail-grid__item">
              <dt>finished_at</dt>
              <dd>{formatAdminTimestamp(run.finished_at)}</dd>
            </div>
            <div className="collection-run-detail-grid__item">
              <dt>error_type</dt>
              <dd>{run.error_type ?? '—'}</dd>
            </div>
          </dl>

          {run.is_stale ? (
            <p className="collection-run-detail-page__stale-note" role="note">
              이 run은 stale로 표시되었습니다. 장시간 running 상태이거나 중단된
              실행일 수 있습니다. 상태를 임의로 합치지 말고 Backend 기준을
              확인하세요.
            </p>
          ) : null}

          <section aria-label="집계 counts">
            <h2 className="collection-run-detail-page__section-title">
              Count aggregates
            </h2>
            <dl className="collection-run-detail-grid collection-run-detail-grid--counts">
              {DETAIL_COUNT_FIELDS.map((field) => (
                <div key={field.key} className="collection-run-detail-grid__item">
                  <dt>{field.label}</dt>
                  <dd>{run[field.key] as number}</dd>
                </div>
              ))}
            </dl>
          </section>
        </>
      ) : null}
    </div>
  );
}
