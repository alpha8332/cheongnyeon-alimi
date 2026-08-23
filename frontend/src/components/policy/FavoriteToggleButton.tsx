import { useState } from 'react';
import BookmarkFolderPickerModal from '@/components/user/BookmarkFolderPickerModal';
import { useFavorites } from '@/hooks/useFavorites';

interface FavoriteToggleButtonProps {
  policyId: number;
  className?: string;
  /** Sticky action bar 등에서 텍스트 라벨 버튼으로 표시 */
  labeled?: boolean;
}

export default function FavoriteToggleButton({
  policyId,
  className = '',
  labeled = false,
}: FavoriteToggleButtonProps) {
  const { isFavorite, getFolderForPolicy } = useFavorites();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const active = isFavorite(policyId);

  return (
    <>
      <button
        type="button"
        className={
          labeled
            ? `btn btn-secondary policy-detail-bookmark-btn${active ? ' policy-detail-bookmark-btn--active' : ''} ${className}`.trim()
            : `favorite-toggle${active ? ' favorite-toggle--active' : ''} ${className}`.trim()
        }
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
        {labeled ? (
          <>
            <span aria-hidden="true">{active ? '★' : '☆'}</span>
            <span>{active ? '북마크 관리' : '북마크 저장'}</span>
          </>
        ) : (
          <span aria-hidden="true">{active ? '★' : '☆'}</span>
        )}
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
