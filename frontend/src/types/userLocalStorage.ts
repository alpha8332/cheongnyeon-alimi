/**
 * Browser-only user payload for Frontend 05 (User Service Features).
 *
 * Key and schema version follow Integration 05 W4-G0 proposal until gate approval.
 * Do not persist personal data beyond region, age band, category, and policy ids.
 */

/** Proposal localStorage key (Integration 05 / FE5-00). */
export const USER_LOCAL_STORAGE_KEY = 'cheongnyeon-alimi.user-local.v1';

/** Current payload schema version. Unsupported versions trigger reset (no migration yet). */
export const USER_LOCAL_STORAGE_SCHEMA_VERSION = 1;

/** Maximum stored favorite policy ids (client-side guard). */
export const USER_LOCAL_STORAGE_MAX_FAVORITES = 200;

export interface UserSavedConditions {
  region: string | null;
  age: number | null;
  category: string | null;
}

export interface UserLocalStoragePayload {
  schema_version: typeof USER_LOCAL_STORAGE_SCHEMA_VERSION;
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
