import assert from 'node:assert/strict';
import test from 'node:test';
import {
  DEFAULT_BOOKMARK_FOLDER_ID,
  USER_LOCAL_STORAGE_KEY,
  USER_LOCAL_STORAGE_SCHEMA_VERSION,
  type UserLocalStoragePayload,
} from '../src/types/userLocalStorage.js';
import {
  clearUserLocalStorage,
  createDefaultUserLocalStoragePayload,
  deriveFavoritePolicyIds,
  normalizeUserLocalStoragePayload,
  readUserLocalStorage,
  updateUserLocalStorage,
  writeUserLocalStorage,
} from '../src/utils/userLocalStorage.js';
import { migrateUserLocalStorageV1ToV2 } from '../src/utils/userLocalStorageMigration.js';

import { MemoryStorage } from './helpers/memoryStorage.js';

function samplePayload(
  overrides: Partial<UserLocalStoragePayload> = {},
): UserLocalStoragePayload {
  return {
    schema_version: USER_LOCAL_STORAGE_SCHEMA_VERSION,
    bookmark_folders: [{ id: DEFAULT_BOOKMARK_FOLDER_ID, name: '기본 폴더' }],
    bookmarks: [
      { policy_id: 1, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
      { policy_id: 2, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
    ],
    conditions: {
      region: '천안시',
      age: 27,
      category: 'housing',
    },
    updated_at: '2026-08-11T10:00:00.000Z',
    ...overrides,
  };
}

test('createDefaultUserLocalStoragePayload는 빈 bookmarks와 기본 폴더를 반환한다', () => {
  const payload = createDefaultUserLocalStoragePayload(
    '2026-08-11T12:00:00.000Z',
  );

  assert.deepEqual(payload.bookmarks, []);
  assert.equal(payload.bookmark_folders[0]?.id, DEFAULT_BOOKMARK_FOLDER_ID);
  assert.equal(payload.conditions, null);
  assert.equal(payload.schema_version, USER_LOCAL_STORAGE_SCHEMA_VERSION);
  assert.equal(payload.updated_at, '2026-08-11T12:00:00.000Z');
});

test('normalizeUserLocalStoragePayload는 유효 payload를 정규화한다', () => {
  const normalized = normalizeUserLocalStoragePayload(
    samplePayload({
      bookmarks: [
        { policy_id: 3, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
        { policy_id: 3, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
        { policy_id: 4.5, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
        { policy_id: -1, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
        { policy_id: 5, folder_id: 'missing-folder' },
      ],
      conditions: {
        region: '  서울 ',
        age: 24,
        category: '',
      },
    }),
  );

  assert.ok(normalized);
  assert.deepEqual(normalized?.bookmarks, [
    { policy_id: 3, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
    { policy_id: 5, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
  ]);
  assert.deepEqual(normalized?.conditions, {
    region: '서울',
    age: 24,
    category: null,
    categories: [],
  });
});

test('normalizeUserLocalStoragePayload는 기존 단일 category를 categories로 호환한다', () => {
  const normalized = normalizeUserLocalStoragePayload(samplePayload());

  assert.deepEqual(normalized?.conditions, {
    region: '천안시',
    age: 27,
    category: 'housing',
    categories: ['housing'],
  });
});

test('normalizeUserLocalStoragePayload는 다중 categories의 순서와 대표 category를 유지한다', () => {
  const normalized = normalizeUserLocalStoragePayload(
    samplePayload({
      conditions: {
        region: '경기도',
        age: 30,
        category: 'housing',
        categories: ['finance', 'housing', 'finance'],
      },
    }),
  );

  assert.deepEqual(normalized?.conditions, {
    region: '경기도',
    age: 30,
    category: 'finance',
    categories: ['finance', 'housing'],
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
  assert.deepEqual(snapshot.data.bookmarks, []);
  assert.equal(snapshot.data.conditions, null);
});

test('readUserLocalStorage는 missing storage entry를 default로 처리한다', () => {
  const storage = new MemoryStorage();
  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'default');
  assert.deepEqual(snapshot.data.bookmarks, []);
});

test('readUserLocalStorage는 corrupt JSON을 reset하고 recovered를 표시한다', () => {
  const storage = new MemoryStorage();
  storage.setItem(USER_LOCAL_STORAGE_KEY, '{not-json');

  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'recovered');
  assert.equal(snapshot.recoveryReason, 'corrupt');
  assert.deepEqual(snapshot.data.bookmarks, []);

  const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
  assert.ok(raw);
  const reparsed = JSON.parse(raw) as UserLocalStoragePayload;
  assert.equal(reparsed.schema_version, USER_LOCAL_STORAGE_SCHEMA_VERSION);
});

test('readUserLocalStorage는 unsupported version을 reset한다', () => {
  const storage = new MemoryStorage();
  storage.setItem(
    USER_LOCAL_STORAGE_KEY,
    JSON.stringify({
      schema_version: 99,
      bookmark_folders: [{ id: DEFAULT_BOOKMARK_FOLDER_ID, name: '기본 폴더' }],
      bookmarks: [],
      conditions: null,
      updated_at: '2026-08-11T10:00:00.000Z',
    }),
  );

  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'recovered');
  assert.equal(snapshot.recoveryReason, 'unsupported_version');
  assert.deepEqual(snapshot.data.bookmarks, []);
});

test('readUserLocalStorage는 legacy v1 payload를 v2로 migrate한다', () => {
  const storage = new MemoryStorage();
  storage.setItem(
    USER_LOCAL_STORAGE_KEY,
    JSON.stringify({
      schema_version: 1,
      favorites: [4, 8],
      conditions: null,
      updated_at: '2026-08-11T10:00:00.000Z',
    }),
  );

  const snapshot = readUserLocalStorage(storage);

  assert.equal(snapshot.source, 'storage');
  assert.deepEqual(deriveFavoritePolicyIds(snapshot.data.bookmarks), [4, 8]);
  assert.equal(snapshot.data.bookmark_folders[0]?.id, DEFAULT_BOOKMARK_FOLDER_ID);

  const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
  assert.ok(raw?.includes('"schema_version":2'));
});

test('migrateUserLocalStorageV1ToV2는 flat favorites를 default folder bookmarks로 변환한다', () => {
  const migrated = migrateUserLocalStorageV1ToV2({
    schema_version: 1,
    favorites: [10, 11],
    conditions: null,
    updated_at: '2026-08-11T10:00:00.000Z',
  });

  assert.equal(migrated.schema_version, 2);
  assert.deepEqual(migrated.bookmarks, [
    { policy_id: 10, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
    { policy_id: 11, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
  ]);
});

test('writeUserLocalStorage와 readUserLocalStorage round-trip', () => {
  const storage = new MemoryStorage();
  const payload = samplePayload();

  assert.equal(writeUserLocalStorage(payload, storage), true);

  const snapshot = readUserLocalStorage(storage);
  assert.equal(snapshot.source, 'storage');
  assert.deepEqual(snapshot.data.bookmarks, payload.bookmarks);
  assert.deepEqual(snapshot.data.conditions, {
    ...payload.conditions,
    categories: ['housing'],
  });
});

test('updateUserLocalStorage는 bookmarks만 갱신하고 conditions를 유지한다', () => {
  const storage = new MemoryStorage();
  writeUserLocalStorage(samplePayload(), storage);

  const snapshot = updateUserLocalStorage(
    {
      bookmarks: [
        { policy_id: 9, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
        { policy_id: 10, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
      ],
    },
    storage,
  );

  assert.deepEqual(snapshot.data.bookmarks, [
    { policy_id: 9, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
    { policy_id: 10, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
  ]);
  assert.deepEqual(snapshot.data.conditions, {
    ...samplePayload().conditions,
    categories: ['housing'],
  });
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
