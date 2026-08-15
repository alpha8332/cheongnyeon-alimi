import {
  DEFAULT_BOOKMARK_FOLDER_ID,
  USER_LOCAL_STORAGE_KEY,
  USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDERS,
  USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDER_NAME,
  USER_LOCAL_STORAGE_MAX_FAVORITES,
  USER_LOCAL_STORAGE_SCHEMA_VERSION,
  type BookmarkEntry,
  type BookmarkFolder,
  type UserLocalStoragePayload,
  type UserLocalStorageRecoveryReason,
  type UserLocalStorageSnapshot,
  type UserSavedConditions,
} from '../types/userLocalStorage.js';
import {
  createDefaultBookmarkFolder,
  deriveFavoritePolicyIds,
  migrateUserLocalStorageV1ToV2,
  normalizeV1UserLocalStoragePayload,
} from './userLocalStorageMigration.js';
import { recordUserLocalStorageRecoveryNotice } from './userLocalStorageRecoveryNotice.js';

const MAX_CONDITION_TEXT_LENGTH = 200;
const MIN_AGE = 1;
const MAX_AGE = 120;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function normalizeOptionalString(
  value: unknown,
  maxLength: number,
): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return null;
  }

  return trimmed.slice(0, maxLength);
}

function normalizeOptionalAge(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value !== 'number' || !Number.isInteger(value)) {
    return null;
  }

  if (value < MIN_AGE || value > MAX_AGE) {
    return null;
  }

  return value;
}

function normalizeConditions(value: unknown): UserSavedConditions | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    return null;
  }

  const region = normalizeOptionalString(value.region, MAX_CONDITION_TEXT_LENGTH);
  const age = normalizeOptionalAge(value.age);
  const category = normalizeOptionalString(
    value.category,
    MAX_CONDITION_TEXT_LENGTH,
  );

  if (region === null && age === null && category === null) {
    return null;
  }

  return { region, age, category };
}

function normalizeUpdatedAt(value: unknown): string | null {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return null;
  }

  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return null;
  }

  return new Date(parsed).toISOString();
}

function normalizeBookmarkFolder(value: unknown): BookmarkFolder | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = normalizeOptionalString(value.id, 80);
  const name = normalizeOptionalString(
    value.name,
    USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDER_NAME,
  );

  if (id === null || name === null) {
    return null;
  }

  return { id, name };
}

function normalizeBookmarkFolders(value: unknown): BookmarkFolder[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const seenIds = new Set<string>();
  const folders: BookmarkFolder[] = [];

  for (const item of value) {
    const folder = normalizeBookmarkFolder(item);
    if (folder === null || seenIds.has(folder.id)) {
      continue;
    }

    seenIds.add(folder.id);
    folders.push(folder);

    if (folders.length >= USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDERS) {
      break;
    }
  }

  if (!folders.some((folder) => folder.id === DEFAULT_BOOKMARK_FOLDER_ID)) {
    folders.unshift(createDefaultBookmarkFolder());
  }

  return folders;
}

function normalizeBookmarks(
  value: unknown,
  folderIds: ReadonlySet<string>,
): BookmarkEntry[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const seenPolicyIds = new Set<number>();
  const bookmarks: BookmarkEntry[] = [];

  for (const item of value) {
    if (!isRecord(item)) {
      continue;
    }

    const policyId = item.policy_id;
    const folderId = normalizeOptionalString(item.folder_id, 80);

    if (
      typeof policyId !== 'number' ||
      !Number.isInteger(policyId) ||
      policyId <= 0 ||
      folderId === null
    ) {
      continue;
    }

    if (seenPolicyIds.has(policyId)) {
      continue;
    }

    seenPolicyIds.add(policyId);
    bookmarks.push({
      policy_id: policyId,
      folder_id: folderIds.has(folderId)
        ? folderId
        : DEFAULT_BOOKMARK_FOLDER_ID,
    });

    if (bookmarks.length >= USER_LOCAL_STORAGE_MAX_FAVORITES) {
      break;
    }
  }

  return bookmarks;
}

/** Empty payload used when storage is missing, corrupt, or unavailable. */
export function createDefaultUserLocalStoragePayload(
  updatedAt: string = new Date().toISOString(),
): UserLocalStoragePayload {
  return {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    bookmark_folders: [createDefaultBookmarkFolder()],
    bookmarks: [],
    conditions: null,
    updated_at: updatedAt,
  };
}

/**
 * Validate and normalize unknown JSON value into a payload.
 * Returns null when the root shape or schema_version is not supported.
 */
export function normalizeUserLocalStoragePayload(
  value: unknown,
): UserLocalStoragePayload | null {
  if (!isRecord(value)) {
    return null;
  }

  if (value.schema_version !== USER_LOCAL_STORAGE_SCHEMA_VERSION) {
    return null;
  }

  const bookmarkFolders = normalizeBookmarkFolders(value.bookmark_folders);
  if (bookmarkFolders === null) {
    return null;
  }

  const folderIds = new Set(bookmarkFolders.map((folder) => folder.id));
  const bookmarks = normalizeBookmarks(value.bookmarks, folderIds);
  if (bookmarks === null) {
    return null;
  }

  let conditions: UserSavedConditions | null = null;
  if (value.conditions !== null && value.conditions !== undefined) {
    if (!isRecord(value.conditions)) {
      return null;
    }
    conditions = normalizeConditions(value.conditions);
  }

  const updatedAt = normalizeUpdatedAt(value.updated_at);
  if (updatedAt === null) {
    return null;
  }

  return {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    bookmark_folders: bookmarkFolders,
    bookmarks,
    conditions,
    updated_at: updatedAt,
  };
}

