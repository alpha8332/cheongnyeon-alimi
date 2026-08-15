import { useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import Button from '@/components/common/Button';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import UserDataResetPanel from '@/components/user/UserDataResetPanel';
import { useFavorites } from '@/hooks/useFavorites';
import type { PolicyDto } from '@/types/policy';
import { DEFAULT_BOOKMARK_FOLDER_ID } from '@/types/userLocalStorage';

export default function FavoritesPage() {
  const { favorites, folders, getFavoritesForFolder, addFolder } = useFavorites();
  const [selectedFolderId, setSelectedFolderId] = useState(DEFAULT_BOOKMARK_FOLDER_ID);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [folderStatusMessage, setFolderStatusMessage] = useState<string | null>(null);

  const activeFolderId = folders.some((folder) => folder.id === selectedFolderId)
    ? selectedFolderId
    : folders[0]?.id ?? DEFAULT_BOOKMARK_FOLDER_ID;

  const visiblePolicyIds = useMemo(() => {
    if (favorites.length === 0) {
      return [];
    }

    return [...getFavoritesForFolder(activeFolderId)];
  }, [activeFolderId, favorites.length, getFavoritesForFolder]);

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

  const handleCreateFolder = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const created = addFolder(newFolderName);
    if (!created.changed || created.folder === null) {
      setFolderStatusMessage('폴더를 만들지 못했습니다. 이름을 확인해 주세요.');
      return;
    }

    setSelectedFolderId(created.folder.id);
    setNewFolderName('');
    setIsCreatingFolder(false);
    setFolderStatusMessage(`"${created.folder.name}" 폴더를 만들었습니다.`);
  };

  if (favorites.length === 0) {
    return (
      <div className="page">
        <header className="greeting">
          <h1 className="greeting__title">북마크</h1>
          <p className="greeting__subtitle">
            폴더별로 정책을 저장할 수 있습니다. 브라우저에만 저장되며 서버와
            동기화되지 않습니다.
          </p>
        </header>

        <div className="bookmark-folder-tabs" role="tablist" aria-label="북마크 폴더">
          {folders.map((folder) => {
            const count = getFavoritesForFolder(folder.id).length;
            const isActive = folder.id === activeFolderId;

            return (
              <button
                key={folder.id}
                type="button"
                role="tab"
                className={`bookmark-folder-tabs__btn${isActive ? ' bookmark-folder-tabs__btn--active' : ''}`}
                aria-selected={isActive}
                onClick={() => setSelectedFolderId(folder.id)}
              >
                {folder.name} ({count})
              </button>
            );
          })}
        </div>

        <div className="bookmark-folder-create">
          {!isCreatingFolder ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreatingFolder(true)}
            >
              + 새 폴더 만들기
            </Button>
          ) : (
            <form className="bookmark-folder-create__form" onSubmit={handleCreateFolder}>
              <label className="bookmark-folder-create__label" htmlFor="favorites-new-folder">
                새 폴더 이름
              </label>
              <div className="bookmark-folder-create__row">
                <input
                  id="favorites-new-folder"
                  className="bookmark-folder-create__input"
                  type="text"
                  value={newFolderName}
                  placeholder='예: "취업지원"'
                  onChange={(event) => setNewFolderName(event.target.value)}
                />
                <Button type="submit" disabled={newFolderName.trim().length === 0}>
                  만들기
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    setIsCreatingFolder(false);
                    setNewFolderName('');
                  }}
                >
                  취소
                </Button>
              </div>
            </form>
          )}
        </div>

        {folderStatusMessage ? (
          <p className="favorites-page__note" role="status">
            {folderStatusMessage}
          </p>
        ) : null}

        <EmptyState message="저장한 정책이 없습니다. 정책 카드의 ☆ 버튼으로 북마크를 추가해 보세요." />
        <div className="favorites-page__footer">
          <UserDataResetPanel />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">북마크</h1>
        <p className="greeting__subtitle">
          저장한 정책 {favorites.length}건 · 폴더 {folders.length}개 · 브라우저에만
          저장됩니다 · <Link to="/calendar">마감 달력</Link>
        </p>
      </header>

      <div className="bookmark-folder-tabs" role="tablist" aria-label="북마크 폴더">
        {folders.map((folder) => {
          const count = getFavoritesForFolder(folder.id).length;
          const isActive = folder.id === activeFolderId;

          return (
            <button
              key={folder.id}
              type="button"
              role="tab"
              className={`bookmark-folder-tabs__btn${isActive ? ' bookmark-folder-tabs__btn--active' : ''}`}
              aria-selected={isActive}
              onClick={() => setSelectedFolderId(folder.id)}
            >
              {folder.name} ({count})
            </button>
          );
        })}
      </div>

      <div className="bookmark-folder-create">
        {!isCreatingFolder ? (
          <Button
            type="button"
            variant="secondary"
            onClick={() => setIsCreatingFolder(true)}
          >
            + 새 폴더 만들기
          </Button>
        ) : (
          <form className="bookmark-folder-create__form" onSubmit={handleCreateFolder}>
            <label className="bookmark-folder-create__label" htmlFor="favorites-new-folder">
              새 폴더 이름
            </label>
            <div className="bookmark-folder-create__row">
              <input
                id="favorites-new-folder"
                className="bookmark-folder-create__input"
                type="text"
                value={newFolderName}
                placeholder='예: "취업지원"'
                onChange={(event) => setNewFolderName(event.target.value)}
              />
              <Button type="submit" disabled={newFolderName.trim().length === 0}>
                만들기
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setIsCreatingFolder(false);
                  setNewFolderName('');
                }}
              >
                취소
              </Button>
            </div>
          </form>
        )}
      </div>

      {folderStatusMessage ? (
        <p className="favorites-page__note" role="status">
          {folderStatusMessage}
        </p>
      ) : null}

      {visiblePolicyIds.length === 0 ? (
        <EmptyState message="이 폴더에 저장된 정책이 없습니다. 정책 카드에서 ☆ 버튼으로 이 폴더에 저장해 보세요." />
      ) : null}

      {visiblePolicyIds.length > 0 && isLoading ? (
        <LoadingState message="북마크한 정책을 불러오는 중입니다." />
      ) : null}

      {visiblePolicyIds.length > 0 && !isLoading && isError ? (
        <ErrorState message="북마크한 정책을 불러오지 못했습니다." />
      ) : null}

      {visiblePolicyIds.length > 0 && !isLoading && !isError && resolvedPolicies.length === 0 ? (
        <EmptyState message="북마크한 정책을 찾지 못했습니다. 목록에서 북마크를 다시 확인해 주세요." />
      ) : null}

      {visiblePolicyIds.length > 0 && !isLoading && resolvedPolicies.length > 0 ? (
        <>
          {missingCount > 0 ? (
            <p className="favorites-page__note" role="status">
              {missingCount}건의 북마크는 현재 데이터에서 찾을 수 없습니다.
            </p>
          ) : null}
          <div className="cards-grid">
            {resolvedPolicies.map((policy) => (
              <PolicyCard key={policy.id} policy={policy} />
            ))}
          </div>
        </>
      ) : null}

      <div className="favorites-page__footer">
        <UserDataResetPanel />
      </div>
    </div>
  );
}
