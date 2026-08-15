import { useCallback, useSyncExternalStore } from 'react';
import {
  createBookmarkFolder,
  getBookmarkFolderForPolicy,
  getFavoritePolicyIdsServerSnapshot,
  getFavoritePolicyIdsSnapshot,
  getPolicyIdsForFolder,
  removeBookmarkPolicy,
  setBookmarkPolicy,
  subscribeFavoritePolicyIds,
  toggleFavoritePolicyId,
} from '@/utils/userFavoritesStorage';

export function useFavorites() {
  const snapshot = useSyncExternalStore(
    subscribeFavoritePolicyIds,
    getFavoritePolicyIdsSnapshot,
    getFavoritePolicyIdsServerSnapshot,
  );

  const { favorites, folders, bookmarks } = snapshot;

  const isFavorite = useCallback(
    (policyId: number) => favorites.includes(policyId),
    [favorites],
  );

  const getFolderForPolicy = useCallback(
    (policyId: number) => getBookmarkFolderForPolicy(policyId),
    [],
  );

  const getFavoritesForFolder = useCallback(
    (folderId: string) => getPolicyIdsForFolder(folderId),
    [],
  );

  const toggleFavorite = useCallback((policyId: number) => {
    return toggleFavoritePolicyId(policyId);
  }, []);

  const saveBookmark = useCallback((policyId: number, folderId: string) => {
    return setBookmarkPolicy(policyId, folderId);
  }, []);

  const removeBookmark = useCallback((policyId: number) => {
    return removeBookmarkPolicy(policyId);
  }, []);

  const addFolder = useCallback((name: string) => {
    return createBookmarkFolder(name);
  }, []);

  return {
    favorites,
    folders,
    bookmarks,
    isFavorite,
    getFolderForPolicy,
    getFavoritesForFolder,
    toggleFavorite,
    saveBookmark,
    removeBookmark,
    addFolder,
  };
}
