import assert from 'node:assert/strict';
import test from 'node:test';
import { USER_LOCAL_STORAGE_KEY } from '../src/types/userLocalStorage.js';
import {
  getFavoritePolicyIdsSnapshot,
  isFavoritePolicyId,
  readFavoritePolicyIds,
  subscribeFavoritePolicyIds,
  toggleFavoritePolicyId,
} from '../src/utils/userFavoritesStorage.js';
import { writeUserLocalStorage } from '../src/utils/userLocalStorage.js';
import { MemoryStorage } from './helpers/memoryStorage.js';

class PatchedWindowStorage {
  install(storage: Storage): void {
    Object.defineProperty(globalThis, 'window', {
      configurable: true,
      value: {
        localStorage: storage,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      },
    });
  }

  restore(): void {
    Reflect.deleteProperty(globalThis, 'window');
  }
}

test('readFavoritePolicyIds는 storage favorites 배열을 반환한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeUserLocalStorage(
      {
        schema_version: 1,
        favorites: [2, 4],
        conditions: null,
        updated_at: '2026-08-11T10:00:00.000Z',
      },
      storage,
    );

    assert.deepEqual(readFavoritePolicyIds(), [2, 4]);
    assert.equal(isFavoritePolicyId(2), true);
    assert.equal(isFavoritePolicyId(99), false);
  } finally {
    windowPatch.restore();
  }
});

test('toggleFavoritePolicyId는 id를 추가하고 제거한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const added = toggleFavoritePolicyId(5);
    assert.equal(added.changed, true);
    assert.equal(added.isFavorite, true);
    assert.deepEqual(added.favorites, [5]);

    const removed = toggleFavoritePolicyId(5);
    assert.equal(removed.changed, true);
    assert.equal(removed.isFavorite, false);
    assert.deepEqual(removed.favorites, []);

    const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
    assert.ok(raw?.includes('"favorites":[]'));
  } finally {
    windowPatch.restore();
  }
});

test('getFavoritePolicyIdsSnapshot은 연속 호출에서 동일 참조를 유지한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeUserLocalStorage(
      {
        schema_version: 1,
        favorites: [2, 4],
        conditions: null,
        updated_at: '2026-08-11T10:00:00.000Z',
      },
      storage,
    );

    const unsubscribe = subscribeFavoritePolicyIds(() => undefined);
    const first = getFavoritePolicyIdsSnapshot();
    const second = getFavoritePolicyIdsSnapshot();

    assert.equal(first, second);
    assert.deepEqual(first, [2, 4]);
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('toggleFavoritePolicyId는 snapshot 참조를 내용 변경 시에만 갱신한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const unsubscribe = subscribeFavoritePolicyIds(() => undefined);
    const before = getFavoritePolicyIdsSnapshot();

    toggleFavoritePolicyId(5);

    const after = getFavoritePolicyIdsSnapshot();
    assert.notDeepEqual(before, after);
    assert.equal(after, getFavoritePolicyIdsSnapshot());
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('toggleFavoritePolicyId는 invalid id를 무시한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const result = toggleFavoritePolicyId(-1);
    assert.equal(result.changed, false);
    assert.deepEqual(result.favorites, []);
  } finally {
    windowPatch.restore();
  }
});
