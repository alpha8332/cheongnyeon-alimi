import { useCallback, useSyncExternalStore } from 'react';
import type { AdminSessionResponse } from '@/types/adminSession';
import {
  clearAdminSession,
  getAdminSessionServerSnapshot,
  getAdminSessionSnapshot,
  setAdminSession,
  subscribeAdminSession,
} from '@/utils/adminSessionStorage';

export function useAdminSession() {
  const session = useSyncExternalStore(
    subscribeAdminSession,
    getAdminSessionSnapshot,
    getAdminSessionServerSnapshot,
  );

  const login = useCallback((response: AdminSessionResponse) => {
    return setAdminSession(response);
  }, []);

  const logout = useCallback(() => {
    clearAdminSession();
  }, []);

  return {
    session,
    isAuthenticated: session !== null,
    accessToken: session?.accessToken,
    login,
    logout,
  };
}