export function serializeUserLocalStoragePayload(
  payload: UserLocalStoragePayload,
): string {
  return JSON.stringify(payload);
}

/** Resolve browser localStorage when running in a document context. */
export function getBrowserLocalStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function persistDefaultPayload(storage: Storage): UserLocalStoragePayload {
  const payload = createDefaultUserLocalStoragePayload();
  try {
    storage.setItem(
      USER_LOCAL_STORAGE_KEY,
      serializeUserLocalStoragePayload(payload),
    );
  } catch {
    // Quota or privacy mode — caller still receives in-memory default.
  }
  return payload;
}

function readRawFromStorage(storage: Storage): string | null {
  try {
    return storage.getItem(USER_LOCAL_STORAGE_KEY);
  } catch {
    return null;
  }
}

function recoverStoragePayload(
  storage: Storage,
  reason: UserLocalStorageRecoveryReason,
): UserLocalStorageSnapshot {
  const data = persistDefaultPayload(storage);
  try {
    recordUserLocalStorageRecoveryNotice(reason);
  } catch {
    // Recovery notice is best-effort UX; never block payload reset.
  }
  return {
    data,
    source: 'recovered',
    recoveryReason: reason,
  };
}

function tryMigrateV1Payload(
  parsed: Record<string, unknown>,
  storage: Storage,
): UserLocalStorageSnapshot | null {
  if (parsed.schema_version !== 1) {
    return null;
  }

  const v1 = normalizeV1UserLocalStoragePayload(
    parsed,
    normalizeConditions,
    normalizeUpdatedAt,
  );
  if (v1 === null) {
    return recoverStoragePayload(storage, 'invalid_shape');
  }

  const migrated = migrateUserLocalStorageV1ToV2(v1);
  writeUserLocalStorage(migrated, storage);
  return {
    data: migrated,
    source: 'storage',
  };
}

/**
 * Read user payload from storage without throwing.
 * Corrupt or unsupported payloads are reset to the default empty contract.
 * Legacy v1 payloads migrate to v2 in place.
 */
export function readUserLocalStorage(
  storage: Storage | null = getBrowserLocalStorage(),
): UserLocalStorageSnapshot {
  if (storage === null) {
    return {
      data: createDefaultUserLocalStoragePayload(),
      source: 'unavailable',
    };
  }

  const raw = readRawFromStorage(storage);
  if (raw === null) {
    return {
      data: createDefaultUserLocalStoragePayload(),
      source: 'default',
    };
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw) as unknown;
  } catch {
    return recoverStoragePayload(storage, 'corrupt');
  }

  if (!isRecord(parsed)) {
    return recoverStoragePayload(storage, 'invalid_shape');
  }

  const migrated = tryMigrateV1Payload(parsed, storage);
  if (migrated !== null) {
    return migrated;
  }

  if (
    parsed.schema_version !== undefined &&
    parsed.schema_version !== USER_LOCAL_STORAGE_SCHEMA_VERSION
  ) {
    return recoverStoragePayload(storage, 'unsupported_version');
  }

  const normalized = normalizeUserLocalStoragePayload(parsed);
  if (normalized === null) {
    return recoverStoragePayload(storage, 'invalid_shape');
  }

  return {
    data: normalized,
    source: 'storage',
  };
}

/** Persist payload; returns false when storage is unavailable or write fails. */
export function writeUserLocalStorage(
  payload: UserLocalStoragePayload,
  storage: Storage | null = getBrowserLocalStorage(),
): boolean {
  if (storage === null) {
    return false;
  }

  const normalized = normalizeUserLocalStoragePayload(payload);
  if (normalized === null) {
    return false;
  }

  try {
    storage.setItem(
      USER_LOCAL_STORAGE_KEY,
      serializeUserLocalStoragePayload(normalized),
    );
    return true;
  } catch {
    return false;
  }
}

/** Remove stored payload. Used by FE5-08; safe to call when storage is unavailable. */
export function clearUserLocalStorage(
  storage: Storage | null = getBrowserLocalStorage(),
): boolean {
  if (storage === null) {
    return false;
  }

  try {
    storage.removeItem(USER_LOCAL_STORAGE_KEY);
    return true;
  } catch {
    return false;
  }
}

/** Merge partial updates, refresh updated_at, and persist when possible. */
export function updateUserLocalStorage(
  patch: Partial<
    Pick<UserLocalStoragePayload, 'bookmark_folders' | 'bookmarks' | 'conditions'>
  >,
  storage: Storage | null = getBrowserLocalStorage(),
): UserLocalStorageSnapshot {
  const current = readUserLocalStorage(storage);
  const merged: UserLocalStoragePayload = {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    bookmark_folders:
      patch.bookmark_folders !== undefined
        ? patch.bookmark_folders
        : current.data.bookmark_folders,
    bookmarks:
      patch.bookmarks !== undefined ? patch.bookmarks : current.data.bookmarks,
    conditions:
      patch.conditions !== undefined
        ? patch.conditions
        : current.data.conditions,
    updated_at: new Date().toISOString(),
  };

  const normalized = normalizeUserLocalStoragePayload(merged);
  if (normalized === null) {
    return readUserLocalStorage(storage);
  }

  if (storage !== null) {
    writeUserLocalStorage(normalized, storage);
  }

  return {
    data: normalized,
    source: storage === null ? 'unavailable' : 'storage',
  };
}

export { deriveFavoritePolicyIds };
