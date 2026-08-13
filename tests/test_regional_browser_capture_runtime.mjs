import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

import {
  buildRegisteredTitleDeadlineDetail,
  buildDetail,
  chungbukConfig,
  daejeonConfig,
  gangwonConfig,
  jejuConfig,
  ulsanConfig,
} from "../scripts/regional-browser-capture-runtime.mjs";

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
const chungbukFixture = JSON.parse(await readFile(
  new URL("./fixtures/regional/chungbuk_detail_440062.json", import.meta.url),
  "utf8",
));
const ulsanFixture = JSON.parse(await readFile(
  new URL("./fixtures/regional/ulsan_detail_60156.json", import.meta.url),
  "utf8",
));
const daejeonFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/daejeon_detail_CT_000000000541.json",
    import.meta.url,
  ),
  "utf8",
));
const gangwonFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/gangwon_detail_A2026021200300200900000001.json",
    import.meta.url,
  ),
  "utf8",
));
const gangwonFailureFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/gangwon_detail_failure_page_context.json",
    import.meta.url,
  ),
  "utf8",
));
const jejuFailureFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/jeju_detail_failure_unstructured_deadline.json",
    import.meta.url,
  ),
  "utf8",
));
const seoulEmptyPeriodFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/seoul_detail_20260415005400212748_empty_period.json",
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

test("Chungbuk numbered prose preserves application period evidence", () => {
  const detail = buildDetail(
    chungbukFixture.expected_title,
    chungbukFixture.extracted,
  );

  assert.equal(
    detail.application_period,
    "2026.07.24.(금) - 2026.08.13.(목)",
  );
  assert.match(detail.eligibility, /충청북도내 미취업상태/);
  assert.equal(
    detail.evidence_observations.application_period.status,
    "value_extracted",
  );
});

test("Ulsan maps the official reception schedule label", () => {
  const detail = buildDetail(
    ulsanFixture.expected_title,
    ulsanFixture.extracted,
  );

  assert.equal(detail.application_period, "2026-08-10 ~ 2026-08-14");
  assert.equal(
    detail.evidence_observations.application_period.label,
    "접수일정",
  );
});

test("Daejeon combines the reception period and per-event deadline", () => {
  const detail = buildDetail(
    daejeonFixture.expected_title,
    daejeonFixture.extracted,
  );

  assert.equal(
    detail.application_period,
    "2026. 3. ~ 2026. 12. 각 회차별 참가 신청은 행사일 기준 7일 전까지 가능",
  );
  assert.match(detail.eligibility, /대전광역시 거주/);
});

test("Gangwon maps class-table regional and application fields", () => {
  const detail = buildDetail(
    gangwonFixture.expected_title,
    gangwonFixture.extracted,
  );

  assert.equal(detail.application_period, "2026.6.1. ~ 2026.8.31.");
  assert.match(detail.eligibility, /도내 주민등록자/);
  assert.match(detail.eligibility, /연소득 8천만 원 이하/);
  assert.equal(detail.organization, "강원특별자치도 건축과");
});

test("Gangwon failure pages preserve the official POST page context", () => {
  assert.equal(gangwonFailureFixture.affected_count, 325);
  for (const representative of gangwonFailureFixture.representatives) {
    const config = gangwonConfig(representative.page);
    assert.equal(config.listPageLinkNavigation, true);
    assert.match(config.detailClickTemplate, /data-id/);
  }
  assert.throws(() => gangwonConfig(30), /observed 1\.\.29 range/);
});

test("Jeju recovers dated closed posts without structured field rows", () => {
  for (const fixtureCase of jejuFailureFixture.cases) {
    const detail = buildRegisteredTitleDeadlineDetail(
      fixtureCase.title,
      {
        actualTitle: fixtureCase.title,
        body: fixtureCase.title.replace(/\s/g, ""),
        pairs: {},
        contentBlocks: [fixtureCase.content_text],
        metadataText: fixtureCase.metadata_text,
      },
      "2026-08-13",
    );
    assert.equal(
      detail.application_period,
      fixtureCase.expected_application_period,
    );
    assert.deepEqual(detail.evidence_observations.application_period, {
      label: "제목 기한 + 등록일",
      status: "value_extracted",
    });
  }
  assert.equal(
    jejuConfig(1, "2026-08-13").detailTitleSelector,
    ".view_title",
  );
  assert.equal(
    jejuConfig(1, "2026-08-13").detailContentSelector,
    "#writeContents",
  );
  assert.throws(() => jejuConfig(1), /requires an as-of date/);
});

test("Seoul distinguishes an empty official period from a missing label", () => {
  const detail = buildDetail(
    seoulEmptyPeriodFixture.expected_title,
    seoulEmptyPeriodFixture.extracted,
  );

  assert.equal(detail.application_period, null);
  assert.equal(
    detail.evidence_observations.application_period.status,
    "label_present_value_empty",
  );
});

test("remaining RYP8 Source configs pin the observed list and detail selectors", () => {
  assert.equal(chungbukConfig(1).detailContentSelector, ".p-table__content");
  assert.match(ulsanConfig(1).linkSelector, /dataId/);
  assert.match(daejeonConfig(1).identityPattern, /CT_/);
  assert.deepEqual(
    {
      row: gangwonConfig(1).detailPairRowSelector,
      label: gangwonConfig(1).detailPairLabelSelector,
      value: gangwonConfig(1).detailPairValueSelector,
    },
    {
      row: ".skinTb-tr",
      label: ".skinTb-th",
      value: ".skinTb-td",
    },
  );
  assert.equal(gangwonConfig(2).listPageLinkNavigation, true);
});
