import type {
  InterpretedCondition,
  InterpretedConditionDimension,
  MatchVerdict,
  PolicySearchHit,
  PolicySearchResponse,
} from '@/types/policySearch';
import type { PolicySearchUrlQueryState } from '@/types/policySearchUrlState';
import {
  formatApplicationStatus,
  getCategoryLabel,
} from '@/utils/policyDisplay';
import {
  hasPolicySearchFilterParam,
  type PolicySearchFilterDimension,
} from '@/utils/policySearchFilterMutations';

const EDITABLE_DIMENSIONS = new Set<InterpretedConditionDimension>([
  'keyword',
  'region',
  'age',
  'category',
  'status',
]);

const VERDICT_DIMENSIONS = new Set<InterpretedConditionDimension>([
  'region',
  'age',
  'category',
  'status',
]);

export type InterpretedFilterChipVerdict = MatchVerdict | null;

export interface InterpretedFilterChip {
  id: string;
  dimension: InterpretedConditionDimension | 'include_partial';
  label: string;
  value: InterpretedCondition['value'] | boolean | null;
  source: InterpretedCondition['source'];
  resolution: InterpretedCondition['resolution'];
  verdict: InterpretedFilterChipVerdict;
  removable: boolean;
  editable: boolean;
}

function formatConditionValue(
  dimension: InterpretedConditionDimension,
  value: InterpretedCondition['value'],
): string {
  switch (dimension) {
    case 'keyword':
      return `키워드: ${String(value)}`;
    case 'region':
      return `지역: ${String(value)}`;
    case 'age':
      return `연령: ${value}세`;
    case 'category':
      return `카테고리: ${getCategoryLabel(value as Parameters<typeof getCategoryLabel>[0])}`;
    case 'status':
      return `신청상태: ${formatApplicationStatus(value as Parameters<typeof formatApplicationStatus>[0])}`;
    default:
      return String(value);
  }
}

function aggregateDimensionVerdict(
  items: PolicySearchHit[],
  dimension: InterpretedConditionDimension,
): MatchVerdict | null {
  if (!VERDICT_DIMENSIONS.has(dimension)) {
    return null;
  }

  const verdictKey = dimension as keyof PolicySearchHit['verdicts'];
  const verdicts = items
    .map((hit) => hit.verdicts[verdictKey])
    .filter((verdict): verdict is MatchVerdict => verdict !== null);

  if (verdicts.length === 0) {
    return null;
  }

  if (verdicts.includes('match')) {
    return 'match';
  }

  if (verdicts.includes('unknown')) {
    return 'unknown';
  }

  return 'mismatch';
}

function toFilterDimension(
  dimension: InterpretedConditionDimension | 'include_partial',
): PolicySearchFilterDimension | null {
  if (dimension === 'include_partial') {
    return 'include_partial';
  }

  return dimension;
}

function buildChipFromCondition(
  condition: InterpretedCondition,
  urlState: PolicySearchUrlQueryState,
  items: PolicySearchHit[],
): InterpretedFilterChip {
  const filterDimension = toFilterDimension(condition.dimension);
  const hasUrlParam =
    filterDimension !== null && hasPolicySearchFilterParam(urlState, filterDimension);

  return {
    id: condition.dimension,
    dimension: condition.dimension,
    label: formatConditionValue(condition.dimension, condition.value),
    value: condition.value,
    source: condition.source,
    resolution: condition.resolution,
    verdict: aggregateDimensionVerdict(items, condition.dimension),
    removable: hasUrlParam,
    editable: EDITABLE_DIMENSIONS.has(condition.dimension),
  };
}

function buildIncludePartialChip(
  urlState: PolicySearchUrlQueryState,
): InterpretedFilterChip | null {
  if (urlState.include_partial !== false) {
    return null;
  }

  return {
    id: 'include_partial',
    dimension: 'include_partial',
    label: 'partial 제외',
    value: false,
    source: 'explicit',
    resolution: 'resolved',
    verdict: null,
    removable: true,
    editable: false,
  };
}

function buildFallbackChipsFromUrl(
  urlState: PolicySearchUrlQueryState,
): InterpretedFilterChip[] {
  const chips: InterpretedFilterChip[] = [];

  const keyword = urlState.keyword?.trim();
  if (keyword) {
    chips.push({
      id: 'keyword',
      dimension: 'keyword',
      label: `키워드: ${keyword}`,
      value: keyword,
      source: 'explicit',
      resolution: 'resolved',
      verdict: null,
      removable: true,
      editable: true,
    });
  }

  const region = urlState.region?.trim();
  if (region) {
    chips.push({
      id: 'region',
      dimension: 'region',
      label: `지역: ${region}`,
      value: region,
      source: 'explicit',
      resolution: 'resolved',
      verdict: null,
      removable: true,
      editable: true,
    });
  }

  if (urlState.age !== null && urlState.age !== undefined) {
    chips.push({
      id: 'age',
      dimension: 'age',
      label: `연령: ${urlState.age}세`,
      value: urlState.age,
      source: 'explicit',
      resolution: 'resolved',
      verdict: null,
      removable: true,
      editable: true,
    });
  }

  if (urlState.category) {
    chips.push({
      id: 'category',
      dimension: 'category',
      label: `카테고리: ${getCategoryLabel(urlState.category)}`,
      value: urlState.category,
      source: 'explicit',
      resolution: 'resolved',
      verdict: null,
      removable: true,
      editable: true,
    });
  }

  if (urlState.status) {
    chips.push({
      id: 'status',
      dimension: 'status',
      label: `신청상태: ${formatApplicationStatus(urlState.status)}`,
      value: urlState.status,
      source: 'explicit',
      resolution: 'resolved',
      verdict: null,
      removable: true,
      editable: true,
    });
  }

  const includePartialChip = buildIncludePartialChip(urlState);
  if (includePartialChip) {
    chips.push(includePartialChip);
  }

  return chips;
}

/** Build interactive filter chips from in-memory response + URL flat params. */
export function buildInterpretedFilterChips(
  urlState: PolicySearchUrlQueryState,
  response?: PolicySearchResponse | null,
): InterpretedFilterChip[] {
  if (!response?.interpreted_conditions) {
    return buildFallbackChipsFromUrl(urlState);
  }

  const items = response.items ?? [];
  const chips = response.interpreted_conditions.conditions.map((condition) =>
    buildChipFromCondition(condition, urlState, items),
  );

  const includePartialChip = buildIncludePartialChip(urlState);
  if (includePartialChip && !chips.some((chip) => chip.id === 'include_partial')) {
    chips.push(includePartialChip);
  }

  return chips;
}

export function getInterpretedChipClassName(chip: InterpretedFilterChip): string {
  if (chip.resolution === 'ambiguous') {
    return 'chip chip--ambiguous';
  }

  if (chip.resolution === 'unmapped') {
    return 'chip chip--unmapped';
  }

  switch (chip.verdict) {
    case 'match':
      return 'chip chip--match';
    case 'unknown':
      return 'chip chip--unknown';
    case 'mismatch':
      return 'chip chip--mismatch';
    default:
      return 'chip';
  }
}

export function mapChipDimensionToFilterDimension(
  dimension: InterpretedFilterChip['dimension'],
): PolicySearchFilterDimension | null {
  return toFilterDimension(dimension);
}
