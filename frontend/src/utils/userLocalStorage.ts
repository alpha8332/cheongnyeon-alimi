import {
  USER_LOCAL_STORAGE_KEY,
  USER_LOCAL_STORAGE_MAX_FAVORITES,
  USER_LOCAL_STORAGE_SCHEMA_VERSION,
  type UserLocalStoragePayload,
  type UserLocalStorageRecoveryReason,
  type UserLocalStorageSnapshot,
  type UserSavedConditions,
} from '../types/userLocalStorage.js';

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

function normalizeFavoriteIds(value: unknown): number[] | null {
  if (!Array.isArray(value)) {
    return null;
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

/** Empty payload used when storage is missing, corrupt, or unavailable. */
export function createDefaultUserLocalStoragePayload(
  updatedAt: string = new Date().toISOString(),
): UserLocalStoragePayload {
  return {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    favorites: [],
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

  const favorites = normalizeFavoriteIds(value.favorites);
  if (favorites === null) {
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
    favorites,
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
  return {
    data,
    source: 'recovered',
    recoveryReason: reason,
  };
}

/**
 * Read user payload from storage without throwing.
 * Corrupt or unsupported payloads are reset to the default empty contract.
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
  patch: Partial<Pick<UserLocalStoragePayload, 'favorites' | 'conditions'>>,
  storage: Storage | null = getBrowserLocalStorage(),
): UserLocalStorageSnapshot {
  const current = readUserLocalStorage(storage);
  const merged: UserLocalStoragePayload = {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    favorites:
      patch.favorites !== undefined ? patch.favorites : current.data.favorites,
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
