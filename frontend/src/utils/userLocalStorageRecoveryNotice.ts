import type { UserLocalStorageRecoveryReason } from '../types/userLocalStorage.js';

export const USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY =
  'cheongnyeon-alimi.user-local-recovery-notice.v1';

const RECOVERY_REASONS: ReadonlySet<UserLocalStorageRecoveryReason> = new Set([
  'corrupt',
  'unsupported_version',
  'invalid_shape',
]);

export function getBrowserSessionStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function recordUserLocalStorageRecoveryNotice(
  reason: UserLocalStorageRecoveryReason,
  storage: Storage | null = getBrowserSessionStorage(),
): void {
  if (storage === null) {
    return;
  }

  try {
    storage.setItem(USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY, reason);
  } catch {
    // Private mode or quota — banner is best-effort UX only.
  }
}

export function peekUserLocalStorageRecoveryNotice(
  storage: Storage | null = getBrowserSessionStorage(),
): UserLocalStorageRecoveryReason | null {
  if (storage === null) {
    return null;
  }

  try {
    const raw = storage.getItem(USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY);
    if (raw === null) {
      return null;
    }

    if (!RECOVERY_REASONS.has(raw as UserLocalStorageRecoveryReason)) {
      return null;
    }

    return raw as UserLocalStorageRecoveryReason;
  } catch {
    return null;
  }
}

export function dismissUserLocalStorageRecoveryNotice(
  storage: Storage | null = getBrowserSessionStorage(),
): void {
  if (storage === null) {
    return;
  }

  try {
    storage.removeItem(USER_LOCAL_RECOVERY_NOTICE_SESSION_KEY);
  } catch {
    // ignore
  }
}

export function buildUserLocalStorageRecoveryMessage(
  reason: UserLocalStorageRecoveryReason,
): string {
  switch (reason) {
    case 'corrupt':
      return '저장된 설정·북마크 데이터가 손상되어 초기화했습니다.';
    case 'unsupported_version':
      return '저장 형식이 달라 설정·북마크를 초기화했습니다.';
    case 'invalid_shape':
      return '저장 데이터 형식이 올바르지 않아 설정·북마크를 초기화했습니다.';
    default: {
      const _exhaustive: never = reason;
      return _exhaustive;
    }
  }
}
