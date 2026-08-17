import { useEffect, useId } from 'react';
import Button from '@/components/common/Button';

interface BookmarkDeleteFolderDialogProps {
  isOpen: boolean;
  folderName: string | null;
  onClose: () => void;
  onConfirm: () => void;
}

export default function BookmarkDeleteFolderDialog({
  isOpen,
  folderName,
  onClose,
  onConfirm,
}: BookmarkDeleteFolderDialogProps) {
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !folderName) {
    return null;
  }

  return (
    <div
      className="bookmark-modal-overlay"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="bookmark-modal bookmark-delete-folder-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id={titleId} className="bookmark-modal__title">
          폴더 삭제
        </h2>
        <p id={descriptionId} className="bookmark-modal__description">
          정말 이 폴더를 삭제하시겠습니까?
          <br />
          <strong>{folderName}</strong> 폴더와 포함된 북마크가 브라우저 저장소에서
          제거됩니다.
        </p>

        <div className="bookmark-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose}>
            취소
          </Button>
          <Button
            type="button"
            className="bookmark-delete-folder-dialog__confirm"
            onClick={onConfirm}
          >
            삭제
          </Button>
        </div>
      </div>
    </div>
  );
}
