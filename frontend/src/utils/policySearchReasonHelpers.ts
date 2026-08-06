import type {
  InterpretedCondition,
  InterpretedConditionDimension,
  MatchVerdict,
  PolicySearchHit,
  PolicySearchInterpretedConditions,
  PolicySearchResponse,
  ReasonCode,
} from '../types/policySearch.js';

export type ConditionAnalysisStatus =
  | 'match'
  | 'mismatch'
  | 'unknown'
  | 'ambiguous'
  | 'unmapped'
  | 'keyword'
  | 'neutral';

export interface ConditionAnalysisRow {
  id: string;
  label: string;
  status: ConditionAnalysisStatus;
}

const CATEGORY_LABELS = {
  housing: '주거',
  finance: '금융',
  welfare: '복지',
  employment: '취업',
  startup: '창업',
  education: '교육',
  other: '기타',
} as const;

const STATUS_LABELS = {
  open: '접수 중',
  closed: '마감',
  scheduled: '예정',
} as const;

const DIMENSION_LABELS: Record<InterpretedConditionDimension, string> = {
  keyword: '키워드',
  region: '지역',
  age: '연령',
  category: '카테고리',
  status: '신청상태',
};

const VERDICT_SHORT_LABELS: Record<MatchVerdict, string> = {
  match: '일치',
  mismatch: '불일치',
  unknown: '미확인',
};

const KNOWN_REASON_CODE_LABELS: Record<string, string> = {
  REGION_MATCH: '지역 조건이 일치합니다.',
  REGION_MISMATCH: '지역 조건이 일치하지 않습니다.',
  REGION_UNKNOWN: '지역 정보가 없어 판정할 수 없습니다.',
  AGE_MATCH: '연령 조건이 일치합니다.',
  AGE_MISMATCH: '연령 조건이 일치하지 않습니다.',
  CATEGORY_MATCH: '카테고리 조건이 일치합니다.',
  CATEGORY_UNKNOWN: '카테고리 정보가 없어 판정할 수 없습니다.',
  STATUS_MATCH: '신청 상태 조건이 일치합니다.',
  KEYWORD_MATCH: '키워드 텍스트 매칭이 적용되었습니다.',
  PARTIAL_POLICY_DATA: '정책 데이터가 partial 품질입니다.',
};

function formatConditionValue(
  dimension: InterpretedConditionDimension,
  value: InterpretedCondition['value'],
): string {
  switch (dimension) {
    case 'age':
      return `${value}세`;
    case 'category':
      return CATEGORY_LABELS[value as keyof typeof CATEGORY_LABELS] ?? String(value);
    case 'status':
      return STATUS_LABELS[value as keyof typeof STATUS_LABELS] ?? String(value);
    default:
      return String(value);
  }
}

function getVerdictForDimension(
  hit: PolicySearchHit | null | undefined,
  dimension: InterpretedConditionDimension,
): MatchVerdict | null {
  if (!hit || dimension === 'keyword') {
    return null;
  }

  if (dimension === 'region') {
    return hit.verdicts.region;
  }

  if (dimension === 'age') {
    return hit.verdicts.age;
  }

  if (dimension === 'category') {
    return hit.verdicts.category;
  }

  return hit.verdicts.status;
}

function buildAnalysisLabel(
  condition: InterpretedCondition,
  hit: PolicySearchHit | null | undefined,
): { label: string; status: ConditionAnalysisStatus } {
  const dimensionLabel = DIMENSION_LABELS[condition.dimension];
  const formattedValue = formatConditionValue(condition.dimension, condition.value);

  if (condition.resolution === 'ambiguous') {
    return {
      label: `${dimensionLabel}: ${formattedValue} — 후보 확인 필요`,
      status: 'ambiguous',
    };
  }

  if (condition.resolution === 'unmapped') {
    return {
      label: `${dimensionLabel}: ${formattedValue} — 해석 불가`,
      status: 'unmapped',
    };
  }

  if (condition.dimension === 'keyword') {
    return {
      label: `${dimensionLabel}: ${formattedValue} — 텍스트 매칭`,
      status: 'keyword',
    };
  }

  const verdict = getVerdictForDimension(hit, condition.dimension);

  if (verdict === null) {
    return {
      label: `${dimensionLabel}: ${formattedValue}`,
      status: 'neutral',
    };
  }

  return {
    label: `${dimensionLabel}: ${formattedValue} — ${VERDICT_SHORT_LABELS[verdict]}`,
    status: verdict,
  };
}

