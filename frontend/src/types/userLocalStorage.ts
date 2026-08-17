/**
 * Browser-only user payload for Frontend 05 (User Service Features).
 *
 * Key and schema version follow Integration 05 W4-G0 proposal until gate approval.
 * Do not persist personal data beyond region, age band, category, and policy ids.
 */

/** Proposal localStorage key (Integration 05 / FE5-00). */
export const USER_LOCAL_STORAGE_KEY = 'cheongnyeon-alimi.user-local.v1';

/** Current payload schema version. v1 payloads migrate to v2 on read. */
export const USER_LOCAL_STORAGE_SCHEMA_VERSION = 2;

/** Maximum stored bookmark policy ids (client-side guard). */
export const USER_LOCAL_STORAGE_MAX_FAVORITES = 200;

/** Maximum user-created bookmark folders (including the default folder). */
export const USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDERS = 30;

/** Maximum folder name length. */
export const USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDER_NAME = 50;

/** Built-in default folder id (cannot be removed). */
export const DEFAULT_BOOKMARK_FOLDER_ID = 'default';

/** Built-in default folder display name. */
export const DEFAULT_BOOKMARK_FOLDER_NAME = '기본 폴더';

export interface UserSavedConditions {
  region: string | null;
  age: number | null;
  category: string | null;
}

export interface BookmarkFolder {
  id: string;
  name: string;
}

export interface BookmarkEntry {
  policy_id: number;
  folder_id: string;
}

export interface UserLocalStoragePayload {
  schema_version: typeof USER_LOCAL_STORAGE_SCHEMA_VERSION;
  bookmark_folders: BookmarkFolder[];
  bookmarks: BookmarkEntry[];
  conditions: UserSavedConditions | null;
  updated_at: string;
}

/** Legacy v1 shape — migrated to v2 on read (not written anew). */
export interface UserLocalStoragePayloadV1 {
  schema_version: 1;
  favorites: number[];
  conditions: UserSavedConditions | null;
  updated_at: string;
}

export type UserLocalStorageRecoveryReason =
  | 'corrupt'
  | 'unsupported_version'
  | 'invalid_shape';

export type UserLocalStorageReadSource =
  | 'storage'
  | 'default'
  | 'recovered'
  | 'unavailable';

export interface UserLocalStorageSnapshot {
  data: UserLocalStoragePayload;
  source: UserLocalStorageReadSource;
  recoveryReason?: UserLocalStorageRecoveryReason;
}
