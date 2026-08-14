import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

import {
  buildGangwonCanaryPlan,
  buildGyeongnamApiDetail,
  buildRegisteredTitleDeadlineDetail,
  buildDetail,
  chungbukConfig,
  daejeonConfig,
  daejeonCheckpointDetailConfig,
  gangwonConfig,
  gotoWithReadyFallback,
  gwangjuConfig,
  gwangjuCheckpointDetailConfig,
  incheonCheckpointDetailConfig,
  jeonbukCheckpointDetailConfig,
  jejuConfig,
  jejuCheckpointDetailConfig,
  normalizeCheckpointDetailTitle,
  classifyDetailCanaryObservation,
  seoulConfig,
  ulsanConfig,
  waitForReadySelector,
  waitForExpectedTitle,
  withSingleDetailRetry,
  validateCheckpointDetailRecaptureContracts,
  validateRecaptureExclusions,
} from "../scripts/regional-browser-capture-runtime.mjs";

test("navigation timeout continues only when the target DOM already loaded", async () => {
  const target = "https://regional.example.test/detail?id=149186&page=33";
  const tab = {
    goto: async () => {
      throw new Error("Page.navigate timeout");
    },
    playwright: {
      evaluate: async (callback, input) => {
        globalThis.location = {href: target};
        globalThis.document = {
          querySelector: (selector) => selector === ".detail-ready" ? {} : null,
        };
        try {
          return callback(input);
        } finally {
          delete globalThis.location;
          delete globalThis.document;
        }
      },
    },
  };

  assert.equal(
    await gotoWithReadyFallback(tab, target, ".detail-ready"),
    true,
  );
});

test("navigation timeout remains a failure when target DOM is absent", async () => {
  const timeout = new Error("Page.navigate timeout");
  const tab = {
    goto: async () => {
      throw timeout;
    },
    playwright: {
      evaluate: async () => false,
    },
  };

  await assert.rejects(
    gotoWithReadyFallback(
      tab,
      "https://regional.example.test/detail?id=missing",
      ".detail-ready",
    ),
    (error) => error === timeout,
  );
});

test("navigation fallback requires the complete target query", async () => {
  const timeout = new Error("Page.navigate timeout");
  const target = "https://regional.example.test/detail?id=149186&page=33";
  const tab = {
    goto: async () => {
      throw timeout;
    },
    playwright: {
      evaluate: async (callback, input) => {
        globalThis.location = {href: `${target}&unexpected=1`};
        globalThis.document = {querySelector: () => ({})};
        try {
          return callback(input);
        } finally {
          delete globalThis.location;
          delete globalThis.document;
        }
      },
    },
  };

  await assert.rejects(
    gotoWithReadyFallback(tab, target, ".detail-ready"),
    (error) => error === timeout,
  );
});

test("navigation fallback never absorbs a non-timeout error", async () => {
  const failure = new Error("navigation target rejected");
  const tab = {
    goto: async () => {
      throw failure;
    },
  };

  await assert.rejects(
    gotoWithReadyFallback(
      tab,
      "https://regional.example.test/detail?id=rejected",
      ".detail-ready",
    ),
    (error) => error === failure,
  );
});

test("ready selector returns immediately when the DOM exists", async () => {
  let checks = 0;
  const tab = {
    playwright: {
      evaluate: async (_callback, selector) => {
        checks += 1;
        return selector === ".ready";
      },
    },
  };

  assert.equal(await waitForReadySelector(tab, ".ready"), true);
  assert.equal(checks, 1);
});

test("ready selector polling observes delayed DOM insertion", async () => {
  let checks = 0;
  const tab = {
    playwright: {
      evaluate: async () => {
        checks += 1;
        return checks > 1;
      },
    },
  };

  assert.equal(await waitForReadySelector(tab, ".ready"), true);
  assert.equal(checks, 2);
});

