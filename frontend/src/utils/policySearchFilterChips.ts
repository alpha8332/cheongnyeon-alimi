import type { PolicySearchUrlQueryState } from '@/types/policySearchUrlState';
import {
  formatApplicationStatus,
  getCategoryLabel,
} from '@/utils/policyDisplay';

export interface UrlFilterChip {
  key: string;
  label: string;
}

/** Build read-only chip labels from flat URL params (no interpreted blob). */
export function buildUrlFilterChips(
  state: PolicySearchUrlQueryState,
): UrlFilterChip[] {
  const chips: UrlFilterChip[] = [];

  const keyword = state.keyword?.trim();
  if (keyword) {
    chips.push({ key: 'keyword', label: `키워드: ${keyword}` });
  }

  const region = state.region?.trim();
  if (region) {
    chips.push({ key: 'region', label: `지역: ${region}` });
  }

  if (state.age !== null && state.age !== undefined) {
    chips.push({ key: 'age', label: `연령: ${state.age}세` });
  }

  if (state.category) {
    chips.push({
      key: 'category',
      label: `카테고리: ${getCategoryLabel(state.category)}`,
    });
  }

  if (state.status) {
    chips.push({
      key: 'status',
      label: `신청상태: ${formatApplicationStatus(state.status)}`,
    });
  }

  if (!state.include_partial) {
    chips.push({ key: 'include_partial', label: 'partial 제외' });
  }

  if (state.page > 1) {
    chips.push({ key: 'page', label: `페이지: ${state.page}` });
  }

  if (state.limit !== 20) {
    chips.push({ key: 'limit', label: `표시: ${state.limit}건` });
  }

  return chips;
}
