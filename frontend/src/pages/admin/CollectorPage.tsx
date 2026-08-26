import { Link } from 'react-router';
import { AdminApiError } from '@/api/adminApiError';
import CollectionRunStatusBadge from '@/components/admin/CollectionRunStatusBadge';
import ManualCollectionRunTrigger from '@/components/admin/ManualCollectionRunTrigger';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminCollectorStatusQuery } from '@/hooks/useAdminCollectorStatusQuery';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useAdminUnauthorizedRedirect } from '@/hooks/useAdminUnauthorizedRedirect';
import type {
  AdminCollectorStatusDto,
  CollectorCredentialStatus,
  CollectorRuntimeStatus,
  CollectorSourceType,
} from '@/types/adminCollector';
import type { CollectionRunTriggerResponse } from '@/types/collectionRun';
import {
  formatAdminTimestamp,
  formatCollectionRunCounts,
} from '@/utils/collectionRunDisplay';

const RUNTIME_LABELS: Record<CollectorRuntimeStatus, string> = {
  ready: '실행 준비됨',
  configuration_required: '인증정보 필요',
  unavailable: '실행 환경 없음',
  unknown: '상태 확인 필요',
};

const CREDENTIAL_LABELS: Record<CollectorCredentialStatus, string> = {
  configured: '인증정보 설정됨',
  missing: '인증정보 미설정',
  not_required: '인증정보 불필요',
  unknown: '인증정보 확인 불가',
};

const SOURCE_TYPE_LABELS: Record<CollectorSourceType, string> = {
  api: '공공 API',
  file: '공개 파일',
  web: '공식 웹',
};

function getManualRunDisabledReason(collector: AdminCollectorStatusDto) {
  if (!collector.manual_run_enabled) return '수동 실행을 지원하지 않는 수집기입니다.';
  if (collector.active_run) return '이 수집기는 이미 대기·실행 중입니다.';
  if (collector.runtime_status === 'configuration_required') {
    return '중앙 수집 워커에 필요한 인증정보가 설정되지 않았습니다.';
  }
  if (collector.runtime_status !== 'ready') {
    return '중앙 수집 워커가 준비되지 않았습니다.';
  }
  return undefined;
}

function CollectorCard({
  collector,
  accessToken,
  onTriggered,
  onUnauthorized,
}: {
  collector: AdminCollectorStatusDto;
  accessToken?: string;
  onTriggered: (response: CollectionRunTriggerResponse) => void;
  onUnauthorized: () => void;
}) {
  const disabledReason = getManualRunDisabledReason(collector);
  const lastRun = collector.last_run;

  return (
    <article className="collector-card">
      <header className="collector-card__header">
        <div>
          <p className="collector-card__type">{SOURCE_TYPE_LABELS[collector.source_type]}</p>
          <h2 className="collector-card__title">{collector.display_name}</h2>
          <code className="collector-card__source-id">{collector.source_id}</code>
        </div>
        <span
          className={`collector-runtime-badge collector-runtime-badge--${collector.runtime_status}`}
          aria-label={`실행 상태: ${RUNTIME_LABELS[collector.runtime_status]}`}
        >
          {RUNTIME_LABELS[collector.runtime_status]}
        </span>
      </header>

      <dl className="collector-card__facts">
        <div>
          <dt>활성 공개 dataset</dt>
          <dd>{collector.public_policy_count.toLocaleString('ko-KR')}건</dd>
        </div>
        <div>
          <dt>워커 등록</dt>
          <dd>
            {collector.worker_registered === null
              ? '확인 불가'
              : collector.worker_registered
                ? '등록됨'
                : '미등록'}
          </dd>
        </div>
        <div>
          <dt>인증 상태</dt>
          <dd>{CREDENTIAL_LABELS[collector.credential_status]}</dd>
        </div>
      </dl>

      <section className="collector-card__run" aria-label="최근 실행">
        <div className="collector-card__run-heading">
          <h3>최근 CollectionRun</h3>
          {lastRun ? (
            <CollectionRunStatusBadge
              status={lastRun.status}
              isStale={lastRun.is_stale}
            />
          ) : null}
        </div>
        {lastRun ? (
          <>
            <p>
              <Link to={ADMIN_APP_ROUTES.runDetail(lastRun.run_id)}>
                {lastRun.run_id.slice(0, 8)}… 상세 보기
              </Link>
              {' · '}{formatAdminTimestamp(lastRun.started_at)}
            </p>
            <p>
              {formatCollectionRunCounts(
                lastRun.inserted_count,
                lastRun.updated_count,
                lastRun.failed_count,
              )}
            </p>
          </>
        ) : (
          <p>이 환경의 실행 기록이 없습니다.</p>
        )}
      </section>

      <ManualCollectionRunTrigger
        accessToken={accessToken}
        sourceId={collector.source_id}
        sourceDisplayName={collector.display_name}
        compact
        disabled={disabledReason !== undefined}
        disabledReason={disabledReason}
        onTriggered={onTriggered}
        onUnauthorized={onUnauthorized}
      />
    </article>
  );
}

