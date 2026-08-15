import { useState } from 'react';
import BookmarkFolderPickerModal from '@/components/user/BookmarkFolderPickerModal';
import { useFavorites } from '@/hooks/useFavorites';

interface FavoriteToggleButtonProps {
  policyId: number;
  className?: string;
}

export default function FavoriteToggleButton({
  policyId,
  className = '',
}: FavoriteToggleButtonProps) {
  const { isFavorite, getFolderForPolicy } = useFavorites();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const active = isFavorite(policyId);

  return (
    <>
      <button
        type="button"
        className={`favorite-toggle${active ? ' favorite-toggle--active' : ''} ${className}`.trim()}
        aria-pressed={active}
        aria-haspopup="dialog"
        aria-label={active ? '북마크 폴더 관리' : '북마크 추가'}
        title={active ? '북마크 폴더 관리' : '북마크 추가'}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          setIsModalOpen(true);
        }}
      >
        <span aria-hidden="true">{active ? '★' : '☆'}</span>
      </button>

      {isModalOpen ? (
        <BookmarkFolderPickerModal
          key={`${policyId}-${active}-${getFolderForPolicy(policyId) ?? 'none'}`}
          policyId={policyId}
          isBookmarked={active}
          currentFolderId={getFolderForPolicy(policyId)}
          onClose={() => setIsModalOpen(false)}
        />
      ) : null}
    </>
  );
}