test("missing ready selector reaches an explicit timeout", async () => {
  const tab = {
    playwright: {evaluate: async () => false},
  };

  await assert.rejects(
    waitForReadySelector(tab, ".missing", 1),
    /ready selector timeout after 1ms: \.missing/,
  );
});

test("ready selector polling never absorbs a DOM evaluation failure", async () => {
  const failure = new Error("DOM evaluation failed");
  const tab = {
    playwright: {evaluate: async () => { throw failure; }},
  };

  await assert.rejects(
    waitForReadySelector(tab, ".ready"),
    (error) => error === failure,
  );
});

test("detail title polling waits for navigation to replace stale DOM", async () => {
  const titles = ["이전 상세 제목", "새 상세 제목", "새 상세 제목"];
  const tab = {
    playwright: {
      evaluate: async () => ({
        title: titles.shift() ?? "새 상세 제목",
        content: null,
      }),
    },
  };

  assert.equal(
    await waitForExpectedTitle(tab, ".title_here", "새 상세 제목"),
    "새 상세 제목",
  );
});

test("detail title polling rejects an unchanged stale DOM", async () => {
  const tab = {
    playwright: {
      evaluate: async () => ({title: "이전 상세 제목", content: null}),
    },
  };

  await assert.rejects(
    waitForExpectedTitle(tab, ".title_here", "새 상세 제목", 1),
    /detail title timeout after 1ms/,
  );
});

test("detail polling waits for content after the title changes", async () => {
  const contents = [
    "이전 상세 본문",
    "새 상세 제목 새 상세 본문",
    "새 상세 제목 새 상세 본문",
  ];
  const tab = {
    playwright: {
      evaluate: async () => ({
        title: "새 상세 제목",
        content: contents.shift() ?? "새 상세 제목 새 상세 본문",
      }),
    },
  };

  assert.equal(
    await waitForExpectedTitle(
      tab,
      ".title_here",
      "새 상세 제목",
      20000,
      "#board_normal_view",
    ),
    "새 상세 제목",
  );
});

test("detail polling resets stability when matching DOM changes back", async () => {
  const contents = [
    "새 상세 제목 새 상세 본문",
    "이전 상세 본문",
    "새 상세 제목 새 상세 본문",
    "새 상세 제목 새 상세 본문",
  ];
  const tab = {
    playwright: {
      evaluate: async () => ({
        title: "새 상세 제목",
        content: contents.shift() ?? "새 상세 제목 새 상세 본문",
      }),
    },
  };

  assert.equal(
    await waitForExpectedTitle(
      tab,
      ".title_here",
      "새 상세 제목",
      20000,
      "#board_normal_view",
    ),
    "새 상세 제목",
  );
});

test("detail retry repeats one transient title mismatch", async () => {
  let attempts = 0;
  const result = await withSingleDetailRetry(async () => {
    attempts += 1;
    if (attempts === 1) throw new Error("detail title does not match list");
    return "stable detail";
  }, true);

  assert.equal(result, "stable detail");
  assert.equal(attempts, 2);
});

test("detail retry preserves non-title failures", async () => {
  let attempts = 0;
  await assert.rejects(
    withSingleDetailRetry(async () => {
      attempts += 1;
      throw new Error("detail access denied");
    }, true),
    /detail access denied/,
  );
  assert.equal(attempts, 1);
});

test("recapture exclusions are explicit and disjoint from selected identities", () => {
  assert.deepEqual(
    validateRecaptureExclusions(true, ["checkpoint-id"], ["current-only-id"]),
    ["current-only-id"],
  );
  assert.throws(
    () => validateRecaptureExclusions(
      true,
      ["checkpoint-id"],
      ["checkpoint-id"],
    ),
    /recapture excluded identities are invalid/,
  );
  assert.throws(
    () => validateRecaptureExclusions(false, null, ["current-only-id"]),
    /recapture excluded identities are invalid/,
  );
});

