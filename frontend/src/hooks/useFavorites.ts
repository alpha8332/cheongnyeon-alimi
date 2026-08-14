import { useCallback, useSyncExternalStore } from 'react';
import {
  getFavoritePolicyIdsServerSnapshot,
  getFavoritePolicyIdsSnapshot,
  subscribeFavoritePolicyIds,
  toggleFavoritePolicyId,
} from '@/utils/userFavoritesStorage';

export function useFavorites() {
  const favorites = useSyncExternalStore(
    subscribeFavoritePolicyIds,
    getFavoritePolicyIdsSnapshot,
    getFavoritePolicyIdsServerSnapshot,
  );

  const isFavorite = useCallback(
    (policyId: number) => favorites.includes(policyId),
    [favorites],
  );

  const toggleFavorite = useCallback((policyId: number) => {
    return toggleFavoritePolicyId(policyId);
  }, []);

  return {
    favorites,
    isFavorite,
    toggleFavorite,
  };
}
