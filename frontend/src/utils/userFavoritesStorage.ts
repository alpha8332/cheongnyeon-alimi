import {
  DEFAULT_BOOKMARK_FOLDER_ID,
  USER_LOCAL_STORAGE_KEY,
  USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDERS,
  USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDER_NAME,
  USER_LOCAL_STORAGE_MAX_FAVORITES,
  type BookmarkEntry,
  type BookmarkFolder,
} from '../types/userLocalStorage.js';
import { deriveFavoritePolicyIds } from './userLocalStorage.js';
import {
  readUserLocalStorage,
  updateUserLocalStorage,
} from './userLocalStorage.js';

const favoriteListeners = new Set<() => void>();

export interface FavoritesStorageSnapshot {
  favorites: readonly number[];
  folders: readonly BookmarkFolder[];
  bookmarks: readonly BookmarkEntry[];
}

const EMPTY_FAVORITES_SNAPSHOT: FavoritesStorageSnapshot = {
  favorites: [],
  folders: [],
  bookmarks: [],
};

let cachedFavoritesSnapshot: FavoritesStorageSnapshot = EMPTY_FAVORITES_SNAPSHOT;

function arraysEqual(left: readonly number[], right: readonly number[]): boolean {
  if (left.length !== right.length) {
    return false;
  }

  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) {
      return false;
    }
  }

  return true;
}

function foldersEqual(
  left: readonly BookmarkFolder[],
  right: readonly BookmarkFolder[],
): boolean {
  if (left.length !== right.length) {
    return false;
  }

  for (let index = 0; index < left.length; index += 1) {
    if (
      left[index].id !== right[index].id ||
      left[index].name !== right[index].name
    ) {
      return false;
    }
  }

  return true;
}

function bookmarksEqual(
  left: readonly BookmarkEntry[],
  right: readonly BookmarkEntry[],
): boolean {
  if (left.length !== right.length) {
    return false;
  }

  for (let index = 0; index < left.length; index += 1) {
    if (
      left[index].policy_id !== right[index].policy_id ||
      left[index].folder_id !== right[index].folder_id
    ) {
      return false;
    }
  }

  return true;
}

function syncFavoritesSnapshotFromStorage(): void {
  try {
    const data = readUserLocalStorage().data;
    const nextFavorites = deriveFavoritePolicyIds(data.bookmarks);
    const nextFolders = data.bookmark_folders;
    const nextBookmarks = data.bookmarks;

    if (
      arraysEqual(cachedFavoritesSnapshot.favorites, nextFavorites) &&
      foldersEqual(cachedFavoritesSnapshot.folders, nextFolders) &&
      bookmarksEqual(cachedFavoritesSnapshot.bookmarks, nextBookmarks)
    ) {
      return;
    }

    cachedFavoritesSnapshot = {
      favorites: nextFavorites,
      folders: nextFolders,
      bookmarks: nextBookmarks,
    };
  } catch {
    cachedFavoritesSnapshot = EMPTY_FAVORITES_SNAPSHOT;
  }
}

if (typeof window !== 'undefined') {
  try {
    syncFavoritesSnapshotFromStorage();
  } catch {
    cachedFavoritesSnapshot = EMPTY_FAVORITES_SNAPSHOT;
  }
}

export interface ToggleFavoritePolicyResult {
  favorites: readonly number[];
  isFavorite: boolean;
  changed: boolean;
}

export interface SetBookmarkPolicyResult {
  favorites: readonly number[];
  bookmarks: readonly BookmarkEntry[];
  isFavorite: boolean;
  folderId: string | null;
  changed: boolean;
}

export interface CreateBookmarkFolderResult {
  folder: BookmarkFolder | null;
  folders: readonly BookmarkFolder[];
  changed: boolean;
}

export interface DeleteBookmarkFolderResult {
  folders: readonly BookmarkFolder[];
  deletedBookmarkCount: number;
  changed: boolean;
}

function normalizeFolderName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) {
    return null;
  }

  return trimmed.slice(0, USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDER_NAME);
}

function createBookmarkFolderId(name: string): string {
  const slug = name
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]+/gu, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 24);

  return `folder-${slug || 'custom'}-${Date.now()}`;
}

function folderExists(folderId: string, folders: readonly BookmarkFolder[]): boolean {
  return folders.some((folder) => folder.id === folderId);
}

