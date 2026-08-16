import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import BookmarkCreateFolderDialog from '@/components/bookmarks/BookmarkCreateFolderDialog';
import BookmarkExplorerToolbar from '@/components/bookmarks/BookmarkExplorerToolbar';
import BookmarkFolderGrid from '@/components/bookmarks/BookmarkFolderGrid';
import UserDataResetPanel from '@/components/user/UserDataResetPanel';
import { useFavorites } from '@/hooks/useFavorites';
import type { PolicyDto } from '@/types/policy';
import {
  readBookmarkViewMode,
  readPinnedFolderIds,
  sortBookmarkFolders,
  togglePinnedFolderId,
  writeBookmarkViewMode,
  type BookmarkExplorerViewMode,
  type BookmarkFolderSort,
} from '@/utils/bookmarkExplorer';

type ExplorerPath = 'root' | string;

export default function FavoritesPage() {
  const { favorites, folders, getFavoritesForFolder, addFolder } = useFavorites();
  const [explorerPath, setExplorerPath] = useState<ExplorerPath>('root');
  const [sortBy, setSortBy] = useState<BookmarkFolderSort>('name');
  const [viewMode, setViewMode] = useState<BookmarkExplorerViewMode>(() =>
    readBookmarkViewMode(),
  );
  const [pinnedFolderIds, setPinnedFolderIds] = useState<string[]>(() =>
    readPinnedFolderIds(),
  );
  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const activeFolderId =
    explorerPath === 'root'
      ? null
      : folders.some((folder) => folder.id === explorerPath)
        ? explorerPath
        : null;

  const activeFolder = activeFolderId
    ? folders.find((folder) => folder.id === activeFolderId) ?? null
    : null;

  const sortedFolders = useMemo(
    () =>
      sortBookmarkFolders(
        folders,
        (folderId) => getFavoritesForFolder(folderId).length,
        sortBy,
        pinnedFolderIds,
      ),
    [folders, getFavoritesForFolder, pinnedFolderIds, sortBy],
  );

  const visiblePolicyIds = useMemo(() => {
    if (activeFolderId === null) {
      return [];
    }

    return [...getFavoritesForFolder(activeFolderId)];
  }, [activeFolderId, getFavoritesForFolder]);

  const policyQueries = useQueries({
    queries: visiblePolicyIds.map((policyId) => ({
      queryKey: ['policy', policyId, { include_partial: true }],
      queryFn: () => getPolicyById(policyId, true),
      enabled: policyId > 0,
    })),
  });

  const resolvedPolicies = useMemo(() => {
    const policies: PolicyDto[] = [];

    for (const query of policyQueries) {
      if (query.data) {
        policies.push(query.data);
      }
    }

    return policies;
  }, [policyQueries]);

  const isLoading =
    visiblePolicyIds.length > 0 && policyQueries.some((query) => query.isLoading);
  const isError =
    visiblePolicyIds.length > 0 &&
    policyQueries.some((query) => query.isError) &&
    resolvedPolicies.length === 0;
  const missingCount = visiblePolicyIds.length - resolvedPolicies.length;

  const handleViewModeChange = useCallback((mode: BookmarkExplorerViewMode) => {
    setViewMode(mode);
    writeBookmarkViewMode(mode);
  }, []);

  const handleTogglePin = useCallback((folderId: string) => {
    setPinnedFolderIds(togglePinnedFolderId(folderId));
  }, []);

  const handleCreateFolder = useCallback(
    (name: string) => {
      const created = addFolder(name);
      if (!created.changed || created.folder === null) {
        return false;
      }

      setStatusMessage(`"${created.folder.name}" 폴더를 만들었습니다.`);
      setExplorerPath(created.folder.id);
      return true;
    },
    [addFolder],
  );

  const handleOpenFolder = useCallback((folderId: string) => {
    setExplorerPath(folderId);
    setStatusMessage(null);
  }, []);

  const handleBackToRoot = useCallback(() => {
    setExplorerPath('root');
    setStatusMessage(null);
  }, []);

  const breadcrumbs =
    activeFolder === null
      ? [{ label: '북마크' }]
      : [
          { label: '북마크', onClick: handleBackToRoot },
          { label: activeFolder.name },
        ];

  const policyContainerClass =
    viewMode === 'grid'
      ? 'cards-grid bookmark-policy-grid'
      : 'bookmark-policy-list';

  return (
    <div className="page favorites-page bookmark-explorer">
      <header className="greeting">
        <h1 className="greeting__title">북마크</h1>
        <p className="greeting__subtitle">
          {favorites.length > 0 ? (
            <>
              저장한 정책 {favorites.length}건 · 폴더 {folders.length}개 ·
              브라우저에만 저장됩니다 ·{' '}
              <Link to="/calendar">마감 달력</Link>
            </>
          ) : (
            <>
              폴더별로 정책을 저장할 수 있습니다. 정책 카드의 ☆ 버튼으로
              북마크를 추가해 보세요. 브라우저에만 저장되며 서버와
              동기화되지 않습니다.
            </>
          )}
        </p>
      </header>

      <BookmarkExplorerToolbar
        breadcrumbs={breadcrumbs}
        sort={sortBy}
        viewMode={viewMode}
        onSortChange={setSortBy}
        onViewModeChange={handleViewModeChange}
        showSortControls={activeFolder === null}
      />

      {statusMessage ? (
        <p className="favorites-page__note" role="status">
          {statusMessage}
        </p>
      ) : null}

      {activeFolder === null ? (
        <BookmarkFolderGrid
          folders={sortedFolders}
          viewMode={viewMode}
          pinnedFolderIds={pinnedFolderIds}
          onOpenFolder={handleOpenFolder}
          onCreateFolder={() => setIsCreateFolderOpen(true)}
          onTogglePin={handleTogglePin}
        />
      ) : (
        <>
          {visiblePolicyIds.length === 0 ? (
            <EmptyState message="저장된 정책이 없습니다." />
          ) : null}

          {visiblePolicyIds.length > 0 && isLoading ? (
            <LoadingState message="북마크한 정책을 불러오는 중입니다." />
          ) : null}

          {visiblePolicyIds.length > 0 && !isLoading && isError ? (
            <ErrorState message="북마크한 정책을 불러오지 못했습니다." />
          ) : null}

          {visiblePolicyIds.length > 0 &&
          !isLoading &&
          !isError &&
          resolvedPolicies.length === 0 ? (
            <EmptyState message="북마크한 정책을 찾지 못했습니다. 목록에서 북마크를 다시 확인해 주세요." />
          ) : null}

          {visiblePolicyIds.length > 0 && !isLoading && resolvedPolicies.length > 0 ? (
            <>
              {missingCount > 0 ? (
                <p className="favorites-page__note" role="status">
                  {missingCount}건의 북마크는 현재 데이터에서 찾을 수 없습니다.
                </p>
              ) : null}
              <div className={policyContainerClass}>
                {resolvedPolicies.map((policy) => (
                  <PolicyCard key={policy.id} policy={policy} />
                ))}
              </div>
            </>
          ) : null}
        </>
      )}

      <BookmarkCreateFolderDialog
        isOpen={isCreateFolderOpen}
        onClose={() => setIsCreateFolderOpen(false)}
        onCreate={handleCreateFolder}
      />

      <div className="favorites-page__footer">
        <UserDataResetPanel onReset={() => setExplorerPath('root')} />
      </div>
    </div>
  );
}
