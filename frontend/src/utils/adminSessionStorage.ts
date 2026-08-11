import type { AdminSessionResponse } from '../types/adminSession.js';

export interface AdminSessionState {
  accessToken: string;
  expiresAtMs: number;
  role: 'admin';
}

const sessionListeners = new Set<() => void>();

let cachedSessionSnapshot: AdminSessionState | null = null;

function notifyAdminSessionChanged(): void {
  syncAdminSessionSnapshot();
  for (const listener of sessionListeners) {
    listener();
  }
}

function isExpired(session: AdminSessionState, nowMs: number = Date.now()): boolean {
  return nowMs >= session.expiresAtMs;
}

function resolveActiveSession(): AdminSessionState | null {
  if (cachedSessionSnapshot === null) {
    return null;
  }

  if (isExpired(cachedSessionSnapshot)) {
    cachedSessionSnapshot = null;
    return null;
  }

  return cachedSessionSnapshot;
}

/** Keep a stable snapshot reference for useSyncExternalStore subscribers. */
function syncAdminSessionSnapshot(): void {
  cachedSessionSnapshot = resolveActiveSession();
}

export function getAdminSessionSnapshot(): AdminSessionState | null {
  syncAdminSessionSnapshot();
  return cachedSessionSnapshot;
}

export function getAdminSessionServerSnapshot(): AdminSessionState | null {
  return null;
}

export function subscribeAdminSession(onStoreChange: () => void): () => void {
  syncAdminSessionSnapshot();
  sessionListeners.add(onStoreChange);
  return () => {
    sessionListeners.delete(onStoreChange);
  };
}

export function setAdminSession(response: AdminSessionResponse): AdminSessionState {
  const next: AdminSessionState = {
    accessToken: response.access_token,
    expiresAtMs: Date.now() + response.expires_in * 1000,
    role: response.role,
  };

  cachedSessionSnapshot = next;
  notifyAdminSessionChanged();
  return next;
}

export function clearAdminSession(): void {
  if (cachedSessionSnapshot === null) {
    return;
  }

  cachedSessionSnapshot = null;
  notifyAdminSessionChanged();
}

export function isAdminAuthenticated(): boolean {
  return getAdminSessionSnapshot() !== null;
}

export function getAdminAccessToken(): string | undefined {
  return getAdminSessionSnapshot()?.accessToken;
}

/** Test helper — reset in-memory session without persisting tokens. */
export function resetAdminSessionForTests(): void {
  cachedSessionSnapshot = null;
  for (const listener of sessionListeners) {
    listener();
  }
}
