import { USER_LOCAL_STORAGE_KEY } from '../types/userLocalStorage.js';
import {
  readUserLocalStorage,
  updateUserLocalStorage,
} from './userLocalStorage.js';

const favoriteListeners = new Set<() => void>();
const EMPTY_FAVORITES_SNAPSHOT: readonly number[] = [];

let cachedFavoritePolicyIdsSnapshot: readonly number[] = EMPTY_FAVORITES_SNAPSHOT;

function favoriteIdsEqual(
  left: readonly number[],
  right: readonly number[],
): boolean {
  if (left.length !== right.length) {
    return false;
  }

  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) {
      return false;
    }
  }

  return true;
}

/** Keep a stable snapshot reference for useSyncExternalStore subscribers. */
function syncFavoritePolicyIdsSnapshotFromStorage(): void {
  try {
    const next = readFavoritePolicyIds();
    if (favoriteIdsEqual(cachedFavoritePolicyIdsSnapshot, next)) {
      return;
    }

    cachedFavoritePolicyIdsSnapshot = next;
  } catch {
    cachedFavoritePolicyIdsSnapshot = EMPTY_FAVORITES_SNAPSHOT;
  }
}

if (typeof window !== 'undefined') {
  try {
    syncFavoritePolicyIdsSnapshotFromStorage();
  } catch {
    cachedFavoritePolicyIdsSnapshot = EMPTY_FAVORITES_SNAPSHOT;
  }
}

export interface ToggleFavoritePolicyResult {
  favorites: readonly number[];
  isFavorite: boolean;
  changed: boolean;
}

export function readFavoritePolicyIds(): readonly number[] {
  return readUserLocalStorage().data.favorites;
}

export function isFavoritePolicyId(policyId: number): boolean {
  if (!Number.isInteger(policyId) || policyId <= 0) {
    return false;
  }

  return readFavoritePolicyIds().includes(policyId);
}

export function notifyFavoritePolicyIdsChanged(): void {
  syncFavoritePolicyIdsSnapshotFromStorage();

  for (const listener of favoriteListeners) {
    listener();
  }
}

export function subscribeFavoritePolicyIds(onStoreChange: () => void): () => void {
  syncFavoritePolicyIdsSnapshotFromStorage();
  favoriteListeners.add(onStoreChange);

  if (typeof window !== 'undefined') {
    const onStorage = (event: StorageEvent) => {
      if (event.key === null || event.key === USER_LOCAL_STORAGE_KEY) {
        syncFavoritePolicyIdsSnapshotFromStorage();
        onStoreChange();
      }
    };
    window.addEventListener('storage', onStorage);

    return () => {
      favoriteListeners.delete(onStoreChange);
      window.removeEventListener('storage', onStorage);
    };
  }

  return () => {
    favoriteListeners.delete(onStoreChange);
  };
}

export function getFavoritePolicyIdsSnapshot(): readonly number[] {
  return cachedFavoritePolicyIdsSnapshot;
}

export function getFavoritePolicyIdsServerSnapshot(): readonly number[] {
  return EMPTY_FAVORITES_SNAPSHOT;
}

export function toggleFavoritePolicyId(
  policyId: number,
): ToggleFavoritePolicyResult {
  if (!Number.isInteger(policyId) || policyId <= 0) {
    const favorites = readFavoritePolicyIds();
    return { favorites, isFavorite: false, changed: false };
  }

  const current = [...readFavoritePolicyIds()];
  const existingIndex = current.indexOf(policyId);

  if (existingIndex >= 0) {
    current.splice(existingIndex, 1);
    const snapshot = updateUserLocalStorage({ favorites: current });
    notifyFavoritePolicyIdsChanged();
    return {
      favorites: snapshot.data.favorites,
      isFavorite: false,
      changed: true,
    };
  }

  const snapshot = updateUserLocalStorage({
    favorites: [...current, policyId],
  });
  const added = snapshot.data.favorites.includes(policyId);

  if (added) {
    notifyFavoritePolicyIdsChanged();
  }

  return {
    favorites: snapshot.data.favorites,
    isFavorite: added,
    changed: added,
  };
}
