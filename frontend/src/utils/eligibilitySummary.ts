import type {
  EligibilityCategory,
  EligibilityCoverage,
  InstitutionalContactDto,
} from '../types/policy.js';

export const ELIGIBILITY_CATEGORY_LABELS: Record<
  EligibilityCategory,
  string
> = {
  age: '연령',
  region: '지역',
  income: '소득',
  asset: '자산',
  employment: '취업',
  education: '학력',
  housing: '주거',
  household: '가구',
  other: '기타',
};

export const ELIGIBILITY_COVERAGE_LABELS: Record<
  EligibilityCoverage,
  string
> = {
  complete: '원문 기준 주요 조건 확인',
  partial: '일부 조건만 확인됨',
  unknown: '구조화된 조건 미확인',
};

export const ELIGIBILITY_COVERAGE_MESSAGES: Record<
  EligibilityCoverage,
  string
> = {
  complete:
    '공식 원문에서 확인한 주요 조건입니다. 최종 신청 전 최신 공고를 확인해 주세요.',
  partial:
    '공식 원문에서 확인 가능한 일부 조건만 정리했습니다. 누락된 조건이 있을 수 있습니다.',
  unknown:
    '구조화할 수 있는 조건을 확인하지 못했습니다. 신청 가능 여부는 공식 원문에서 확인해 주세요.',
};

export function getPublicHttpUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return (url.protocol === 'http:' || url.protocol === 'https:') &&
      !url.username &&
      !url.password
      ? url.toString()
      : null;
  } catch {
    return null;
  }
}

export function getInstitutionalContactHref(
  contact: InstitutionalContactDto,
): string | null {
  if (contact.kind === 'phone') {
    const digits = contact.value.replace(/\D/g, '');
    const prefix = contact.value.trim().startsWith('+') ? '+' : '';
    return digits ? `tel:${prefix}${digits}` : null;
  }

  return getPublicHttpUrl(contact.value);
}

export function getInstitutionalContactActionLabel(
  contact: InstitutionalContactDto,
): string {
  return contact.kind === 'phone' ? '전화 걸기' : '공식 채널 열기';
}
