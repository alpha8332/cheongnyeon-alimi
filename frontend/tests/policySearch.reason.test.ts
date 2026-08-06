import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildConditionAnalysisRows,
  buildUninterpretedNotices,
  resolvePolicySearchReasonMessage,
} from '../src/utils/policySearchReasonHelpers.js';

const interpretedM1 = {
  q_raw: '서울 주거',
  q_clean: '서울 주거',
  conditions: [
    {
      dimension: 'region' as const,
      value: '서울특별시',
      source: 'explicit' as const,
      resolution: 'resolved' as const,
      candidates: [],
    },
    {
      dimension: 'keyword' as const,
      value: '주거',
      source: 'q' as const,
      resolution: 'resolved' as const,
      candidates: [],
    },
  ],
  override_fields: ['region' as const],
  uninterpreted_terms: [],
};

const hitM1 = {
  policy: { id: 1, title: '온통청년 주거' },
  score: 0.91,
  verdicts: {
    region: 'match' as const,
    age: null,
    status: null,
    category: 'match' as const,
  },
  unknown_count: 0,
  reason_codes: ['REGION_MATCH', 'KEYWORD_MATCH'],
  message: '서울 지역 주거 조건과 일치하는 온통청년 정책입니다.',
  unconfirmed_conditions: [],
};

test('buildConditionAnalysisRows는 interpreted condition과 verdict를 결합한다', () => {
  const rows = buildConditionAnalysisRows(interpretedM1, hitM1 as never);

  assert.equal(rows.length, 2);
  assert.match(rows[0]?.label ?? '', /지역: 서울특별시 — 일치/);
  assert.match(rows[1]?.label ?? '', /키워드: 주거 — 텍스트 매칭/);
});

test('buildUninterpretedNotices는 미파싱 토큰 안내 문구를 생성한다', () => {
  const notices = buildUninterpretedNotices({
    ...interpretedM1,
    uninterpreted_terms: ['복지로', '지원금'],
  });

  assert.equal(notices.length, 2);
  assert.match(notices[0] ?? '', /복지로/);
  assert.match(notices[0] ?? '', /키워드 매칭만 적용/);
});

test('resolvePolicySearchReasonMessage는 message를 우선하고 unknown code도 fallback한다', () => {
  assert.equal(
    resolvePolicySearchReasonMessage(hitM1 as never),
    hitM1.message,
  );

  const fallback = resolvePolicySearchReasonMessage({
    ...hitM1,
    message: '',
    reason_codes: ['UNKNOWN_CUSTOM_CODE'],
  } as never);

  assert.equal(fallback, 'UNKNOWN_CUSTOM_CODE');
});

test('resolvePolicySearchReasonMessage는 알려진 reason code label을 사용한다', () => {
  const labeled = resolvePolicySearchReasonMessage({
    ...hitM1,
    message: '  ',
    reason_codes: ['REGION_MATCH'],
  } as never);

  assert.match(labeled ?? '', /지역 조건이 일치합니다/);
});
