import { clearUserLocalStorage, getBrowserLocalStorage } from './userLocalStorage.js';
import { notifyFavoritePolicyIdsChanged } from './userFavoritesStorage.js';
import { notifySavedConditionsChanged } from './userConditionsStorage.js';

/** Remove entire user localStorage payload and refresh in-memory subscribers (FE5-08). */
export function resetAllUserLocalStorage(
  storage: Storage | null = getBrowserLocalStorage(),
): boolean {
  const cleared = clearUserLocalStorage(storage);
  notifyFavoritePolicyIdsChanged();
  notifySavedConditionsChanged();
  return cleared;
}
