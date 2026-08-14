import assert from 'node:assert/strict';
import test from 'node:test';
import { MemoryStorage } from './helpers/memoryStorage.js';
import {
  USER_LOCAL_STORAGE_KEY,
  USER_LOCAL_STORAGE_SCHEMA_VERSION,
} from '../src/types/userLocalStorage.js';
import { readUserLocalStorage } from '../src/utils/userLocalStorage.js';
import {
  getFavoritePolicyIdsSnapshot,
  readFavoritePolicyIds,
} from '../src/utils/userFavoritesStorage.js';
import {
  getSavedConditionsSnapshot,
  readSavedConditions,
} from '../src/utils/userConditionsStorage.js';
import { resetAllUserLocalStorage } from '../src/utils/userDataReset.js';

test('resetAllUserLocalStorage는 key를 삭제하고 subscribers snapshot을 초기화한다', () => {
  const storage = new MemoryStorage();
  storage.setItem(
    USER_LOCAL_STORAGE_KEY,
    JSON.stringify({
      schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
      favorites: [1, 2],
      conditions: { region: '서울', age: 24, category: 'housing' },
      updated_at: '2026-08-11T00:00:00.000Z',
    }),
  );

  const cleared = resetAllUserLocalStorage(storage);
  assert.equal(cleared, true);
  assert.equal(storage.getItem(USER_LOCAL_STORAGE_KEY), null);

  const snapshot = readUserLocalStorage(storage);
  assert.deepEqual(snapshot.data.favorites, []);
  assert.equal(snapshot.data.conditions, null);
  assert.deepEqual(readFavoritePolicyIds(), []);
  assert.equal(readSavedConditions(), null);
  assert.deepEqual(getFavoritePolicyIdsSnapshot(), []);
  assert.equal(getSavedConditionsSnapshot(), null);
});
