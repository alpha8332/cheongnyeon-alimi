import { useFavorites } from '@/hooks/useFavorites';

interface FavoriteToggleButtonProps {
  policyId: number;
  className?: string;
}

export default function FavoriteToggleButton({
  policyId,
  className = '',
}: FavoriteToggleButtonProps) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const active = isFavorite(policyId);

  return (
    <button
      type="button"
      className={`favorite-toggle${active ? ' favorite-toggle--active' : ''} ${className}`.trim()}
      aria-pressed={active}
      aria-label={active ? '북마크 해제' : '북마크 추가'}
      title={active ? '북마크 해제' : '북마크 추가'}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleFavorite(policyId);
      }}
    >
      <span aria-hidden="true">{active ? '★' : '☆'}</span>
    </button>
  );
}
