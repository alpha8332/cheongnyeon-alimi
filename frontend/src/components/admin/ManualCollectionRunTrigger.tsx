import { useEffect, useState } from 'react';
import Button from '@/components/common/Button';
import { triggerManualCollectionRun } from '@/api/collectionRuns';
import { AdminApiError } from '@/api/adminApiError';
import { useApiErrorToast } from '@/hooks/useApiErrorToast';
import type { CollectionRunTriggerResponse } from '@/types/collectionRun';
import { mapAdminApiErrorToToast } from '@/utils/adminApiErrorToast';

interface ManualCollectionRunTriggerProps {
  accessToken?: string;
  sourceId?: string;
  sourceDisplayName?: string;
  compact?: boolean;
  disabled?: boolean;
  disabledReason?: string;
  onTriggered: (response: CollectionRunTriggerResponse) => void;
  onUnauthorized?: () => void;
}

export default function ManualCollectionRunTrigger({
  accessToken,
  sourceId,
  sourceDisplayName,
  compact = false,
  disabled = false,
  disabledReason,
  onTriggered,
  onUnauthorized,
}: ManualCollectionRunTriggerProps) {
  const { showToast } = useApiErrorToast();
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isDisabled = disabled || isSubmitting;
  const dialogTitleId = `manual-run-trigger-title-${sourceId ?? 'default'}`;

  const closeConfirmDialog = () => {
    setIsConfirmOpen(false);
  };

  useEffect(() => {
    if (!isConfirmOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeConfirmDialog();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isConfirmOpen]);

  const handleConfirm = async () => {
    setIsSubmitting(true);

    try {
      const response = await triggerManualCollectionRun(
        sourceId ? { source_id: sourceId } : {},
        { accessToken },
      );
      closeConfirmDialog();
      onTriggered(response);
    } catch (error) {
      if (error instanceof AdminApiError && error.status === 401) {
        showToast(mapAdminApiErrorToToast(error));
        onUnauthorized?.();
        return;
      }

      if (error instanceof AdminApiError) {
        showToast(mapAdminApiErrorToToast(error), {
          onRetry:
            error.status >= 500
              ? () => {
                  void handleConfirm();
                }
              : undefined,
        });
        return;
      }

      showToast({
        message: '수동 실행 요청을 처리하지 못했습니다.',
        kind: 'error',
        retryable: false,
        dedupeKey: 'manual-run-unknown-error',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section
      className={`manual-run-trigger${compact ? ' manual-run-trigger--compact' : ''}`}
      aria-label={`${sourceDisplayName ?? '수집기'} 수동 CollectionRun 실행`}
    >
      {!compact ? <div className="manual-run-trigger__header">
        <h2 className="manual-run-trigger__title">수동 실행</h2>
        <p className="manual-run-trigger__description">
          관리자 trigger로 새 CollectionRun을 queue에 등록합니다. 대기·실행 중인
          run이 있으면 버튼이 비활성화됩니다.
        </p>
      </div> : null}

      <Button
        type="button"
        variant="secondary"
        disabled={isDisabled}
        aria-disabled={isDisabled}
        onClick={() => setIsConfirmOpen(true)}
      >
        {compact ? '이 수집기 실행' : '수동 실행 요청'}
      </Button>

      {disabled && disabledReason ? (
        <p className="manual-run-trigger__hint" role="status">
          {disabledReason}
        </p>
      ) : null}

      {isConfirmOpen ? (
        <div
          className="manual-run-trigger__dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby={dialogTitleId}
        >
          <h3 id={dialogTitleId} className="manual-run-trigger__dialog-title">
            수동 실행 확인
          </h3>
          <p className="manual-run-trigger__dialog-message">
            {sourceDisplayName ? `${sourceDisplayName} 수집 작업을 ` : '새 수집 작업을 '}
            CollectionRun queue에 등록합니다. 확인 후 한 번만 요청합니다.
            계속할까요?
          </p>

          <div className="manual-run-trigger__dialog-actions">
            <Button
              type="button"
              variant="secondary"
              autoFocus
              disabled={isSubmitting}
              onClick={closeConfirmDialog}
            >
              취소
            </Button>
            <Button
              type="button"
              disabled={isSubmitting}
              onClick={() => void handleConfirm()}
            >
              {isSubmitting ? '요청 중…' : '실행'}
            </Button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
