import { useState } from 'react';
import type { BookmarkExplorerViewMode } from '@/utils/bookmarkExplorer';
import {
  formatBookmarkFolderLabel,
  type BookmarkFolderWithCount,
} from '@/utils/bookmarkExplorer';

interface BookmarkFolderGridProps {
  folders: BookmarkFolderWithCount[];
  viewMode: BookmarkExplorerViewMode;
  pinnedFolderIds: readonly string[];
  onOpenFolder: (folderId: string) => void;
  onCreateFolder: () => void;
  onTogglePin: (folderId: string) => void;
}

function FolderIconGraphic() {
  return (
    <svg
      className="bookmark-folder-card__icon-svg"
      viewBox="0 0 64 48"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M4 12c0-2.2 1.8-4 4-4h14l6 6h32c2.2 0 4 1.8 4 4v24c0 2.2-1.8 4-4 4H8c-2.2 0-4-1.8-4-4V12z"
        fill="currentColor"
      />
      <path
        d="M4 18h56v22c0 2.2-1.8 4-4 4H8c-2.2 0-4-1.8-4-4V18z"
        fill="currentColor"
        opacity="0.85"
      />
    </svg>
  );
}

export default function BookmarkFolderGrid({
  folders,
  viewMode,
  pinnedFolderIds,
  onOpenFolder,
  onCreateFolder,
  onTogglePin,
}: BookmarkFolderGridProps) {
  const [openMenuFolderId, setOpenMenuFolderId] = useState<string | null>(null);
  const gridClass =
    viewMode === 'grid'
      ? 'bookmark-folder-grid bookmark-folder-grid--grid'
      : 'bookmark-folder-grid bookmark-folder-grid--list';

  return (
    <div className={gridClass} aria-label="북마크 폴더">
      <button
        type="button"
        className="bookmark-folder-card bookmark-folder-card--new"
        aria-label="새 폴더 만들기"
        onClick={onCreateFolder}
      >
        <span className="bookmark-folder-card__new-icon" aria-hidden="true">
          +
        </span>
        <span className="bookmark-folder-card__label">새 폴더</span>
      </button>

      {folders.map((folder) => {
        const label = formatBookmarkFolderLabel(folder.name, folder.count);
        const isPinned = pinnedFolderIds.includes(folder.id);
        const menuOpen = openMenuFolderId === folder.id;

        return (
          <article
            key={folder.id}
            className={`bookmark-folder-card${viewMode === 'list' ? ' bookmark-folder-card--list' : ''}`}
          >
            <button
              type="button"
              className="bookmark-folder-card__open"
              aria-label={label}
              onClick={() => onOpenFolder(folder.id)}
            >
              <span className="bookmark-folder-card__icon-wrap">
                <FolderIconGraphic />
              </span>
              <span className="bookmark-folder-card__label">{label}</span>
            </button>

            <div className="bookmark-folder-card__actions">
              <button
                type="button"
                className={`bookmark-folder-card__star${isPinned ? ' bookmark-folder-card__star--active' : ''}`}
                aria-label={isPinned ? `${folder.name} 즐겨찾기 해제` : `${folder.name} 즐겨찾기`}
                aria-pressed={isPinned}
                onClick={(event) => {
                  event.stopPropagation();
                  onTogglePin(folder.id);
                }}
              >
                {isPinned ? '★' : '☆'}
              </button>

              <div className="bookmark-folder-card__menu-wrap">
                <button
                  type="button"
                  className="bookmark-folder-card__menu-btn"
                  aria-label={`${folder.name} 폴더 옵션`}
                  aria-expanded={menuOpen}
                  aria-haspopup="menu"
                  onClick={(event) => {
                    event.stopPropagation();
                    setOpenMenuFolderId(menuOpen ? null : folder.id);
                  }}
                >
                  ···
                </button>
                {menuOpen ? (
                  <div className="bookmark-folder-card__menu" role="menu">
                    <button
                      type="button"
                      role="menuitem"
                      className="bookmark-folder-card__menu-item"
                      onClick={() => {
                        setOpenMenuFolderId(null);
                        onOpenFolder(folder.id);
                      }}
                    >
                      폴더 열기
                    </button>
                    <button
                      type="button"
                      role="menuitem"
                      className="bookmark-folder-card__menu-item"
                      onClick={() => {
                        setOpenMenuFolderId(null);
                        onTogglePin(folder.id);
                      }}
                    >
                      {isPinned ? '즐겨찾기 해제' : '즐겨찾기'}
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
