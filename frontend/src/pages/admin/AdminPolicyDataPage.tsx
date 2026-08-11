import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import AdminPolicyDataFilters from '@/components/admin/AdminPolicyDataFilters';
import {
  EMPTY_ADMIN_POLICY_FILTER_DRAFT,
  toAdminPolicyListQueryFromDraft,
  type AdminPolicyFilterDraft,
} from '@/utils/adminPolicyFilters';
import AdminPolicyDataTable, {
  AdminPolicyColumnToggle,
} from '@/components/admin/AdminPolicyDataTable';
import AdminPolicyRowDetail from '@/components/admin/AdminPolicyRowDetail';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import {
  useAdminPolicyDetailQuery,
  useAdminPolicyListQuery,
} from '@/hooks/useAdminObservabilityQuery';
import type {
  AdminPolicyListItemDto,
  AdminPolicySortField,
  AdminPolicySortOrder,
} from '@/types/adminPolicyData';
import {
  DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS,
  type AdminPolicyTableColumnKey,
} from '@/utils/adminPolicyTableColumns';
import { clearAdminSession } from '@/utils/adminSessionStorage';

const PAGE_SIZE = 10;

export default function AdminPolicyDataPage() {
  const navigate = useNavigate();
  const { accessToken, logout } = useAdminSession();
  const [filterDraft, setFilterDraft] = useState<AdminPolicyFilterDraft>(
    EMPTY_ADMIN_POLICY_FILTER_DRAFT,
  );
  const [appliedFilters, setAppliedFilters] = useState<AdminPolicyFilterDraft>(
    EMPTY_ADMIN_POLICY_FILTER_DRAFT,
  );
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<AdminPolicySortField>('id');
  const [sortOrder, setSortOrder] = useState<AdminPolicySortOrder>('asc');
  const [visibleColumns, setVisibleColumns] = useState<AdminPolicyTableColumnKey[]>(
    DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS,
  );
  const [selectedPolicyId, setSelectedPolicyId] = useState<number | null>(null);

  const query = useMemo(
    () =>
      toAdminPolicyListQueryFromDraft(
        appliedFilters,
        page,
        PAGE_SIZE,
        sortBy,
        sortOrder,
      ),
    [appliedFilters, page, sortBy, sortOrder],
  );

  const {
    data: listResponse,
    isLoading,
    isError,
    error,
  } = useAdminPolicyListQuery(query, accessToken);

  const {
    data: detailPolicy,
    isLoading: isDetailLoading,
    isError: isDetailError,
  } = useAdminPolicyDetailQuery(selectedPolicyId, accessToken);

  useEffect(() => {
    if (!(error instanceof AdminApiError) || error.status !== 401) {
      return;
    }

    clearAdminSession();
    logout();
    navigate(ADMIN_APP_ROUTES.login, { replace: true });
  }, [error, logout, navigate]);

  const errorMessage =
    error instanceof AdminApiError
      ? error.detail
      : error instanceof Error
        ? error.message
        : '정책 데이터를 불러오지 못했습니다.';

  const handleApplyFilters = () => {
    setAppliedFilters(filterDraft);
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilterDraft(EMPTY_ADMIN_POLICY_FILTER_DRAFT);
    setAppliedFilters(EMPTY_ADMIN_POLICY_FILTER_DRAFT);
    setPage(1);
  };

  const handleToggleColumn = (key: AdminPolicyTableColumnKey) => {
    setVisibleColumns((current) =>
      current.includes(key)
        ? current.filter((columnKey) => columnKey !== key)
        : [...current, key],
    );
  };

  const handleSelectRow = (item: AdminPolicyListItemDto) => {
    setSelectedPolicyId(item.id);
  };

  return (
    <div className="page admin-policy-data-page">
      <header className="greeting">
        <h1 className="greeting__title">정책 데이터</h1>
        <p className="greeting__subtitle">
          승인 Policy projection read-only table (server pagination·allowlist filter)
        </p>
      </header>

      <AdminPolicyColumnToggle
        visibleColumns={visibleColumns}
        onToggle={handleToggleColumn}
      />

      <AdminPolicyDataFilters
        draft={filterDraft}
        onChange={setFilterDraft}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
      />

      {isLoading ? <LoadingState message="정책 데이터를 불러오는 중입니다." /> : null}
      {isError ? <ErrorState message={errorMessage} /> : null}

      {!isLoading && !isError && listResponse && listResponse.items.length === 0 ? (
        <p className="state-message state-message--empty" role="status">
          조건에 맞는 Policy row가 없습니다.
        </p>
      ) : null}

      <div className="admin-policy-data-page__layout">
        {!isLoading && !isError && listResponse && listResponse.items.length > 0 ? (
          <>
            <AdminPolicyDataTable
              items={listResponse.items}
              visibleColumns={visibleColumns}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={(nextSortBy, nextSortOrder) => {
                setSortBy(nextSortBy);
                setSortOrder(nextSortOrder);
                setPage(1);
              }}
              onSelectRow={handleSelectRow}
              selectedPolicyId={selectedPolicyId}
            />

            <nav className="collection-run-pagination" aria-label="정책 pagination">
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                이전
              </button>
              <span className="collection-run-pagination__status" role="status">
                {listResponse.page} / {listResponse.pages} 페이지
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page >= listResponse.pages}
                onClick={() =>
                  setPage((current) => Math.min(listResponse.pages, current + 1))
                }
              >
                다음
              </button>
            </nav>
          </>
        ) : null}

        {selectedPolicyId !== null ? (
          <AdminPolicyRowDetail
            policy={detailPolicy}
            isLoading={isDetailLoading}
            isNotFound={
              !isDetailLoading &&
              !isDetailError &&
              (detailPolicy === null || detailPolicy === undefined)
            }
            onClose={() => setSelectedPolicyId(null)}
          />
        ) : null}
      </div>
    </div>
  );
}
