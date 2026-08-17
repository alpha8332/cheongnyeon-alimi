import type { BookmarkFolder } from '../types/userLocalStorage.js';

export type BookmarkFolderSort = 'name' | 'count';
export type BookmarkExplorerViewMode = 'grid' | 'list';

export const BOOKMARK_PINNED_FOLDERS_SESSION_KEY =
  'cheongnyeon-alimi.bookmark-folder-pins';
export const BOOKMARK_VIEW_MODE_SESSION_KEY =
  'cheongnyeon-alimi.bookmark-explorer-view';

export interface BookmarkFolderWithCount extends BookmarkFolder {
  count: number;
}

function compareFolderName(left: BookmarkFolder, right: BookmarkFolder): number {
  return left.name.localeCompare(right.name, 'ko');
}

export function sortBookmarkFolders(
  folders: readonly BookmarkFolder[],
  countForFolder: (folderId: string) => number,
  sort: BookmarkFolderSort,
  pinnedFolderIds: readonly string[],
): BookmarkFolderWithCount[] {
  const withCounts = folders.map((folder) => ({
    ...folder,
    count: countForFolder(folder.id),
  }));

  const pinnedSet = new Set(pinnedFolderIds);

  return [...withCounts].sort((left, right) => {
    const leftPinned = pinnedSet.has(left.id);
    const rightPinned = pinnedSet.has(right.id);

    if (leftPinned !== rightPinned) {
      return leftPinned ? -1 : 1;
    }

    if (sort === 'count') {
      const countDiff = right.count - left.count;
      if (countDiff !== 0) {
        return countDiff;
      }
    }

    return compareFolderName(left, right);
  });
}

export function readPinnedFolderIds(): string[] {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const raw = window.sessionStorage.getItem(BOOKMARK_PINNED_FOLDERS_SESSION_KEY);
    if (!raw) {
      return [];
    }

    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter((item): item is string => typeof item === 'string');
  } catch {
    return [];
  }
}

export function writePinnedFolderIds(folderIds: readonly string[]): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.sessionStorage.setItem(
    BOOKMARK_PINNED_FOLDERS_SESSION_KEY,
    JSON.stringify(folderIds),
  );
}

export function togglePinnedFolderId(folderId: string): string[] {
  const current = readPinnedFolderIds();
  const next = current.includes(folderId)
    ? current.filter((id) => id !== folderId)
    : [...current, folderId];

  writePinnedFolderIds(next);
  return next;
}

export function readBookmarkViewMode(): BookmarkExplorerViewMode {
  if (typeof window === 'undefined') {
    return 'grid';
  }

  const stored = window.sessionStorage.getItem(BOOKMARK_VIEW_MODE_SESSION_KEY);
  return stored === 'list' ? 'list' : 'grid';
}

export function writeBookmarkViewMode(mode: BookmarkExplorerViewMode): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.sessionStorage.setItem(BOOKMARK_VIEW_MODE_SESSION_KEY, mode);
}

export function formatBookmarkFolderLabel(
  folderName: string,
  count: number,
): string {
  return `${folderName} (${count})`;
}
