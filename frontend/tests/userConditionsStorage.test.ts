import assert from 'node:assert/strict';
import test from 'node:test';
import { DEFAULT_BOOKMARK_FOLDER_ID, USER_LOCAL_STORAGE_KEY } from '../src/types/userLocalStorage.js';
import {
  clearSavedConditions,
  getSavedConditionsSnapshot,
  readSavedConditions,
  saveSavedConditions,
  subscribeSavedConditions,
} from '../src/utils/userConditionsStorage.js';
import { writeUserLocalStorage } from '../src/utils/userLocalStorage.js';
import { toggleFavoritePolicyId } from '../src/utils/userFavoritesStorage.js';
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

test('readSavedConditions는 storage conditions를 반환한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeUserLocalStorage(
      {
        schema_version: 2,
        bookmark_folders: [{ id: DEFAULT_BOOKMARK_FOLDER_ID, name: '기본 폴더' }],
        bookmarks: [{ policy_id: 1, folder_id: DEFAULT_BOOKMARK_FOLDER_ID }],
        conditions: {
          region: '서울특별시',
          age: 24,
          category: 'housing',
        },
        updated_at: '2026-08-11T10:00:00.000Z',
      },
      storage,
    );

    const unsubscribe = subscribeSavedConditions(() => undefined);
    assert.deepEqual(readSavedConditions(), {
      region: '서울특별시',
      age: 24,
      category: 'housing',
    });
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('saveSavedConditions는 region·age·category를 저장한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const unsubscribe = subscribeSavedConditions(() => undefined);
    const result = saveSavedConditions({
      region: '  천안시 ',
      age: 24,
      category: 'employment',
    });

    assert.equal(result.changed, true);
    assert.deepEqual(result.conditions, {
      region: '천안시',
      age: 24,
      category: 'employment',
    });

    const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
    assert.ok(raw?.includes('"region":"천안시"'));
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('saveSavedConditions는 모든 필드가 비면 conditions null을 저장한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const unsubscribe = subscribeSavedConditions(() => undefined);
    const result = saveSavedConditions({
      region: null,
      age: null,
      category: null,
    });

    assert.equal(result.changed, false);
    assert.equal(result.conditions, null);
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('clearSavedConditions는 conditions만 null로 만들고 favorites는 유지한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const unsubscribe = subscribeSavedConditions(() => undefined);
    toggleFavoritePolicyId(7);
    saveSavedConditions({
      region: '부산광역시',
      age: 29,
      category: 'finance',
    });

    const cleared = clearSavedConditions();

    assert.equal(cleared.changed, true);
    assert.equal(cleared.conditions, null);
    assert.deepEqual(cleared.favorites, [7]);
    assert.equal(readSavedConditions(), null);

    const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
    assert.ok(raw?.includes('"policy_id":7'));
    assert.ok(raw?.includes('"conditions":null'));
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('getSavedConditionsSnapshot은 연속 호출에서 동일 참조를 유지한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeUserLocalStorage(
      {
        schema_version: 2,
        bookmark_folders: [{ id: DEFAULT_BOOKMARK_FOLDER_ID, name: '기본 폴더' }],
        bookmarks: [],
        conditions: {
          region: '대전광역시',
          age: 22,
          category: 'education',
        },
        updated_at: '2026-08-11T10:00:00.000Z',
      },
      storage,
    );

    const unsubscribe = subscribeSavedConditions(() => undefined);
    const first = getSavedConditionsSnapshot();
    const second = getSavedConditionsSnapshot();

    assert.equal(first, second);
    assert.deepEqual(first, {
      region: '대전광역시',
      age: 22,
      category: 'education',
    });
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('saveSavedConditions는 snapshot 참조를 내용 변경 시에만 갱신한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const unsubscribe = subscribeSavedConditions(() => undefined);
    const before = getSavedConditionsSnapshot();

    saveSavedConditions({
      region: '광주광역시',
      age: 27,
      category: 'welfare',
    });

    const after = getSavedConditionsSnapshot();
    assert.notEqual(before, after);
    assert.equal(after, getSavedConditionsSnapshot());
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});
