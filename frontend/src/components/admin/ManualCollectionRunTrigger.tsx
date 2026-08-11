import { useState } from 'react';
import Button from '@/components/common/Button';
import { triggerManualCollectionRun } from '@/api/collectionRuns';
import { AdminApiError } from '@/api/adminApiError';
import type { CollectionRunTriggerResponse } from '@/types/collectionRun';

interface ManualCollectionRunTriggerProps {
  accessToken?: string;
  disabled?: boolean;
  disabledReason?: string;
  onTriggered: (response: CollectionRunTriggerResponse) => void;
  onUnauthorized?: () => void;
}

export default function ManualCollectionRunTrigger({
  accessToken,
  disabled = false,
  disabledReason,
  onTriggered,
  onUnauthorized,
}: ManualCollectionRunTriggerProps) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isDisabled = disabled || isSubmitting;

  const handleConfirm = async () => {
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await triggerManualCollectionRun({}, { accessToken });
      setIsConfirmOpen(false);
      onTriggered(response);
    } catch (error) {
      if (error instanceof AdminApiError && error.status === 401) {
        onUnauthorized?.();
        setErrorMessage('세션이 만료되었습니다. 다시 로그인해 주세요.');
        return;
      }

      const detail =
        error instanceof AdminApiError
          ? error.detail
          : '수동 실행 요청을 처리하지 못했습니다.';
      setErrorMessage(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="manual-run-trigger" aria-label="수동 CollectionRun 실행">
      <div className="manual-run-trigger__header">
        <h2 className="manual-run-trigger__title">수동 실행</h2>
        <p className="manual-run-trigger__description">
          관리자 trigger로 새 CollectionRun을 시작합니다. 실행 중인 run이 있으면
          버튼이 비활성화됩니다.
        </p>
      </div>

      <Button
        type="button"
        variant="secondary"
        disabled={isDisabled}
        aria-disabled={isDisabled}
        onClick={() => setIsConfirmOpen(true)}
      >
        수동 실행 요청
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
          aria-labelledby="manual-run-trigger-title"
        >
          <h3 id="manual-run-trigger-title" className="manual-run-trigger__dialog-title">
            수동 실행 확인
          </h3>
          <p className="manual-run-trigger__dialog-message">
            새 CollectionRun을 시작합니다. 중복 제출을 방지하기 위해 확인 후 한
            번만 실행됩니다. 계속할까요?
          </p>

          {errorMessage ? (
            <p className="manual-run-trigger__error" role="alert">
              {errorMessage}
            </p>
          ) : null}

          <div className="manual-run-trigger__dialog-actions">
            <Button
              type="button"
              variant="secondary"
              autoFocus
              disabled={isSubmitting}
              onClick={() => {
                setIsConfirmOpen(false);
                setErrorMessage(null);
              }}
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
