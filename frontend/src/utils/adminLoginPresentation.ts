import { AdminApiError } from '../api/adminApiError.js';

export interface AdminLoginErrorPresentation {
  kind: 'validation' | 'unauthorized' | 'cooldown' | 'server';
  message: string;
  cooldownMs?: number;
}

export const ADMIN_LOGIN_COOLDOWN_MS = 5_000;

export function mapAdminLoginError(error: unknown): AdminLoginErrorPresentation {
  if (error instanceof AdminApiError) {
    if (error.status === 422) {
      return {
        kind: 'validation',
        message: error.detail,
      };
    }

    if (error.status === 401) {
      return {
        kind: 'unauthorized',
        message: 'PIN이 올바르지 않거나 관리자 인증이 비활성화되어 있습니다.',
      };
    }

    if (error.status === 429) {
      return {
        kind: 'cooldown',
        message:
          error.detail ||
          '로그인 시도 횟수가 많습니다. 잠시 후 다시 시도해 주세요.',
        cooldownMs: ADMIN_LOGIN_COOLDOWN_MS,
      };
    }

    if (error.status === 403) {
      return {
        kind: 'unauthorized',
        message: error.detail || '관리자 권한이 없습니다.',
      };
    }

    return {
      kind: 'server',
      message: error.detail || '로그인 요청을 처리하지 못했습니다.',
    };
  }

  if (error instanceof Error) {
    return {
      kind: 'server',
      message: error.message || '로그인 요청을 처리하지 못했습니다.',
    };
  }

  return {
    kind: 'server',
    message: '로그인 요청을 처리하지 못했습니다.',
  };
}

export function isValidAdminPinInput(value: string): boolean {
  return /^\d{4}$/.test(value);
}
