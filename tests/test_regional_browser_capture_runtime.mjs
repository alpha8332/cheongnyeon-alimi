import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

import {buildDetail} from "../scripts/regional-browser-capture-runtime.mjs";

const fixtureUrl = new URL(
  "./fixtures/regional/daegu_detail_6104.json",
  import.meta.url,
);
const fixture = JSON.parse(await readFile(fixtureUrl, "utf8"));
const gwangjuFixture = JSON.parse(await readFile(
  new URL("./fixtures/regional/gwangju_detail_1248.json", import.meta.url),
  "utf8",
));
const incheonFixture = JSON.parse(await readFile(
  new URL("./fixtures/regional/incheon_detail_110.json", import.meta.url),
  "utf8",
));
const jeonbukFixture = JSON.parse(await readFile(
  new URL("./fixtures/regional/jeonbuk_detail_129.json", import.meta.url),
  "utf8",
));
const seoulFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/seoul_detail_20250224005400210564.json",
    import.meta.url,
  ),
  "utf8",
));

test("Daegu prose labels preserve multi-paragraph field evidence", () => {
  const detail = buildDetail(fixture.expected_title, fixture.extracted);

  assert.equal(detail.organization, "대구광역시 중구");
  assert.equal(detail.contact, "053-661-2183");
  assert.match(detail.eligibility, /대구광역시 중구로 전입/);
  assert.match(detail.eligibility, /중위소득 150% 이하/);
  assert.equal(
    detail.support_content,
    "최대 30만원 내에서 중개수수료 및 이사비용 실비 지원(생애 1회)",
  );
  assert.equal(
    detail.evidence_observations.eligibility.status,
    "value_extracted",
  );
  assert.equal(
    detail.evidence_observations.eligibility.label,
    "지원대상",
  );
  assert.equal(
    detail.evidence_observations.support_content.status,
    "value_extracted",
  );
});

test("Gwangju detail aliases preserve eligibility and application method", () => {
  const detail = buildDetail(
    gwangjuFixture.expected_title,
    gwangjuFixture.extracted,
  );

  assert.match(detail.eligibility, /남구 거주/);
  assert.match(detail.application_method, /방문 또는 이메일 신청/);
  assert.doesNotMatch(detail.application_method, /신청대상/);
  assert.equal(
    detail.evidence_observations.eligibility.label,
    "참여요건",
  );
  assert.equal(
    detail.evidence_observations.application_method.label,
    "신청절차",
  );
});

test("Incheon prefers support content and combines regional eligibility", () => {
  const detail = buildDetail(
    incheonFixture.expected_title,
    incheonFixture.extracted,
  );

  assert.equal(
    detail.support_content,
    "맞춤형 프로그램 및 참여수당, 인센티브 등",
  );
  assert.match(detail.eligibility, /구직단념 청년/);
  assert.match(detail.eligibility, /부평구 거주자/);
  assert.equal(
    detail.contact,
    "사회적협동조합 일터와사람들 070-4148-5325",
  );
});

test("Jeonbuk detail aliases preserve region and official application URL", () => {
  const detail = buildDetail(
    jeonbukFixture.expected_title,
    jeonbukFixture.extracted,
  );

  assert.equal(detail.source_region, "전북특별자치도");
  assert.equal(detail.organization, "베스트인");
  assert.equal(detail.age, "만15 ~ 69세");
  assert.equal(
    detail.application_method,
    "https://docs.google.com/forms/example",
  );
  assert.equal(
    detail.evidence_observations.support_content.status,
    "label_not_found",
  );
  assert.equal(
    detail.evidence_observations.required_documents.status,
    "label_present_value_empty",
  );
});

test("Seoul prefers support content and resident condition over scale", () => {
  const detail = buildDetail(
    seoulFixture.expected_title,
    seoulFixture.extracted,
  );

  assert.equal(
    detail.support_content,
    "자격시험 준비비, 면접 준비비, 문화힐링비 지원",
  );
  assert.equal(
    detail.application_period,
    "2025년 3월 5일 ~ 2025년 11월 30일",
  );
  assert.match(detail.eligibility, /금천구에 계속 거주/);
  assert.equal(detail.organization, "금천구");
  assert.equal(detail.exclusions, "신청항목별 상이");
});
