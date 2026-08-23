import assert from 'node:assert/strict';
import test from 'node:test';
import {
  DEFAULT_BOOKMARK_FOLDER_ID,
  USER_LOCAL_STORAGE_KEY,
} from '../src/types/userLocalStorage.js';
import {
  createBookmarkFolder,
  deleteBookmarkFolder,
  getBookmarkFolderForPolicy,
  getFavoritePolicyIdsSnapshot,
  getPolicyIdsForFolder,
  isFavoritePolicyId,
  isDeletableBookmarkFolder,
  readFavoritePolicyIds,
  removeBookmarkPolicy,
  setBookmarkPolicy,
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

function writeDefaultPayload(storage: Storage) {
  writeUserLocalStorage(
    {
      schema_version: 2,
      bookmark_folders: [{ id: DEFAULT_BOOKMARK_FOLDER_ID, name: '기본 폴더' }],
      bookmarks: [
        { policy_id: 2, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
        { policy_id: 4, folder_id: DEFAULT_BOOKMARK_FOLDER_ID },
      ],
      conditions: null,
      updated_at: '2026-08-11T10:00:00.000Z',
    },
    storage,
  );
}

test('readFavoritePolicyIds는 storage bookmarks에서 policy id를 반환한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeDefaultPayload(storage);

    assert.deepEqual(readFavoritePolicyIds(), [2, 4]);
    assert.equal(isFavoritePolicyId(2), true);
    assert.equal(isFavoritePolicyId(99), false);
  } finally {
    windowPatch.restore();
  }
});

test('setBookmarkPolicy와 removeBookmarkPolicy는 folder bookmark를 추가·제거한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const added = setBookmarkPolicy(5, DEFAULT_BOOKMARK_FOLDER_ID);
    assert.equal(added.changed, true);
    assert.equal(added.isFavorite, true);
    assert.deepEqual(added.favorites, [5]);

    const removed = removeBookmarkPolicy(5);
    assert.equal(removed.changed, true);
    assert.equal(removed.isFavorite, false);
    assert.deepEqual(removed.favorites, []);

    const raw = storage.getItem(USER_LOCAL_STORAGE_KEY);
    assert.ok(raw?.includes('"bookmarks":[]'));
  } finally {
    windowPatch.restore();
  }
});

test('createBookmarkFolder는 folder를 추가하고 setBookmarkPolicy가 folder id를 사용한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const created = createBookmarkFolder('주거정책모음');
    assert.equal(created.changed, true);
    assert.ok(created.folder);

    const saved = setBookmarkPolicy(7, created.folder!.id);
    assert.equal(saved.changed, true);
    assert.equal(getBookmarkFolderForPolicy(7), created.folder!.id);
    assert.deepEqual(getPolicyIdsForFolder(created.folder!.id), [7]);
  } finally {
    windowPatch.restore();
  }
});

test('isDeletableBookmarkFolder는 기본 폴더만 삭제 불가', () => {
  assert.equal(isDeletableBookmarkFolder(DEFAULT_BOOKMARK_FOLDER_ID), false);
  assert.equal(isDeletableBookmarkFolder('folder-custom-1'), true);
});

test('deleteBookmarkFolder는 사용자 폴더와 포함 북마크를 제거한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const created = createBookmarkFolder('삭제 대상');
    assert.ok(created.folder);
    setBookmarkPolicy(9, created.folder!.id);

    const deleted = deleteBookmarkFolder(created.folder!.id);
    assert.equal(deleted.changed, true);
    assert.equal(deleted.deletedBookmarkCount, 1);
    assert.equal(
      deleted.folders.some((folder) => folder.id === created.folder!.id),
      false,
    );
    assert.equal(getBookmarkFolderForPolicy(9), null);
    assert.deepEqual(readFavoritePolicyIds(), []);
  } finally {
    windowPatch.restore();
  }
});

test('deleteBookmarkFolder는 기본 폴더 삭제를 거부한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeDefaultPayload(storage);

    const deleted = deleteBookmarkFolder(DEFAULT_BOOKMARK_FOLDER_ID);
    assert.equal(deleted.changed, false);
    assert.equal(deleted.deletedBookmarkCount, 0);
    assert.deepEqual(readFavoritePolicyIds(), [2, 4]);
  } finally {
    windowPatch.restore();
  }
});

test('toggleFavoritePolicyId는 default folder에 추가하고 제거한다', () => {
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
  } finally {
    windowPatch.restore();
  }
});

test('getFavoritePolicyIdsSnapshot은 연속 호출에서 동일 참조를 유지한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    writeDefaultPayload(storage);

    const unsubscribe = subscribeFavoritePolicyIds(() => undefined);
    const first = getFavoritePolicyIdsSnapshot();
    const second = getFavoritePolicyIdsSnapshot();

    assert.equal(first, second);
    assert.deepEqual(first.favorites, [2, 4]);
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('setBookmarkPolicy는 snapshot 참조를 내용 변경 시에만 갱신한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const unsubscribe = subscribeFavoritePolicyIds(() => undefined);
    const before = getFavoritePolicyIdsSnapshot();

    setBookmarkPolicy(5, DEFAULT_BOOKMARK_FOLDER_ID);

    const after = getFavoritePolicyIdsSnapshot();
    assert.notDeepEqual(before.favorites, after.favorites);
    assert.equal(after, getFavoritePolicyIdsSnapshot());
    unsubscribe();
  } finally {
    windowPatch.restore();
  }
});

test('setBookmarkPolicy는 invalid id를 무시한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    const result = setBookmarkPolicy(-1, DEFAULT_BOOKMARK_FOLDER_ID);
    assert.equal(result.changed, false);
    assert.deepEqual(result.favorites, []);
  } finally {
    windowPatch.restore();
  }
});

test('readUserLocalStorage v1 migrate 후 favorites API가 동작한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    storage.setItem(
      USER_LOCAL_STORAGE_KEY,
      JSON.stringify({
        schema_version: 1,
        favorites: [12],
        conditions: null,
        updated_at: '2026-08-11T10:00:00.000Z',
      }),
    );

    assert.deepEqual(readFavoritePolicyIds(), [12]);
    assert.equal(getBookmarkFolderForPolicy(12), DEFAULT_BOOKMARK_FOLDER_ID);
  } finally {
    windowPatch.restore();
  }
});
