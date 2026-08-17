import type { PolicyDetailDto, PolicyDto } from '../types/policy.js';
import { isImminentDeadline } from './policyDeadline.js';
import {
  formatApplicationSchedule,
  formatApplicationStatus,
} from './policyDisplay.js';

export interface PolicyStatusBadge {
  label: string;
  variant: 'always' | 'open' | 'hot' | 'closed' | 'warn' | 'muted';
}

function stripHtmlTags(value: string): string {
  return value.replace(/<[^>]*>/g, '').trim();
}

export function sanitizePolicyText(value: string | null | undefined): string {
  if (!value) {
    return '';
  }

  return stripHtmlTags(value)
    .replace(/\u00a0/g, ' ')
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n[ \t]+/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
}

export function splitPolicyTextToBullets(value: string | null | undefined): string[] {
  return splitPolicyTextToItems(value).items;
}

/** `○`·`●` 구분자로 뭉친 요약 텍스트를 줄 단위로 분리 */
export function splitCircleBulletLines(value: string | null | undefined): string[] {
  const sanitized = sanitizePolicyText(value);
  if (!sanitized) {
    return [];
  }

  if (!/[○●◦]/u.test(sanitized)) {
    return [sanitized];
  }

  return sanitized
    .split(/\s*[○●◦]\s*/u)
    .map((line) => line.trim())
    .filter(Boolean);
}

export function splitPolicyTextToItems(value: string | null | undefined): {
  items: string[];
  ordered: boolean;
} {
  const sanitized = sanitizePolicyText(value);
  if (!sanitized) {
    return { items: [], ordered: false };
  }

  const lines = sanitized.split(/\n+/).map((line) => line.trim()).filter(Boolean);
  const numberedLines = lines.filter((line) => /^\d+[.)]\s/.test(line));

  if (numberedLines.length >= 2) {
    return {
      items: numberedLines.map((line) => line.replace(/^\d+[.)]\s*/, '').trim()),
      ordered: true,
    };
  }

  const bulletCandidates = lines
    .flatMap((line) => line.split(/(?<=[.;!?])\s+(?=[•\-–*])/u))
    .map((line) => line.replace(/^[\s•\-–*]+/u, '').trim())
    .filter(Boolean);

  if (bulletCandidates.length >= 2) {
    return { items: bulletCandidates, ordered: false };
  }

  const semicolonSplit = sanitized
    .split(/\s*;\s*|\s*\/\s*(?=\S)/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (semicolonSplit.length >= 2) {
    return { items: semicolonSplit, ordered: false };
  }

  return { items: bulletCandidates.length > 0 ? bulletCandidates : [sanitized], ordered: false };
}

export function getPolicyStatusBadge(policy: PolicyDto): PolicyStatusBadge {
  if (
    policy.application_schedule === 'always' &&
    policy.application_status === 'open'
  ) {
    return { label: '상시', variant: 'always' };
  }

  if (policy.data_quality_status === 'partial') {
    return { label: '정보 미확인', variant: 'warn' };
  }

  if (isImminentDeadline(policy)) {
    return { label: '마감임박', variant: 'hot' };
  }

  if (policy.application_status === 'open') {
    return { label: '모집중', variant: 'open' };
  }

  if (policy.application_status === 'scheduled') {
    return { label: '예정', variant: 'muted' };
  }

  if (policy.application_status === 'closed') {
    return { label: '마감', variant: 'closed' };
  }

  if (policy.application_status) {
    return {
      label: formatApplicationStatus(policy.application_status),
      variant: 'muted',
    };
  }

  if (policy.application_schedule === 'always') {
    return { label: '상시', variant: 'always' };
  }

  if (policy.application_schedule) {
    return {
      label: formatApplicationSchedule(policy.application_schedule),
      variant: 'muted',
    };
  }

  return { label: '정책', variant: 'muted' };
}

/** 상세 헤더: 신청 일정(`application_schedule`)과 접수 상태(`application_status`)를 분리 표시 */
export function getPolicyDetailStatusBadges(policy: PolicyDto): PolicyStatusBadge[] {
  const badges: PolicyStatusBadge[] = [];

  if (policy.application_schedule) {
    badges.push({
      label: formatApplicationSchedule(policy.application_schedule),
      variant: policy.application_schedule === 'always' ? 'always' : 'muted',
    });
  }

  if (policy.data_quality_status === 'partial') {
    badges.push({ label: '정보 미확인', variant: 'warn' });
  }

  if (isImminentDeadline(policy)) {
    badges.push({ label: '마감임박', variant: 'hot' });
  }

  if (policy.application_status === 'open') {
    badges.push({ label: formatApplicationStatus('open'), variant: 'open' });
  } else if (policy.application_status === 'scheduled') {
    badges.push({ label: formatApplicationStatus('scheduled'), variant: 'muted' });
  } else if (policy.application_status === 'closed') {
    badges.push({ label: formatApplicationStatus('closed'), variant: 'closed' });
  } else if (policy.application_status) {
    badges.push({
      label: formatApplicationStatus(policy.application_status),
      variant: 'muted',
    });
  }

  if (badges.length === 0) {
    return [getPolicyStatusBadge(policy)];
  }

  return badges;
}

export function formatPolicyIncomeSummary(policy: PolicyDetailDto): string {
  const incomeTexts =
    policy.eligibility_summary?.requirements
      ?.filter((item) => item.category === 'income')
      .map((item) => sanitizePolicyText(item.text))
      .filter(Boolean) ?? [];

  if (incomeTexts.length > 0) {
    return incomeTexts.join(' · ');
  }

  const eligibilityText = sanitizePolicyText(policy.eligibility_text);
  if (/소득|중위|기준\s*소득/u.test(eligibilityText)) {
    const incomeLine =
      eligibilityText
        .split(/\n+/)
        .find((line) => /소득|중위/u.test(line)) ?? eligibilityText;
    return incomeLine.slice(0, 160);
  }

  return '소득 기준 미확인';
}

export function formatPolicyEmploymentSummary(policy: PolicyDto): string {
  const parts: string[] = [];

  if (policy.employment_statuses.length > 0) {
    parts.push(policy.employment_statuses.join(', '));
  }

  if (policy.education_statuses.length > 0) {
    parts.push(policy.education_statuses.join(', '));
  }

  if (parts.length > 0) {
    return parts.join(' · ');
  }

  return '취업·학력 조건 미확인';
}

export function hasPolicyTextContent(value: string | null | undefined): boolean {
  return sanitizePolicyText(value).length > 0;
}