export default function CollectorPage() {
  const { accessToken } = useAdminSession();
  const { data, isLoading, isError, error, refetch } =
    useAdminCollectorStatusQuery(accessToken);
  const { redirectToLogin } = useAdminUnauthorizedRedirect({
    error,
    onRetry: () => void refetch(),
  });

  const readyCount = data?.collectors.filter(
    (collector) => collector.runtime_status === 'ready',
  ).length ?? 0;
  const publicPolicyCount = data?.collectors.reduce(
    (sum, collector) => sum + collector.public_policy_count,
    0,
  ) ?? 0;

  const errorMessage =
    error instanceof AdminApiError
      ? error.detail
      : error instanceof Error
        ? error.message
        : '수집기 상태를 불러오지 못했습니다.';

  const handleTriggered = () => {
    void refetch();
  };

  return (
    <div className="page collector-page">
      <header className="greeting collector-page__heading">
        <div>
          <h1 className="greeting__title">수집기 운영 상태</h1>
          <p className="greeting__subtitle">
            등록 소스, 중앙 queue·worker, 공개 dataset 포함 여부와 실행 이력을 확인합니다.
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => void refetch()}>
          상태 새로고침
        </button>
      </header>

      <aside className="collector-page__scope-note" role="note">
        공개 검색은 설치된 활성 dataset을 사용하므로 clone·ZIP 실행자에게 API key가
        필요하지 않습니다. 아래 인증 상태와 수동 실행은 중앙 운영자가 새 데이터를
        수집할 때만 적용되며, 수동 수집 결과가 자동으로 공개되지는 않습니다.
      </aside>

      {isLoading ? <LoadingState message="수집기 상태를 확인하는 중입니다." /> : null}
      {isError && !(error instanceof AdminApiError) ? (
        <ErrorState message={errorMessage} />
      ) : null}

      {!isLoading && !isError && data ? (
        <>
          <section className="collector-summary" aria-label="수집 환경 요약">
            <div className="collector-summary__item">
              <span>중앙 worker</span>
              <strong>{data.queue.worker_available ? `${data.queue.worker_count}개 연결` : '연결 안 됨'}</strong>
            </div>
            <div className="collector-summary__item">
              <span>queue</span>
              <strong>{data.queue.broker_available ? `${data.queue.queue_name} 준비됨` : 'broker 연결 안 됨'}</strong>
            </div>
            <div className="collector-summary__item">
              <span>실행 준비 수집기</span>
              <strong>{readyCount} / {data.collectors.length}</strong>
            </div>
            <div className="collector-summary__item">
              <span>활성 공개 정책</span>
              <strong>{publicPolicyCount.toLocaleString('ko-KR')}건</strong>
            </div>
          </section>

          <section className="collector-schedule" aria-labelledby="collector-schedule-title">
            <div>
              <h2 id="collector-schedule-title">자동 수집 스케줄</h2>
              <p>
                {data.schedule.enabled
                  ? `매일 ${String(data.schedule.cron_hour).padStart(2, '0')}:${String(data.schedule.cron_minute).padStart(2, '0')} (${data.schedule.timezone}) · ${data.schedule.source_id} · ${data.schedule.requested_count}건`
                  : '비활성화됨 — 현재 자동 수집 작업을 등록하지 않습니다.'}
              </p>
            </div>
            <span className={`collector-runtime-badge collector-runtime-badge--${data.schedule.enabled ? 'ready' : 'unknown'}`}>
              {data.schedule.enabled ? '사용 중' : '사용 안 함'}
            </span>
          </section>

          {data.collectors.length === 0 ? (
            <p className="state-message state-message--empty" role="status">
              등록된 수집기가 없습니다.
            </p>
          ) : (
            <section className="collector-grid" aria-label="등록 수집기 목록">
              {data.collectors.map((collector) => (
                <CollectorCard
                  key={collector.source_id}
                  collector={collector}
                  accessToken={accessToken}
                  onTriggered={handleTriggered}
                  onUnauthorized={redirectToLogin}
                />
              ))}
            </section>
          )}

          <p className="collector-page__footer-link">
            환경별 실행 이력은 서로 다를 수 있습니다. <Link to={ADMIN_APP_ROUTES.runs}>전체 CollectionRun 보기 →</Link>
          </p>
        </>
      ) : null}
    </div>
  );
}
