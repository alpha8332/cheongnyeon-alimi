import type { PolicyCategory } from '@/types/policy';
import { HOME_REGION_GROUPS } from '@/utils/homeSearchRegions';
import { SAVED_CONDITIONS_CATEGORY_OPTIONS } from '@/utils/savedConditionsForm';
import { getCategoryLabel } from '@/utils/policyDisplay';

interface HomeSearchConditionsProps {
  province: string;
  district: string;
  category: PolicyCategory | null;
  useSavedConditions: boolean;
  disabled?: boolean;
  onProvinceChange: (province: string) => void;
  onDistrictChange: (district: string) => void;
  onCategoryChange: (category: PolicyCategory | null) => void;
  onUseSavedConditionsChange: (enabled: boolean) => void;
  onReset: () => void;
}

export default function HomeSearchConditions({
  province,
  district,
  category,
  useSavedConditions,
  disabled = false,
  onProvinceChange,
  onDistrictChange,
  onCategoryChange,
  onUseSavedConditionsChange,
  onReset,
}: HomeSearchConditionsProps) {
  const selectedProvince = HOME_REGION_GROUPS.find(
    (group) => group.province === province,
  );
  const hasExplicitCondition = Boolean(province || category);

  return (
    <fieldset className="home-search-conditions" disabled={disabled}>
      <legend>검색 조건</legend>
      {hasExplicitCondition ? (
        <button
          className="home-search-conditions__reset"
          type="button"
          onClick={onReset}
        >
          조건 초기화
        </button>
      ) : null}

      <div className="home-search-conditions__fields">
        <label>
          <span>시·도</span>
          <select
            aria-label="시·도"
            value={province}
            onChange={(event) => onProvinceChange(event.target.value)}
          >
            <option value="">전체 지역</option>
            {HOME_REGION_GROUPS.map((group) => (
              <option key={group.province} value={group.province}>
                {group.province}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>시·군·구</span>
          <select
            aria-label="시·군·구"
            value={district}
            disabled={!selectedProvince || selectedProvince.districts.length === 0}
            onChange={(event) => onDistrictChange(event.target.value)}
          >
            <option value="">전체</option>
            {selectedProvince?.districts.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>관심 분야</span>
          <select
            aria-label="관심 분야 검색 조건"
            value={category ?? ''}
            onChange={(event) =>
              onCategoryChange(
                (event.target.value || null) as PolicyCategory | null,
              )
            }
          >
            <option value="">전체 분야</option>
            {SAVED_CONDITIONS_CATEGORY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {getCategoryLabel(option)}
              </option>
            ))}
          </select>
        </label>

        <label className="home-search-conditions__profile-toggle">
          <input
            type="checkbox"
            checked={useSavedConditions}
            onChange={(event) => onUseSavedConditionsChange(event.target.checked)}
          />
          <span>저장 프로필로 관련도 보정</span>
        </label>
      </div>

      <p className="home-search-conditions__help">
        지역을 선택하면 해당 지역과 상위 지역·전국 대상 정책을 함께 찾습니다.
      </p>
    </fieldset>
  );
}