const fixtureUrl = new URL(
  "./fixtures/regional/daegu_detail_6104.json",
  import.meta.url,
);
const fixture = JSON.parse(await readFile(fixtureUrl, "utf8"));
const daeguCheckpointDetailFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/daegu_checkpoint_detail_recapture.json",
    import.meta.url,
  ),
  "utf8",
));
const gwangjuCheckpointDetailFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/gwangju_checkpoint_detail_recapture.json",
    import.meta.url,
  ),
  "utf8",
));
const incheonCheckpointDetailFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/incheon_checkpoint_detail_recapture.json",
    import.meta.url,
  ),
  "utf8",
));
const jeonbukCheckpointDetailFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/jeonbuk_checkpoint_detail_recapture.json",
    import.meta.url,
  ),
  "utf8",
));
const gyeongnamApiFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/gyeongnam_api_detail_2225.json",
    import.meta.url,
  ),
  "utf8",
));
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
const chungbukSubmissionDeadlineFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/chungbuk_detail_440288_submission_deadline.json",
    import.meta.url,
  ),
  "utf8",
));
const ulsanFixture = JSON.parse(await readFile(
  new URL("./fixtures/regional/ulsan_detail_60156.json", import.meta.url),
  "utf8",
));
const ulsanClosedFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/ulsan_detail_46930_closed_status.json",
    import.meta.url,
  ),
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

test("Daegu checkpoint detail recapture accepts a frozen Raw identity contract", () => {
  assert.deepEqual(
    validateCheckpointDetailRecaptureContracts(
      daeguCheckpointDetailFixture.source_id,
      daeguCheckpointDetailFixture.list_url,
      daeguCheckpointDetailFixture.items,
    ),
    daeguCheckpointDetailFixture.items,
  );
});

test("Daegu checkpoint detail recapture rejects a detail URL identity drift", () => {
  const drifted = structuredClone(daeguCheckpointDetailFixture.items);
  drifted[0].detail_url = drifted[0].detail_url.replace("6104", "6105");
  assert.throws(
    () => validateCheckpointDetailRecaptureContracts(
      daeguCheckpointDetailFixture.source_id,
      daeguCheckpointDetailFixture.list_url,
      drifted,
    ),
    /checkpoint detail recapture contract is invalid/,
  );
});

test("Gwangju checkpoint detail recapture accepts a frozen Raw identity contract", () => {
  assert.deepEqual(
    validateCheckpointDetailRecaptureContracts(
      gwangjuCheckpointDetailFixture.source_id,
      gwangjuCheckpointDetailFixture.list_url,
      gwangjuCheckpointDetailFixture.items,
    ),
    gwangjuCheckpointDetailFixture.items,
  );
});

test("Gwangju checkpoint detail recapture rejects a detail URL identity drift", () => {
  const drifted = structuredClone(gwangjuCheckpointDetailFixture.items);
  drifted[0].detail_url = drifted[0].detail_url.replace("1419", "1420");
  assert.throws(
    () => validateCheckpointDetailRecaptureContracts(
      gwangjuCheckpointDetailFixture.source_id,
      gwangjuCheckpointDetailFixture.list_url,
      drifted,
    ),
    /checkpoint detail recapture contract is invalid/,
  );
});

test("Incheon checkpoint detail recapture accepts its frozen identity contract", () => {
  assert.deepEqual(
    validateCheckpointDetailRecaptureContracts(
      incheonCheckpointDetailFixture.source_id,
      incheonCheckpointDetailFixture.list_url,
      incheonCheckpointDetailFixture.items,
    ),
    incheonCheckpointDetailFixture.items,
  );
  assert.ok(
    normalizeCheckpointDetailTitle(
      incheonCheckpointDetailFixture.observed_title,
      incheonCheckpointDetailFixture.items[0].title,
    ).startsWith(incheonCheckpointDetailFixture.items[0].title),
  );
});

