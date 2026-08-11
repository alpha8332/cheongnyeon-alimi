import assert from 'node:assert/strict';
import test from 'node:test';
import {
  USER_LOCAL_STORAGE_KEY,
  USER_LOCAL_STORAGE_SCHEMA_VERSION,
  type UserLocalStoragePayload,
} from '../src/types/userLocalStorage.js';
import {
  clearUserLocalStorage,
  createDefaultUserLocalStoragePayload,
  normalizeUserLocalStoragePayload,
  readUserLocalStorage,
  serializeUserLocalStoragePayload,
  updateUserLocalStorage,
  writeUserLocalStorage,
} from '../src/utils/userLocalStorage.js';

class MemoryStorage implements Storage {
  private readonly map = new Map<string, string>();

  get length(): number {
    return this.map.size;
  }

  clear(): void {
    this.map.clear();
  }

  getItem(key: string): string | null {
    return this.map.get(key) ?? null;
  }

  key(index: number): string | null {
    return [...this.map.keys()][index] ?? null;
  }

  removeItem(key: string): void {
    this.map.delete(key);
  }

  setItem(key: string, value: string): void {
    this.map.set(key, value);
  }
}

function samplePayload(
  overrides: Partial<UserLocalStoragePayload> = {},
): UserLocalStoragePayload {
  return {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    favorites: [1, 2],
    conditions: {
      region: '천안시',
      age: 27,
      category: 'housing',
    },
    updated_at: '2026-08-11T10:00:00.000Z',
    ...overrides,
  };
}

test('createDefaultUserLocalStoragePayload는 빈 favorites와 null conditions를 반환한다', () => {
  const payload = createDefaultUserLocalStoragePayload(
    '2026-08-11T12:00:00.000Z',
  );

  assert.deepEqual(payload.favorites, []);
  assert.equal(payload.conditions, null);
  assert.equal(payload.schema_version, USER_LOCAL_STORAGE_SCHEMA_VERSION);
  assert.equal(payload.updated_at, '2026-08-11T12:00:00.000Z');
});

test('normalizeUserLocalStoragePayload는 유효 payload를 정규화한다', () => {
  const normalized = normalizeUserLocalStoragePayload(
    samplePayload({
      favorites: [3, 3, 4.5, -1, 0],
      conditions: {
        region: '  서울 ',
        age: 24,
        category: '',
      },
    }),
  );

  assert.ok(normalized);
  assert.deepEqual(normalized?.favorites, [3]);
  assert.deepEqual(normalized?.conditions, {
    region: '서울',
    age: 24,
    category: null,
  });
});

test('normalizeUserLocalStoragePayload는 unsupported schema_version을 거부한다', () => {
  assert.equal(
    normalizeUserLocalStoragePayload(
      samplePayload({ schema_version: 99 as typeof USER_LOCAL_STORAGE_SCHEMA_VERSION }),
    ),
    null,
  );
});

test('normalizeUserLocalStoragePayload는 conditions가 모두 비어 있으면 null로 만든다', () => {
  const normalized = normalizeUserLocalStoragePayload(
    samplePayload({
      conditions: {
        region: null,
        age: null,
        category: null,
      },
    }),
  );

  assert.ok(normalized);
  assert.equal(normalized?.conditions, null);
});

test('readUserLocalStorage는 storage가 없으면 unavailable default를 반환한다', () => {
  const snapshot = readUserLocalStorage(null);

  assert.equal(snapshot.source, 'unavailable');
  assert.deepEqual(snapshot.data.favorites, []);
  assert.equal(snapshot.data.conditions, null);
});

test('readUserLocalStorage는 missing storage entry를 default로 처리한다', () => {
  const storage = new MemoryStorage();
  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'default');
  assert.deepEqual(snapshot.data.favorites, []);
});

test('readUserLocalStorage는 corrupt JSON을 reset하고 recovered를 표시한다', () => {
  const storage = new MemoryStorage();
  storage.setItem(USER_LOCAL_STORAGE_KEY, '{not-json');

  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'recovered');
  assert.equal(snapshot.recoveryReason, 'corrupt');
  assert.deepEqual(snapshot.data.favorites, []);

  const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
  assert.ok(raw);
  const reparsed = JSON.parse(raw) as UserLocalStoragePayload;
  assert.equal(reparsed.schema_version, USER_LOCAL_STORAGE_SCHEMA_VERSION);
});

test('readUserLocalStorage는 unsupported version을 reset한다', () => {
  const storage = new MemoryStorage();
  storage.setItem(
    USER_LOCAL_STORAGE_KEY,
    serializeUserLocalStoragePayload(
      samplePayload({
        schema_version: 2 as typeof USER_LOCAL_STORAGE_SCHEMA_VERSION,
      }),
    ),
  );

  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'recovered');
  assert.equal(snapshot.recoveryReason, 'unsupported_version');
  assert.deepEqual(snapshot.data.favorites, []);
});

test('writeUserLocalStorage와 readUserLocalStorage round-trip', () => {
  const storage = new MemoryStorage();
  const payload = samplePayload();

  assert.equal(writeUserLocalStorage(payload, storage), true);

  const snapshot = readUserLocalStorage(storage);
  assert.equal(snapshot.source, 'storage');
  assert.deepEqual(snapshot.data.favorites, payload.favorites);
  assert.deepEqual(snapshot.data.conditions, payload.conditions);
});

test('updateUserLocalStorage는 favorites만 갱신하고 conditions를 유지한다', () => {
  const storage = new MemoryStorage();
  writeUserLocalStorage(samplePayload(), storage);

  const snapshot = updateUserLocalStorage({ favorites: [9, 10] }, storage);

  assert.deepEqual(snapshot.data.favorites, [9, 10]);
  assert.deepEqual(snapshot.data.conditions, samplePayload().conditions);
});

test('clearUserLocalStorage는 key를 제거한다', () => {
  const storage = new MemoryStorage();
  writeUserLocalStorage(samplePayload(), storage);

  assert.equal(clearUserLocalStorage(storage), true);
  assert.equal(storage.getItem(USER_LOCAL_STORAGE_KEY), null);
});

test('readUserLocalStorage(null) 이후 write 실패해도 호출자는 default payload를 받는다', () => {
  assert.equal(writeUserLocalStorage(samplePayload(), null), false);
  const snapshot = readUserLocalStorage(null);
  assert.equal(snapshot.source, 'unavailable');
});
