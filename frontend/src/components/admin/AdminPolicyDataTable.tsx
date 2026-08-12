import { useEffect, useId, useState } from 'react';
import type {
  AdminPolicyListItemDto,
  AdminPolicySortField,
  AdminPolicySortOrder,
} from '@/types/adminPolicyData';
import {
  ADMIN_POLICY_TABLE_COLUMNS,
  formatAdminPolicyCellValue,
  isAdminPolicySortField,
  shouldExpandAdminPolicyCell,
  truncateAdminPolicyCell,
  type AdminPolicyTableColumnKey,
} from '@/utils/adminPolicyTableColumns';

interface AdminPolicyDataTableProps {
  items: AdminPolicyListItemDto[];
  visibleColumns: AdminPolicyTableColumnKey[];
  sortBy: AdminPolicySortField;
  sortOrder: AdminPolicySortOrder;
  onSortChange: (sortBy: AdminPolicySortField, sortOrder: AdminPolicySortOrder) => void;
  onSelectRow: (item: AdminPolicyListItemDto) => void;
  selectedPolicyId: number | null;
}

function nextSortOrder(
  currentField: AdminPolicySortField,
  currentOrder: AdminPolicySortOrder,
  clickedField: AdminPolicySortField,
): AdminPolicySortOrder {
  if (currentField !== clickedField) {
    return 'asc';
  }

  return currentOrder === 'asc' ? 'desc' : 'asc';
}

export default function AdminPolicyDataTable({
  items,
  visibleColumns,
  sortBy,
  sortOrder,
  onSortChange,
  onSelectRow,
  selectedPolicyId,
}: AdminPolicyDataTableProps) {
  const [expandedCells, setExpandedCells] = useState<Record<string, boolean>>({});

  const columns = ADMIN_POLICY_TABLE_COLUMNS.filter((column) =>
    visibleColumns.includes(column.key),
  );

  const toggleCellExpand = (rowId: number, columnKey: AdminPolicyTableColumnKey) => {
    const cellKey = `${rowId}:${columnKey}`;
    setExpandedCells((current) => ({
      ...current,
      [cellKey]: !current[cellKey],
    }));
  };

  return (
    <div
      className="admin-policy-table-wrap"
      aria-describedby="admin-policy-table-caption"
    >
      <table className="admin-policy-table">
        <caption id="admin-policy-table-caption" className="admin-policy-table__caption">
          승인 Policy projection ({items.length} rows on page)
        </caption>
        <thead>
          <tr>
            {columns.map((column) => {
              const sortField = isAdminPolicySortField(column.key)
                ? column.key
                : null;

              return (
              <th key={column.key} scope="col">
                {column.sortable && sortField ? (
                  <button
                    type="button"
                    className="admin-policy-table__sort-btn"
                    aria-label={`${column.label} 정렬`}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSortChange(
                        sortField,
                        nextSortOrder(sortBy, sortOrder, sortField),
                      );
                    }}
                  >
                    {column.label}
                    {sortBy === sortField
                      ? sortOrder === 'asc'
                        ? ' ↑'
                        : ' ↓'
                      : null}
                  </button>
                ) : (
                  column.label
                )}
              </th>
              );
            })}
            <th scope="col">상세</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.id}
              className={
                selectedPolicyId === item.id
                  ? 'admin-policy-table__row admin-policy-table__row--selected admin-policy-table__row--interactive'
                  : 'admin-policy-table__row admin-policy-table__row--interactive'
              }
              tabIndex={0}
              aria-selected={selectedPolicyId === item.id}
              onClick={() => onSelectRow(item)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  onSelectRow(item);
                }
              }}
            >
              {columns.map((column) => {
                const rawValue = formatAdminPolicyCellValue(item, column.key);
                const cellKey = `${item.id}:${column.key}`;
                const isExpanded = expandedCells[cellKey] === true;
                const canExpand = shouldExpandAdminPolicyCell(rawValue);
                const displayValue =
                  isExpanded || !canExpand
                    ? rawValue
                    : truncateAdminPolicyCell(rawValue);

                return (
                  <td key={column.key}>
                    <span>{displayValue}</span>
                    {canExpand ? (
                      <button
                        type="button"
                        className="admin-policy-table__expand-btn"
                        aria-expanded={isExpanded}
                        onClick={(event) => {
                          event.stopPropagation();
                          toggleCellExpand(item.id, column.key);
                        }}
                      >
                        {isExpanded ? '접기' : '더 보기'}
                      </button>
                    ) : null}
                  </td>
                );
              })}
              <td>
                <button
                  type="button"
                  className="btn btn-secondary"
                  aria-label={`${item.title} 상세보기`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectRow(item);
                  }}
                >
                  상세보기
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminPolicyColumnToggle({
  visibleColumns,
  onToggle,
}: {
  visibleColumns: AdminPolicyTableColumnKey[];
  onToggle: (key: AdminPolicyTableColumnKey) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const panelId = useId();

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <div className="admin-policy-column-toggle">
      <button
        type="button"
        className="admin-policy-column-toggle__trigger"
        aria-expanded={isOpen}
        aria-controls={panelId}
        onClick={() => setIsOpen((current) => !current)}
      >
        표시 열 설정
      </button>
      {isOpen ? (
        <fieldset id={panelId} className="admin-policy-column-toggle__panel">
          <legend className="admin-policy-column-toggle__legend">표시 열</legend>
          <div className="admin-policy-column-toggle__grid">
            {ADMIN_POLICY_TABLE_COLUMNS.map((column) => (
              <label key={column.key} className="admin-policy-column-toggle__item">
                <input
                  type="checkbox"
                  checked={visibleColumns.includes(column.key)}
                  onChange={() => onToggle(column.key)}
                />
                {column.label}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}
    </div>
  );
}