test("Incheon checkpoint detail recapture rejects a poly_seq drift", () => {
  const drifted = structuredClone(incheonCheckpointDetailFixture.items);
  drifted[0].detail_url = drifted[0].detail_url.replace("420", "421");
  assert.throws(
    () => validateCheckpointDetailRecaptureContracts(
      incheonCheckpointDetailFixture.source_id,
      incheonCheckpointDetailFixture.list_url,
      drifted,
    ),
    /checkpoint detail recapture contract is invalid/,
  );
});

test("Jeonbuk checkpoint detail recapture accepts its frozen identity contract", () => {
  assert.deepEqual(
    validateCheckpointDetailRecaptureContracts(
      jeonbukCheckpointDetailFixture.source_id,
      jeonbukCheckpointDetailFixture.list_url,
      jeonbukCheckpointDetailFixture.items,
    ),
    jeonbukCheckpointDetailFixture.items,
  );
});

test("Jeonbuk checkpoint detail recapture rejects an id drift", () => {
  const drifted = structuredClone(jeonbukCheckpointDetailFixture.items);
  drifted[0].detail_url = drifted[0].detail_url.replace("485", "486");
  assert.throws(
    () => validateCheckpointDetailRecaptureContracts(
      jeonbukCheckpointDetailFixture.source_id,
      jeonbukCheckpointDetailFixture.list_url,
      drifted,
    ),
    /checkpoint detail recapture contract is invalid/,
  );
});

test("Jeju checkpoint detail recapture pins bo_table and wr_id", () => {
  const items = [{
    external_id: "1196",
    title: "제주형 청년기본소득 토론장 참여 청년 모집",
    detail_url: "https://jejuyouth.com/m/bbs/board.php?bo_table=1_2_2_1&wr_id=1196",
  }];
  assert.deepEqual(
    validateCheckpointDetailRecaptureContracts(
      "regional-jeju-youth-platform",
      "https://jejuyouth.com/m/bbs/board.php?bo_table=1_2_2_1&page=1",
      items,
    ),
    items,
  );
  const drifted = structuredClone(items);
  drifted[0].detail_url = drifted[0].detail_url.replace("1196", "1195");
  assert.throws(
    () => validateCheckpointDetailRecaptureContracts(
      "regional-jeju-youth-platform",
      "https://jejuyouth.com/m/bbs/board.php?bo_table=1_2_2_1&page=1",
      drifted,
    ),
    /checkpoint detail recapture contract is invalid/,
  );
});

test("Gyeongnam API detail maps official fields and explicit label absence", () => {
  assert.deepEqual(
    validateCheckpointDetailRecaptureContracts(
      gyeongnamApiFixture.source_id,
      gyeongnamApiFixture.list_url,
      gyeongnamApiFixture.items,
    ),
    gyeongnamApiFixture.items,
  );
  const detail = buildGyeongnamApiDetail(gyeongnamApiFixture.result);
  assert.equal(detail.title, gyeongnamApiFixture.items[0].title);
  assert.equal(detail.application_period, "2026-07-27 ~ 2026-08-16");
  assert.equal(detail.eligibility, gyeongnamApiFixture.result.policy_target_content);
  assert.equal(
    detail.evidence_observations.source_region.status,
    "label_not_found",
  );
  assert.equal(
    detail.evidence_observations.application_method.status,
    "value_extracted",
  );
  assert.equal(
    buildGyeongnamApiDetail({policy_title: "나도 &quot;혼자&quot; 산다"}).title,
    '나도 "혼자" 산다',
  );
  assert.equal(
    buildGyeongnamApiDetail({policy_title: "A&middot;B"}).title,
    "A·B",
  );
});

