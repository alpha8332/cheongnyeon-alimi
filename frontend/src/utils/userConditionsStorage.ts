import type { UserSavedConditions } from '../types/userLocalStorage.js';
import { USER_LOCAL_STORAGE_KEY } from '../types/userLocalStorage.js';
import {
  readUserLocalStorage,
  updateUserLocalStorage,
} from './userLocalStorage.js';

const conditionListeners = new Set<() => void>();

let cachedSavedConditionsSnapshot: UserSavedConditions | null = null;

function savedConditionsEqual(
  left: UserSavedConditions | null,
  right: UserSavedConditions | null,
): boolean {
  if (left === right) {
    return true;
  }

  if (left === null || right === null) {
    return false;
  }

  return (
    left.region === right.region &&
    left.age === right.age &&
    left.category === right.category
  );
}

/** Keep a stable snapshot reference for useSyncExternalStore subscribers. */
function syncSavedConditionsSnapshotFromStorage(): void {
  const next = readSavedConditions();
  if (savedConditionsEqual(cachedSavedConditionsSnapshot, next)) {
    return;
  }

  cachedSavedConditionsSnapshot =
    next === null ? null : { ...next };
}

if (typeof window !== 'undefined') {
  syncSavedConditionsSnapshotFromStorage();
}

export interface SaveSavedConditionsResult {
  conditions: UserSavedConditions | null;
  changed: boolean;
}

export interface ClearSavedConditionsResult {
  conditions: UserSavedConditions | null;
  favorites: readonly number[];
  changed: boolean;
}

export function readSavedConditions(): UserSavedConditions | null {
  return readUserLocalStorage().data.conditions;
}

export function notifySavedConditionsChanged(): void {
  syncSavedConditionsSnapshotFromStorage();

  for (const listener of conditionListeners) {
    listener();
  }
}

export function subscribeSavedConditions(onStoreChange: () => void): () => void {
  syncSavedConditionsSnapshotFromStorage();
  conditionListeners.add(onStoreChange);

  if (typeof window !== 'undefined') {
    const onStorage = (event: StorageEvent) => {
      if (event.key === null || event.key === USER_LOCAL_STORAGE_KEY) {
        syncSavedConditionsSnapshotFromStorage();
        onStoreChange();
      }
    };
    window.addEventListener('storage', onStorage);

    return () => {
      conditionListeners.delete(onStoreChange);
      window.removeEventListener('storage', onStorage);
    };
  }

  return () => {
    conditionListeners.delete(onStoreChange);
  };
}

export function getSavedConditionsSnapshot(): UserSavedConditions | null {
  return cachedSavedConditionsSnapshot;
}

export function getSavedConditionsServerSnapshot(): UserSavedConditions | null {
  return null;
}

/**
 * Persist region·age·category. Empty or invalid fields normalize to null;
 * all-empty payload stores `conditions: null`.
 */
export function saveSavedConditions(
  input: UserSavedConditions,
): SaveSavedConditionsResult {
  const before = readSavedConditions();
  const snapshot = updateUserLocalStorage({ conditions: input });
  const after = snapshot.data.conditions;
  const changed = !savedConditionsEqual(before, after);

  if (changed) {
    notifySavedConditionsChanged();
  }

  return {
    conditions: after,
    changed,
  };
}

/** Remove only `conditions`; favorites and other payload fields stay intact. */
export function clearSavedConditions(): ClearSavedConditionsResult {
  const before = readSavedConditions();
  const snapshot = updateUserLocalStorage({ conditions: null });
  const changed = before !== null;
  const favoritesAfter = snapshot.data.favorites;

  if (changed) {
    notifySavedConditionsChanged();
  }

  return {
    conditions: snapshot.data.conditions,
    favorites: favoritesAfter,
    changed,
  };
}
