import Input from '@/components/common/Input';
import type { ProgramFilterState } from '@/utils/policyFilters';
import type { PolicyCategory } from '@/types/policy';

interface PolicyFiltersProps {
  filters: ProgramFilterState;
  regionOptions: string[];
  onChange: (next: ProgramFilterState) => void;
}

const CATEGORY_OPTIONS: { value: PolicyCategory; label: string }[] = [
  { value: 'housing', label: '주거' },
  { value: 'finance', label: '금융' },
  { value: 'welfare', label: '복지' },
  { value: 'employment', label: '취업' },
  { value: 'startup', label: '창업' },
  { value: 'education', label: '교육' },
  { value: 'other', label: '기타' },
];

export default function PolicyFilters({
  filters,
  regionOptions,
  onChange,
}: PolicyFiltersProps) {
  return (
    <div
      style={{
        border: '1px solid black',
        padding: '10px',
        marginBottom: '16px',
        display: 'grid',
        gap: '10px',
      }}
    >
      <label>
        검색
        <Input
          placeholder="정책명, 키워드 검색"
          value={filters.search}
          onChange={(event) =>
            onChange({ ...filters, search: event.target.value })
          }
          style={{ display: 'block', width: '100%', marginTop: '4px' }}
        />
      </label>

      <label>
        지역
        <select
          value={filters.region}
          onChange={(event) =>
            onChange({ ...filters, region: event.target.value })
          }
          style={{ display: 'block', width: '100%', marginTop: '4px' }}
        >
          <option value="">전체</option>
          {regionOptions.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
      </label>

      <label>
        카테고리
        <select
          value={filters.category}
          onChange={(event) =>
            onChange({
              ...filters,
              category: event.target.value as ProgramFilterState['category'],
            })
          }
          style={{ display: 'block', width: '100%', marginTop: '4px' }}
        >
          <option value="">전체</option>
          {CATEGORY_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        연령
        <Input
          type="number"
          min={0}
          max={150}
          placeholder="예: 25"
          value={filters.age}
          onChange={(event) =>
            onChange({ ...filters, age: event.target.value })
          }
          style={{ display: 'block', width: '100%', marginTop: '4px' }}
        />
      </label>

      <label>
        <input
          type="checkbox"
          checked={filters.includePartial}
          onChange={(event) =>
            onChange({ ...filters, includePartial: event.target.checked })
          }
        />{' '}
        정보가 일부 누락된 정책 포함
      </label>
    </div>
  );
}
