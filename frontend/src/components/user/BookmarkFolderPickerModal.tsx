import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/common/Button';
import { useFavorites } from '@/hooks/useFavorites';
import {
  DEFAULT_BOOKMARK_FOLDER_ID,
  type BookmarkFolder,
} from '@/types/userLocalStorage';

interface BookmarkFolderPickerModalProps {
  policyId: number;
  isBookmarked: boolean;
  currentFolderId: string | null;
  onClose: () => void;
}

export default function BookmarkFolderPickerModal({
  policyId,
  isBookmarked,
  currentFolderId,
  onClose,
}: BookmarkFolderPickerModalProps) {
  const { folders, saveBookmark, removeBookmark, addFolder } = useFavorites();
  const initialFolderId =
    currentFolderId ??
    folders.find((folder) => folder.id === DEFAULT_BOOKMARK_FOLDER_ID)?.id ??
    folders[0]?.id ??
    DEFAULT_BOOKMARK_FOLDER_ID;

  const [selectedFolderId, setSelectedFolderId] = useState(initialFolderId);
  const [newFolderName, setNewFolderName] = useState('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const folderOptions = useMemo(() => folders as BookmarkFolder[], [folders]);

  const handleCreateFolder = () => {
    const created = addFolder(newFolderName);
    if (!created.changed || created.folder === null) {
      setStatusMessage('폴더를 만들지 못했습니다. 이름을 확인해 주세요.');
      return;
    }

    setSelectedFolderId(created.folder.id);
    setNewFolderName('');
    setStatusMessage(`"${created.folder.name}" 폴더를 만들었습니다.`);
  };

  const handleSave = () => {
    const result = saveBookmark(policyId, selectedFolderId);
    if (!result.changed && !result.isFavorite) {
      setStatusMessage('북마크를 저장하지 못했습니다.');
      return;
    }

    onClose();
  };

  const handleRemove = () => {
    removeBookmark(policyId);
    onClose();
  };

  return (
    <div className="bookmark-modal-overlay" onClick={onClose}>
      <div
        className="bookmark-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="bookmark-folder-picker-title"
        aria-describedby="bookmark-folder-picker-description"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="bookmark-folder-picker-title" className="bookmark-modal__title">
          북마크 저장
        </h2>
        <p id="bookmark-folder-picker-description" className="bookmark-modal__description">
          {isBookmarked
            ? '저장 폴더를 변경하거나 북마크를 해제할 수 있습니다.'
            : '저장할 폴더를 선택해 주세요.'}
        </p>

        <fieldset className="bookmark-modal__folder-list">
          <legend className="bookmark-modal__legend">저장할 폴더</legend>
          {folderOptions.map((folder) => (
            <label key={folder.id} className="bookmark-modal__folder-option">
              <input
                type="radio"
                name="bookmark-folder"
                value={folder.id}
                checked={selectedFolderId === folder.id}
                onChange={() => setSelectedFolderId(folder.id)}
              />
              <span>{folder.name}</span>
            </label>
          ))}
        </fieldset>

        <div className="bookmark-modal__create-folder">
          <label className="bookmark-modal__create-label" htmlFor="bookmark-new-folder-name">
            + 새 폴더 만들기
          </label>
          <div className="bookmark-modal__create-row">
            <input
              id="bookmark-new-folder-name"
              className="bookmark-modal__create-input"
              type="text"
              value={newFolderName}
              placeholder='예: "주거정책모음"'
              onChange={(event) => setNewFolderName(event.target.value)}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={newFolderName.trim().length === 0}
              onClick={handleCreateFolder}
            >
              추가
            </Button>
          </div>
        </div>

        {statusMessage ? (
          <p className="bookmark-modal__status" role="status">
            {statusMessage}
          </p>
        ) : null}

        <div className="bookmark-modal__actions">
          {isBookmarked ? (
            <Button type="button" variant="secondary" onClick={handleRemove}>
              북마크 해제
            </Button>
          ) : null}
          <Button type="button" variant="secondary" onClick={onClose}>
            취소
          </Button>
          <Button type="button" onClick={handleSave}>
            저장
          </Button>
        </div>
      </div>
    </div>
  );
}