export function isDeletableBookmarkFolder(folderId: string): boolean {
  return folderId !== DEFAULT_BOOKMARK_FOLDER_ID;
}

export function readBookmarkFolders(): readonly BookmarkFolder[] {
  return readUserLocalStorage().data.bookmark_folders;
}

export function readBookmarkEntries(): readonly BookmarkEntry[] {
  return readUserLocalStorage().data.bookmarks;
}

export function readFavoritePolicyIds(): readonly number[] {
  return deriveFavoritePolicyIds(readUserLocalStorage().data.bookmarks);
}

export function getBookmarkFolderForPolicy(policyId: number): string | null {
  if (!Number.isInteger(policyId) || policyId <= 0) {
    return null;
  }

  const entry = readBookmarkEntries().find(
    (bookmark) => bookmark.policy_id === policyId,
  );
  return entry?.folder_id ?? null;
}

export function getPolicyIdsForFolder(folderId: string): readonly number[] {
  return readBookmarkEntries()
    .filter((bookmark) => bookmark.folder_id === folderId)
    .map((bookmark) => bookmark.policy_id);
}

export function isFavoritePolicyId(policyId: number): boolean {
  return readFavoritePolicyIds().includes(policyId);
}

export function notifyFavoritePolicyIdsChanged(): void {
  syncFavoritesSnapshotFromStorage();

  for (const listener of favoriteListeners) {
    listener();
  }
}

export function subscribeFavoritePolicyIds(onStoreChange: () => void): () => void {
  syncFavoritesSnapshotFromStorage();
  favoriteListeners.add(onStoreChange);

  if (typeof window !== 'undefined') {
    const onStorage = (event: StorageEvent) => {
      if (event.key === null || event.key === USER_LOCAL_STORAGE_KEY) {
        syncFavoritesSnapshotFromStorage();
        onStoreChange();
      }
    };
    window.addEventListener('storage', onStorage);

    return () => {
      favoriteListeners.delete(onStoreChange);
      window.removeEventListener('storage', onStorage);
    };
  }

  return () => {
    favoriteListeners.delete(onStoreChange);
  };
}

export function getFavoritePolicyIdsSnapshot(): FavoritesStorageSnapshot {
  return cachedFavoritesSnapshot;
}

export function getFavoritePolicyIdsServerSnapshot(): FavoritesStorageSnapshot {
  return EMPTY_FAVORITES_SNAPSHOT;
}

export function createBookmarkFolder(name: string): CreateBookmarkFolderResult {
  const normalizedName = normalizeFolderName(name);
  if (normalizedName === null) {
    return {
      folder: null,
      folders: readBookmarkFolders(),
      changed: false,
    };
  }

  const current = readUserLocalStorage().data;
  if (current.bookmark_folders.length >= USER_LOCAL_STORAGE_MAX_BOOKMARK_FOLDERS) {
    return {
      folder: null,
      folders: current.bookmark_folders,
      changed: false,
    };
  }

  const folder: BookmarkFolder = {
    id: createBookmarkFolderId(normalizedName),
    name: normalizedName,
  };

  const snapshot = updateUserLocalStorage({
    bookmark_folders: [...current.bookmark_folders, folder],
  });
  notifyFavoritePolicyIdsChanged();

  return {
    folder,
    folders: snapshot.data.bookmark_folders,
    changed: true,
  };
}

export function deleteBookmarkFolder(folderId: string): DeleteBookmarkFolderResult {
  if (!isDeletableBookmarkFolder(folderId)) {
    return {
      folders: readBookmarkFolders(),
      deletedBookmarkCount: 0,
      changed: false,
    };
  }

  const current = readUserLocalStorage().data;
  if (!folderExists(folderId, current.bookmark_folders)) {
    return {
      folders: current.bookmark_folders,
      deletedBookmarkCount: 0,
      changed: false,
    };
  }

  const removedBookmarks = current.bookmarks.filter(
    (bookmark) => bookmark.folder_id === folderId,
  );
  const nextBookmarks = current.bookmarks.filter(
    (bookmark) => bookmark.folder_id !== folderId,
  );
  const nextFolders = current.bookmark_folders.filter(
    (folder) => folder.id !== folderId,
  );

  const snapshot = updateUserLocalStorage({
    bookmark_folders: nextFolders,
    bookmarks: nextBookmarks,
  });
  notifyFavoritePolicyIdsChanged();

  return {
    folders: snapshot.data.bookmark_folders,
    deletedBookmarkCount: removedBookmarks.length,
    changed: true,
  };
}