test("Daegu checkpoint detail recapture removes repeated category prefixes", () => {
  assert.equal(
    normalizeCheckpointDetailTitle(
      daeguCheckpointDetailFixture.repeated_category_title.observed,
      daeguCheckpointDetailFixture.repeated_category_title.expected,
      "^\\[\\s*[^\\]]+\\]\\s*",
    ),
    daeguCheckpointDetailFixture.repeated_category_title.expected,
  );
});

test("Daegu checkpoint detail recapture preserves a bracketed policy title", () => {
  assert.equal(
    normalizeCheckpointDetailTitle(
      daeguCheckpointDetailFixture.bracketed_policy_title.observed,
      daeguCheckpointDetailFixture.bracketed_policy_title.expected,
      "^\\[\\s*[^\\]]+\\]\\s*",
    ),
    daeguCheckpointDetailFixture.bracketed_policy_title.expected,
  );
});
const gangwonCanaryFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/gangwon_detail_canary_signatures.json",
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
const seoulIdentityFixture = JSON.parse(await readFile(
  new URL(
    "./fixtures/regional/seoul_list_identity_contract.json",
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

test("Gwangju config captures the policy-level region badge", () => {
  assert.equal(
    gwangjuConfig(1).detailRegionSelector,
    ".detail-policy .detail-into-top .tag .badge.type07",
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

test("Chungbuk uses the submission deadline instead of the training period", () => {
  const detail = buildDetail(
    chungbukSubmissionDeadlineFixture.expected_title,
    chungbukSubmissionDeadlineFixture.extracted,
  );

  assert.equal(detail.application_period, "2026.07.28.(화)");
  assert.equal(
    detail.evidence_observations.application_period.label,
    "제출기한",
  );
});

test("Chungbuk bounded operation period overrides a stale always-open label", () => {
  const title = "2022년 청년도전지원사업 참가자 모집 안내";
  const detail = buildDetail(title, {
    body: title.replace(/\s/g, ""),
    pairs: {},
    contentBlocks: [
      "1. 모집기간 : 상시모집",
      "4. 운영기간 : 2022.05.02.(월)-10.31.(월)",
    ],
  });

  assert.equal(
    detail.application_period,
    "운영기간: 2022.05.02.(월)-10.31.(월)",
  );
  assert.equal(
    detail.evidence_observations.application_period.label,
    "모집기간 + 운영기간",
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

test("Ulsan removes the bare closed badge from historical list titles", () => {
  const pattern = new RegExp(ulsanConfig(30).titlePrefixPattern);
  const normalizedTitle = ulsanClosedFixture.list_title.replace(pattern, "");
  const detail = buildDetail(normalizedTitle, ulsanClosedFixture.extracted);

  assert.equal(normalizedTitle, ulsanClosedFixture.expected_title);
  assert.equal(
    detail.application_period,
    "상시모집(선착순 마감) 2025-02-06 ~ 2025-08-31",
  );
  assert.equal(
    ulsanClosedFixture.scheduled_list_title.replace(pattern, ""),
    ulsanClosedFixture.scheduled_expected_title,
  );
  assert.equal(
    ulsanClosedFixture.no_schedule_list_title.replace(pattern, ""),
    ulsanClosedFixture.no_schedule_expected_title,
  );
});

test("Ulsan pins the official detail title and content roots", () => {
  const config = ulsanConfig(1);
  assert.equal(config.detailTitleSelector, ".title_here");
  assert.equal(config.detailContentSelector, "#board_normal_view");
  assert.equal(config.detailReadySelector, ".title_here");
  assert.equal(config.detailFromListContext, true);
  assert.equal(config.detailRetryOnMismatch, true);
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

test("Gangwon canaries rotate one failed identity through each page stratum", () => {
  const discoveredIds = Array.from(
    {length: 337},
    (_, index) => `A${String(index).padStart(24, "0")}`,
  );
  const decisions = discoveredIds.map((externalId, index) => ({
    external_id: externalId,
    outcome: index < 12 ? "review" : "failed",
  }));
  decisions[12].outcome = "review";
  decisions[14 * 12].outcome = "closed";
  decisions[336].outcome = "review";
  const plan = buildGangwonCanaryPlan({
    source_id: "regional-gangwon-youth-platform",
    discovered_ids: discoveredIds,
    decisions,
  });

  assert.equal(plan.failed_count, 322);
  assert.deepEqual(
    plan.canaries.map(({stratum, page}) => ({stratum, page})),
    [
      {stratum: "early", page: 2},
      {stratum: "middle", page: 11},
      {stratum: "late", page: 21},
    ],
  );
});

test("Gangwon canary signatures keep unfamiliar failures out of healthy", () => {
  for (const observation of gangwonCanaryFixture.observations) {
    assert.equal(
      classifyDetailCanaryObservation(observation),
      observation.expected,
    );
  }
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
  assert.equal(
    jejuCheckpointDetailConfig("2026-08-14").sourceScopeSelectors.jurisdiction_text,
    ".view_title",
  );
  assert.equal(
    jejuCheckpointDetailConfig("2026-08-14").sourceScopeSelectors.application_scope_text,
    ".mb_area",
  );
  assert.equal(
    gwangjuCheckpointDetailConfig().detailContentSelector,
    ".detail-policy",
  );
  assert.equal(incheonCheckpointDetailConfig().detailContentSelector, "#contents");
  assert.equal(
    incheonCheckpointDetailConfig().sourceScopeSelectors.application_scope_text,
    "#contents",
  );
  assert.equal(jeonbukCheckpointDetailConfig().detailContentSelector, ".board_view");
  assert.equal(chungbukConfig(1).detailContentSelector, ".p-table__content");
  assert.match(ulsanConfig(1).linkSelector, /dataId/);
  assert.match(daejeonConfig(1).identityPattern, /CT_/);
  assert.equal(daejeonCheckpointDetailConfig().detailTitleSelector, "h3");
  assert.equal(daejeonCheckpointDetailConfig().detailContentSelector, "#txt");
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

test("Seoul maps the 18 city and 5 district pages into one checkpoint order", () => {
  const cityFirst = seoulConfig(1);
  const cityLast = seoulConfig(seoulIdentityFixture.city_pages);
  const districtFirst = seoulConfig(seoulIdentityFixture.city_pages + 1);
  const districtLast = seoulConfig(seoulIdentityFixture.total_pages);

  assert.match(cityFirst.listUrl, /\/ctList\.do/);
  assert.match(cityFirst.listUrl, /key=2309150002/);
  assert.match(cityFirst.listUrl, /tabKind=002/);
  assert.equal(cityFirst.paginationValue, 1);
  assert.equal(cityLast.paginationValue, 18);
  assert.match(districtFirst.listUrl, /\/guList\.do/);
  assert.match(districtFirst.listUrl, /tabKind=003/);
  assert.equal(districtFirst.paginationValue, 1);
  assert.equal(districtLast.paginationValue, 5);
  assert.equal(districtLast.page, 23);
  assert.equal(cityFirst.detailTitleSelector, ".policy-detail strong.title");
  assert.equal(cityFirst.detailReadySelector, ".policy-detail .form-table");
  assert.match(cityFirst.identityPattern, /goView/);
  assert.throws(() => seoulConfig(0), /observed 1\.\.23 range/);
  assert.throws(() => seoulConfig(24), /observed 1\.\.23 range/);
});

test("Seoul identity audit fixture records a resolved replacement drift", () => {
  assert.equal(seoulIdentityFixture.total_count, 110);
  assert.equal(seoulIdentityFixture.city_count, 89);
  assert.equal(seoulIdentityFixture.district_count, 21);
  assert.equal(seoulIdentityFixture.added_ids.length, 0);
  assert.equal(seoulIdentityFixture.missing_ids.length, 0);
  assert.equal(seoulIdentityFixture.common_order_diff, 0);
});
