import { useCallback, useSyncExternalStore } from 'react';
import type { UserSavedConditions } from '@/types/userLocalStorage';
import {
  clearSavedConditions,
  getSavedConditionsServerSnapshot,
  getSavedConditionsSnapshot,
  saveSavedConditions,
  subscribeSavedConditions,
} from '@/utils/userConditionsStorage';

export function useSavedConditions() {
  const conditions = useSyncExternalStore(
    subscribeSavedConditions,
    getSavedConditionsSnapshot,
    getSavedConditionsServerSnapshot,
  );

  const saveConditions = useCallback((input: UserSavedConditions) => {
    return saveSavedConditions(input);
  }, []);

  const clearConditions = useCallback(() => {
    return clearSavedConditions();
  }, []);

  return {
    conditions,
    saveConditions,
    clearConditions,
  };
}