export function buildConditionAnalysisRows(
  interpreted: PolicySearchInterpretedConditions | undefined,
  selectedHit: PolicySearchHit | null | undefined,
): ConditionAnalysisRow[] {
  if (!interpreted) {
    return [];
  }

  return interpreted.conditions.map((condition) => {
    const analysis = buildAnalysisLabel(condition, selectedHit);

    return {
      id: `${condition.dimension}-${String(condition.value)}`,
      label: analysis.label,
      status: analysis.status,
    };
  });
}

export function resolvePolicySearchReasonMessage(hit: PolicySearchHit | null | undefined): string | null {
  if (!hit) {
    return null;
  }

  const trimmedMessage = hit.message?.trim();
  if (trimmedMessage) {
    return trimmedMessage;
  }

  const knownLabels = hit.reason_codes
    .map((code) => KNOWN_REASON_CODE_LABELS[code])
    .filter((label): label is string => Boolean(label));

  if (knownLabels.length > 0) {
    return knownLabels.join(' ');
  }

  if (hit.reason_codes.length > 0) {
    return hit.reason_codes.join(', ');
  }

  return null;
}

export function buildUninterpretedNotices(
  interpreted: PolicySearchInterpretedConditions | undefined,
): string[] {
  if (!interpreted) {
    return [];
  }

  return interpreted.uninterpreted_terms
    .map((term) => term.trim())
    .filter(Boolean)
    .map(
      (term) =>
        `※ '${term}'은(는) 조건 Chip으로 파싱되지 않아 키워드 매칭만 적용됩니다.`,
    );
}

export function hasQueryLevelWarnings(
  interpreted: PolicySearchInterpretedConditions | undefined,
): boolean {
  if (!interpreted) {
    return false;
  }

  return interpreted.conditions.some(
    (condition) =>
      condition.resolution === 'ambiguous' || condition.resolution === 'unmapped',
  );
}

export function buildQueryLevelWarnings(
  interpreted: PolicySearchInterpretedConditions | undefined,
): string[] {
  if (!interpreted) {
    return [];
  }

  const warnings: string[] = [];

  for (const condition of interpreted.conditions) {
    const dimensionLabel = DIMENSION_LABELS[condition.dimension];
    const formattedValue = formatConditionValue(condition.dimension, condition.value);

    if (condition.resolution === 'ambiguous') {
      const candidates = condition.candidates.join(', ');
      warnings.push(
        `${dimensionLabel} '${formattedValue}' 해석이 ambiguous합니다. 후보: ${candidates || '없음'}`,
      );
    }

    if (condition.resolution === 'unmapped') {
      warnings.push(`${dimensionLabel} '${formattedValue}' 값을 검색 조건으로 해석하지 못했습니다.`);
    }
  }

  return warnings;
}

export function pickDefaultSelectedHit(
  response: PolicySearchResponse | null | undefined,
): PolicySearchHit | null {
  return response?.items[0] ?? null;
}

export function findSelectedHit(
  response: PolicySearchResponse | null | undefined,
  selectedPolicyId: number | null,
): PolicySearchHit | null {
  if (!response || selectedPolicyId === null) {
    return pickDefaultSelectedHit(response);
  }

  return response.items.find((hit) => hit.policy.id === selectedPolicyId) ?? null;
}

export function formatReasonCodeSummary(codes: readonly ReasonCode[]): string {
  return codes
    .map((code) => KNOWN_REASON_CODE_LABELS[code] ?? code)
    .join(' · ');
}
