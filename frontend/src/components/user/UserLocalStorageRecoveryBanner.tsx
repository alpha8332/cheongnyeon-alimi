import { useState } from 'react';
import Button from '@/components/common/Button';
import type { UserLocalStorageRecoveryReason } from '@/types/userLocalStorage';
import {
  buildUserLocalStorageRecoveryMessage,
  dismissUserLocalStorageRecoveryNotice,
  peekUserLocalStorageRecoveryNotice,
} from '@/utils/userLocalStorageRecoveryNotice';

function readRecoveryNoticeSafely(): UserLocalStorageRecoveryReason | null {
  try {
    return peekUserLocalStorageRecoveryNotice();
  } catch {
    return null;
  }
}

function buildRecoveryMessageSafely(
  recoveryReason: UserLocalStorageRecoveryReason,
): string {
  try {
    return buildUserLocalStorageRecoveryMessage(recoveryReason);
  } catch {
    return '저장된 설정·북마크 데이터를 초기화했습니다. 변경 사항이 없으면 무시해도 됩니다.';
  }
}

export default function UserLocalStorageRecoveryBanner() {
  const [reason, setReason] = useState<UserLocalStorageRecoveryReason | null>(
    readRecoveryNoticeSafely,
  );

  if (reason === null) {
    return null;
  }

  const handleDismiss = () => {
    try {
      dismissUserLocalStorageRecoveryNotice();
    } catch {
      // Best-effort dismiss — hide banner even when storage is unavailable.
    }
    setReason(null);
  };

  return (
    <div
      className="user-local-recovery-banner"
      role="status"
      aria-live="polite"
      aria-label="저장 데이터 복구 안내"
    >
      <strong className="user-local-recovery-banner__title">
        저장 데이터를 초기화했습니다
      </strong>
      <p className="user-local-recovery-banner__message">
        {buildRecoveryMessageSafely(reason)}
      </p>
      <Button type="button" variant="secondary" onClick={handleDismiss}>
        닫기
      </Button>
    </div>
  );
}
