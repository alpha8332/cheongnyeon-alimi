import type { PolicySort } from '@/types/policy';
import { POLICY_SORT_OPTIONS } from '@/utils/policySort';
import './PolicySortSelect.css';

interface PolicySortSelectProps {
  value: PolicySort;
  onChange: (sort: PolicySort) => void;
  defaultLabel: string;
  disabled?: boolean;
}

export default function PolicySortSelect({
  value,
  onChange,
  defaultLabel,
  disabled = false,
}: PolicySortSelectProps) {
  return (
    <label className="policy-sort-select">
      <span className="policy-sort-select__label">정렬</span>
      <select
        className="field__select policy-sort-select__control"
        value={value}
        onChange={(event) => onChange(event.target.value as PolicySort)}
        disabled={disabled}
        aria-label="검색 결과 정렬"
      >
        {POLICY_SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.value === 'default' ? defaultLabel : option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
