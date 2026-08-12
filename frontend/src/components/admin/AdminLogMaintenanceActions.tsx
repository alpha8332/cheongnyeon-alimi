import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/common/Button';
import {
  deleteAdminLogArchive,
  rotateAdminLogCurrent,
} from '@/api/adminLog';
import { AdminApiError } from '@/api/adminApiError';
import { useApiErrorToast } from '@/hooks/useApiErrorToast';
import type { AdminLogFileListItemDto } from '@/types/adminLog';
import { mapAdminApiErrorToToast } from '@/utils/adminApiErrorToast';
import {
  buildArchiveDeleteConfirmLabel,
  isArchiveDeleteConfirmValid,
} from '@/utils/adminLogMaintenance';

interface AdminLogMaintenanceActionsProps {
  files: AdminLogFileListItemDto[];
  accessToken?: string;
  onMaintenanceComplete: () => void;
  onUnauthorized?: () => void;
}

export default function AdminLogMaintenanceActions({
  files,
  accessToken,
  onMaintenanceComplete,
  onUnauthorized,
}: AdminLogMaintenanceActionsProps) {
  const { showToast } = useApiErrorToast();
  const archiveFiles = useMemo(
    () => files.filter((file) => file.status === 'archive'),
    [files],
  );
  const [selectedArchiveId, setSelectedArchiveId] = useState('');
  const resolvedArchiveId =
    archiveFiles.find((file) => file.file_id === selectedArchiveId)?.file_id ??
    archiveFiles[0]?.file_id ??
    '';
  const [typedConfirm, setTypedConfirm] = useState('');
  const [isRotateOpen, setIsRotateOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isRotateOpen && !isDeleteOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsRotateOpen(false);
        setIsDeleteOpen(false);
        setTypedConfirm('');
        setErrorMessage(null);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isDeleteOpen, isRotateOpen]);

  const handleRotate = async () => {
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const result = await rotateAdminLogCurrent({ accessToken });
      setStatusMessage(result.message);
      setIsRotateOpen(false);
      onMaintenanceComplete();
    } catch (error) {
      if (error instanceof AdminApiError && error.status === 401) {
        onUnauthorized?.();
        return;
      }

      if (error instanceof AdminApiError) {
        showToast(mapAdminApiErrorToToast(error), {
          onRetry:
            error.status >= 500
              ? () => {
                  void handleRotate();
                }
              : undefined,
        });
      }

      setErrorMessage(
        error instanceof AdminApiError
          ? error.detail
          : '로그 rotate 요청을 처리하지 못했습니다.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteArchive = async () => {
    if (!isArchiveDeleteConfirmValid(resolvedArchiveId, typedConfirm)) {
      setErrorMessage('file_id 확인 입력이 일치하지 않습니다.');
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const result = await deleteAdminLogArchive(resolvedArchiveId, {
        accessToken,
      });
      setStatusMessage(result.message);
      setIsDeleteOpen(false);
      setTypedConfirm('');
      onMaintenanceComplete();
    } catch (error) {
      if (error instanceof AdminApiError && error.status === 401) {
        onUnauthorized?.();
        return;
      }

      if (error instanceof AdminApiError) {
        showToast(mapAdminApiErrorToToast(error), {
          onRetry:
            error.status >= 500
              ? () => {
                  void handleDeleteArchive();
                }
              : undefined,
        });
      }

      setErrorMessage(
        error instanceof AdminApiError
          ? error.detail
          : 'archive 삭제 요청을 처리하지 못했습니다.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="admin-log-maintenance" aria-label="Log maintenance">
      <h2 className="admin-log-maintenance__title">Log maintenance</h2>
      <p className="admin-log-maintenance__description">
        active log file는 직접 삭제할 수 없습니다. rotate 후 archive만 삭제하세요.
      </p>

      <div className="admin-log-maintenance__actions">
        <Button
          type="button"
          variant="secondary"
          disabled={isSubmitting}
          onClick={() => {
            setIsRotateOpen(true);
            setErrorMessage(null);
          }}
        >
          현재 log rotate
        </Button>

        <Button
          type="button"
          variant="secondary"
          disabled={isSubmitting || archiveFiles.length === 0}
          onClick={() => {
            setSelectedArchiveId(archiveFiles[0]?.file_id ?? '');
            setIsDeleteOpen(true);
            setErrorMessage(null);
          }}
        >
          archive 삭제
        </Button>
      </div>

      {statusMessage ? (
        <p className="admin-log-maintenance__status" role="status">
          {statusMessage}
        </p>
      ) : null}

      {isRotateOpen ? (
        <div
          className="admin-log-maintenance__dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="admin-log-rotate-title"
        >
          <h3 id="admin-log-rotate-title">현재 log rotate 확인</h3>
          <p>
            active log를 rotate하고 이전 archive 정리를 요청합니다. 계속할까요?
          </p>
          {errorMessage ? (
            <p className="admin-log-maintenance__error" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <div className="admin-log-maintenance__dialog-actions">
            <Button
              type="button"
              variant="secondary"
              autoFocus
              disabled={isSubmitting}
              onClick={() => setIsRotateOpen(false)}
            >
              취소
            </Button>
            <Button
              type="button"
              disabled={isSubmitting}
              onClick={() => void handleRotate()}
            >
              {isSubmitting ? '요청 중…' : 'rotate 실행'}
            </Button>
          </div>
        </div>
      ) : null}

      {isDeleteOpen ? (
        <div
          className="admin-log-maintenance__dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="admin-log-delete-title"
          aria-describedby="admin-log-delete-target"
        >
          <h3 id="admin-log-delete-title">archive 삭제 확인</h3>
          <p
            id="admin-log-delete-target"
            className="admin-log-maintenance__target"
            role="status"
            aria-live="polite"
          >
            삭제 대상 file_id: {resolvedArchiveId || '없음'}
          </p>
          <label className="admin-log-maintenance__field">
            <span className="admin-log-maintenance__label">archive file</span>
            <select
              className="admin-log-maintenance__input"
              value={resolvedArchiveId}
              onChange={(event) => setSelectedArchiveId(event.target.value)}
              disabled={isSubmitting}
              aria-label="archive file 선택"
            >
              {archiveFiles.map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.filename} ({file.file_id})
                </option>
              ))}
            </select>
          </label>
          <label className="admin-log-maintenance__field">
            <span className="admin-log-maintenance__label">
              {buildArchiveDeleteConfirmLabel(resolvedArchiveId)}
            </span>
            <input
              className="admin-log-maintenance__input"
              type="text"
              value={typedConfirm}
              onChange={(event) => setTypedConfirm(event.target.value)}
              disabled={isSubmitting}
              aria-describedby="archive-delete-help"
              aria-label={buildArchiveDeleteConfirmLabel(resolvedArchiveId)}
            />
          </label>
          <p id="archive-delete-help" className="admin-log-maintenance__help">
            active file_id는 선택할 수 없습니다.
          </p>
          {errorMessage ? (
            <p className="admin-log-maintenance__error" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <div className="admin-log-maintenance__dialog-actions">
            <Button
              type="button"
              variant="secondary"
              autoFocus
              disabled={isSubmitting}
              onClick={() => {
                setIsDeleteOpen(false);
                setTypedConfirm('');
              }}
            >
              취소
            </Button>
            <Button
              type="button"
              disabled={
                isSubmitting ||
                !isArchiveDeleteConfirmValid(resolvedArchiveId, typedConfirm)
              }
              onClick={() => void handleDeleteArchive()}
            >
              {isSubmitting ? '삭제 중…' : 'archive 삭제'}
            </Button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