export function setBookmarkPolicy(
  policyId: number,
  folderId: string,
): SetBookmarkPolicyResult {
  if (!Number.isInteger(policyId) || policyId <= 0) {
    const favorites = readFavoritePolicyIds();
    return {
      favorites,
      bookmarks: readBookmarkEntries(),
      isFavorite: false,
      folderId: null,
      changed: false,
    };
  }

  const current = readUserLocalStorage().data;
  if (!folderExists(folderId, current.bookmark_folders)) {
    const favorites = readFavoritePolicyIds();
    return {
      favorites,
      bookmarks: current.bookmarks,
      isFavorite: isFavoritePolicyId(policyId),
      folderId: getBookmarkFolderForPolicy(policyId),
      changed: false,
    };
  }

  const existingIndex = current.bookmarks.findIndex(
    (bookmark) => bookmark.policy_id === policyId,
  );

  if (existingIndex >= 0) {
    const existing = current.bookmarks[existingIndex];
    if (existing.folder_id === folderId) {
      return {
        favorites: readFavoritePolicyIds(),
        bookmarks: current.bookmarks,
        isFavorite: true,
        folderId,
        changed: false,
      };
    }

    const nextBookmarks = [...current.bookmarks];
    nextBookmarks[existingIndex] = { policy_id: policyId, folder_id: folderId };
    const snapshot = updateUserLocalStorage({ bookmarks: nextBookmarks });
    notifyFavoritePolicyIdsChanged();

    return {
      favorites: deriveFavoritePolicyIds(snapshot.data.bookmarks),
      bookmarks: snapshot.data.bookmarks,
      isFavorite: true,
      folderId,
      changed: true,
    };
  }

  if (current.bookmarks.length >= USER_LOCAL_STORAGE_MAX_FAVORITES) {
    return {
      favorites: deriveFavoritePolicyIds(current.bookmarks),
      bookmarks: current.bookmarks,
      isFavorite: false,
      folderId: null,
      changed: false,
    };
  }

  const snapshot = updateUserLocalStorage({
    bookmarks: [...current.bookmarks, { policy_id: policyId, folder_id: folderId }],
  });
  notifyFavoritePolicyIdsChanged();

  return {
    favorites: deriveFavoritePolicyIds(snapshot.data.bookmarks),
    bookmarks: snapshot.data.bookmarks,
    isFavorite: true,
    folderId,
    changed: true,
  };
}

export function removeBookmarkPolicy(policyId: number): SetBookmarkPolicyResult {
  if (!Number.isInteger(policyId) || policyId <= 0) {
    const favorites = readFavoritePolicyIds();
    return {
      favorites,
      bookmarks: readBookmarkEntries(),
      isFavorite: false,
      folderId: null,
      changed: false,
    };
  }

  const current = readUserLocalStorage().data;
  const nextBookmarks = current.bookmarks.filter(
    (bookmark) => bookmark.policy_id !== policyId,
  );

  if (nextBookmarks.length === current.bookmarks.length) {
    return {
      favorites: deriveFavoritePolicyIds(current.bookmarks),
      bookmarks: current.bookmarks,
      isFavorite: false,
      folderId: null,
      changed: false,
    };
  }

  const snapshot = updateUserLocalStorage({ bookmarks: nextBookmarks });
  notifyFavoritePolicyIdsChanged();

  return {
    favorites: deriveFavoritePolicyIds(snapshot.data.bookmarks),
    bookmarks: snapshot.data.bookmarks,
    isFavorite: false,
    folderId: null,
    changed: true,
  };
}

/** Legacy toggle — adds to default folder or removes bookmark. */
export function toggleFavoritePolicyId(
  policyId: number,
): ToggleFavoritePolicyResult {
  if (isFavoritePolicyId(policyId)) {
    const removed = removeBookmarkPolicy(policyId);
    return {
      favorites: removed.favorites,
      isFavorite: false,
      changed: removed.changed,
    };
  }

  const added = setBookmarkPolicy(policyId, DEFAULT_BOOKMARK_FOLDER_ID);
  return {
    favorites: added.favorites,
    isFavorite: added.isFavorite,
    changed: added.changed,
  };
}
