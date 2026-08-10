import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import type {
  EligibilitySummaryDto,
  InstitutionalContactDto,
} from '../src/types/policy.js';
import {
  ELIGIBILITY_CATEGORY_LABELS,
  ELIGIBILITY_COVERAGE_LABELS,
  ELIGIBILITY_COVERAGE_MESSAGES,
  getInstitutionalContactActionLabel,
  getInstitutionalContactHref,
  getPublicHttpUrl,
} from '../src/utils/eligibilitySummary.js';

interface EligibilityHandoffItem {
  source_id: string;
  eligibility_summary: EligibilitySummaryDto;
}

interface EligibilityFixture {
  source_handoff: EligibilityHandoffItem[];
}

const fixturePath = resolve(
  process.cwd(),
  '..',
  'data',
  'fixtures',
  'contracts',
  'eligibility_evidence_cases.json',
);
const fixture = JSON.parse(
  readFileSync(fixturePath, 'utf8'),
) as EligibilityFixture;
const webSummary = fixture.source_handoff.find(
  (item) => item.source_id === 'cheonan-youthcenter-web',
)?.eligibility_summary;

test('승인 Eligibility 문구는 자격을 단정하지 않고 coverage를 구분한다', () => {
  assert.equal(ELIGIBILITY_COVERAGE_LABELS.partial, '일부 조건만 확인됨');
  assert.equal(
    ELIGIBILITY_COVERAGE_LABELS.unknown,
    '구조화된 조건 미확인',
  );
  assert.match(ELIGIBILITY_COVERAGE_MESSAGES.partial, /누락/);
  assert.match(ELIGIBILITY_COVERAGE_MESSAGES.unknown, /공식 원문/);
  assert.equal(ELIGIBILITY_CATEGORY_LABELS.household, '가구');
});

test('승인 웹 표본에 제외조건·서류·시설 문의처가 모두 존재한다', () => {
  assert.ok(webSummary);
  assert.ok(webSummary.exclusions.length > 0);
  assert.ok(webSummary.documents.length > 0);
  assert.ok(webSummary.institutional_contacts.length > 0);
  assert.ok(
    webSummary.institutional_contacts.every((contact) =>
      contact.evidence.every(
        (evidence) =>
          evidence.source_id === 'cheonan-youthcenter-web' &&
          evidence.locator_type === 'css_selector',
      ),
    ),
  );
});

test('시설 대표전화는 모바일 전화 링크로 만들고 개인 번호를 추정하지 않는다', () => {
  assert.ok(webSummary);
  const phone = webSummary.institutional_contacts.find(
    (contact) => contact.kind === 'phone',
  );
  assert.ok(phone);
  assert.match(getInstitutionalContactHref(phone) ?? '', /^tel:/);
  assert.equal(getInstitutionalContactActionLabel(phone), '전화 걸기');

  const invalidPhone: InstitutionalContactDto = {
    ...phone,
    value: '문의는 원문 확인',
  };
  assert.equal(getInstitutionalContactHref(invalidPhone), null);
});

test('공식 채널은 HTTP(S) 주소일 때만 새 링크로 제공한다', () => {
  assert.ok(webSummary);
  const channel = webSummary.institutional_contacts.find(
    (contact) => contact.kind === 'official_channel',
  );
  assert.ok(channel);
  assert.equal(getInstitutionalContactHref(channel), null);

  const linkedChannel: InstitutionalContactDto = {
    ...channel,
    value: 'https://example.org/contact',
  };
  assert.equal(
    getInstitutionalContactHref(linkedChannel),
    'https://example.org/contact',
  );
  assert.equal(
    getInstitutionalContactActionLabel(linkedChannel),
    '공식 채널 열기',
  );
  assert.equal(getPublicHttpUrl('javascript:alert(1)'), null);
  assert.equal(getPublicHttpUrl('https://user@example.org/contact'), null);
});
