import {
  DEFAULT_BOOKMARK_FOLDER_ID,
  DEFAULT_BOOKMARK_FOLDER_NAME,
  type BookmarkEntry,
  type BookmarkFolder,
  type UserLocalStoragePayload,
  type UserLocalStoragePayloadV1,
  type UserSavedConditions,
  USER_LOCAL_STORAGE_MAX_FAVORITES,
} from '../types/userLocalStorage.js';

function normalizeFavoriteIdsFromV1(value: unknown): number[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const seen = new Set<number>();
  const favorites: number[] = [];

  for (const item of value) {
    if (typeof item !== 'number' || !Number.isInteger(item) || item <= 0) {
      continue;
    }

    if (seen.has(item)) {
      continue;
    }

    seen.add(item);
    favorites.push(item);

    if (favorites.length >= USER_LOCAL_STORAGE_MAX_FAVORITES) {
      break;
    }
  }

  return favorites;
}

export function createDefaultBookmarkFolder(): BookmarkFolder {
  return {
    id: DEFAULT_BOOKMARK_FOLDER_ID,
    name: DEFAULT_BOOKMARK_FOLDER_NAME,
  };
}

/** Migrate legacy v1 flat favorites into v2 folder bookmarks. */
export function migrateUserLocalStorageV1ToV2(
  payload: UserLocalStoragePayloadV1,
): UserLocalStoragePayload {
  const defaultFolder = createDefaultBookmarkFolder();
  const favoriteIds = normalizeFavoriteIdsFromV1(payload.favorites);
  const bookmarks: BookmarkEntry[] = favoriteIds.map((policyId) => ({
    policy_id: policyId,
    folder_id: DEFAULT_BOOKMARK_FOLDER_ID,
  }));

  return {
    schema_version: 2,
    bookmark_folders: [defaultFolder],
    bookmarks,
    conditions: payload.conditions,
    updated_at: new Date().toISOString(),
  };
}

export function deriveFavoritePolicyIds(
  bookmarks: readonly BookmarkEntry[],
): number[] {
  const seen = new Set<number>();
  const favorites: number[] = [];

  for (const entry of bookmarks) {
    if (
      typeof entry.policy_id !== 'number' ||
      !Number.isInteger(entry.policy_id) ||
      entry.policy_id <= 0
    ) {
      continue;
    }

    if (seen.has(entry.policy_id)) {
      continue;
    }

    seen.add(entry.policy_id);
    favorites.push(entry.policy_id);

    if (favorites.length >= USER_LOCAL_STORAGE_MAX_FAVORITES) {
      break;
    }
  }

  return favorites;
}

export function normalizeV1UserLocalStoragePayload(
  value: unknown,
  normalizeConditions: (value: unknown) => UserSavedConditions | null,
  normalizeUpdatedAt: (value: unknown) => string | null,
): UserLocalStoragePayloadV1 | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return null;
  }

  const record = value as Record<string, unknown>;
  if (record.schema_version !== 1) {
    return null;
  }

  const favorites = normalizeFavoriteIdsFromV1(record.favorites);
  let conditions: UserSavedConditions | null = null;

  if (record.conditions !== null && record.conditions !== undefined) {
    if (typeof record.conditions !== 'object' || Array.isArray(record.conditions)) {
      return null;
    }

    conditions = normalizeConditions(record.conditions);
  }

  const updatedAt = normalizeUpdatedAt(record.updated_at);
  if (updatedAt === null) {
    return null;
  }

  return {
    schema_version: 1,
    favorites,
    conditions,
    updated_at: updatedAt,
  };
}
