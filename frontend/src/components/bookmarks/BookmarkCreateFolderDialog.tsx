import { useEffect, useId, useState, type FormEvent } from 'react';
import Button from '@/components/common/Button';

interface BookmarkCreateFolderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string) => boolean;
}

export default function BookmarkCreateFolderDialog({
  isOpen,
  onClose,
  onCreate,
}: BookmarkCreateFolderDialogProps) {
  const titleId = useId();
  const inputId = useId();
  const [folderName, setFolderName] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleClose = () => {
    setFolderName('');
    setErrorMessage(null);
    onClose();
  };

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setFolderName('');
        setErrorMessage(null);
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const created = onCreate(folderName);
    if (!created) {
      setErrorMessage('폴더를 만들지 못했습니다. 이름을 확인해 주세요.');
      return;
    }

    setFolderName('');
    setErrorMessage(null);
    onClose();
  };

  return (
    <div
      className="bookmark-modal-overlay"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          handleClose();
        }
      }}
    >
      <div
        className="bookmark-modal bookmark-create-folder-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id={titleId} className="bookmark-modal__title">
          새 폴더 만들기
        </h2>
        <p className="bookmark-modal__description">
          북마크를 분류할 폴더 이름을 입력해 주세요.
        </p>

        <form className="bookmark-create-folder-dialog__form" onSubmit={handleSubmit}>
          <label className="bookmark-folder-create__label" htmlFor={inputId}>
            새 폴더 이름
          </label>
          <input
            id={inputId}
            className="bookmark-folder-create__input"
            type="text"
            value={folderName}
            placeholder='예: "취업지원"'
            autoFocus
            onChange={(event) => {
              setFolderName(event.target.value);
              setErrorMessage(null);
            }}
          />

          {errorMessage ? (
            <p className="bookmark-modal__status" role="alert">
              {errorMessage}
            </p>
          ) : null}

          <div className="bookmark-modal__actions">
            <Button type="button" variant="secondary" onClick={handleClose}>
              취소
            </Button>
            <Button type="submit" disabled={folderName.trim().length === 0}>
              만들기
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
