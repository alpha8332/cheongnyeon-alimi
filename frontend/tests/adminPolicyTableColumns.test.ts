import assert from 'node:assert/strict';
import test from 'node:test';
import type { AdminPolicyListItemDto } from '../src/types/adminPolicyData.js';
import {
  DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS,
  formatAdminPolicyCellValue,
  isAdminPolicySortField,
  shouldExpandAdminPolicyCell,
  truncateAdminPolicyCell,
} from '../src/utils/adminPolicyTableColumns.js';

const SAMPLE_ITEM: AdminPolicyListItemDto = {
  id: 1,
  title: '청년 주거 지원',
  source_name: '복지로',
  organization: '행정안전부',
  categories: ['housing', 'welfare'],
  application_status: 'open',
  application_start: '2026-01-01',
  application_end: '2026-12-31',
  regions: ['서울', '경기'],
  data_quality_status: 'valid',
  collected_at: '2026-08-01T00:00:00Z',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-02T00:00:00Z',
  source_id: 'welfare',
  external_id: 'ext-001',
};

test('DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS는 기본 표시 컬럼만 포함한다', () => {
  assert.ok(DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS.includes('id'));
  assert.ok(DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS.includes('title'));
  assert.equal(DEFAULT_VISIBLE_ADMIN_POLICY_COLUMNS.includes('organization'), false);
});

test('isAdminPolicySortField는 sortable 컬럼만 true를 반환한다', () => {
  assert.equal(isAdminPolicySortField('id'), true);
  assert.equal(isAdminPolicySortField('title'), true);
  assert.equal(isAdminPolicySortField('source_name'), false);
});

test('formatAdminPolicyCellValue는 배열·null을 표시 문자열로 변환한다', () => {
  assert.equal(formatAdminPolicyCellValue(SAMPLE_ITEM, 'categories'), 'housing, welfare');
  assert.equal(formatAdminPolicyCellValue({ ...SAMPLE_ITEM, organization: null }, 'organization'), '—');
});

test('truncateAdminPolicyCell은 긴 문자열을 잘라낸다', () => {
  const longTitle = '가'.repeat(60);
  const truncated = truncateAdminPolicyCell(longTitle, 48);

  assert.equal(truncated.endsWith('…'), true);
  assert.equal(shouldExpandAdminPolicyCell(longTitle, 48), true);
  assert.equal(shouldExpandAdminPolicyCell('짧은 제목', 48), false);
});
