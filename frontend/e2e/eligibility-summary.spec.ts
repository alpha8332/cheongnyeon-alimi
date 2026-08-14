import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect, test } from '@playwright/test';
import type { EligibilitySummaryDto } from '../src/types/policy';

interface ContractFixture {
  cases: Array<{
    case_id: string;
    summary: EligibilitySummaryDto;
  }>;
  source_handoff: Array<{
    source_id: string;
    external_id: string;
    title: string;
    eligibility_summary: EligibilitySummaryDto;
  }>;
}

const repositoryRoot = resolve(process.cwd(), '..');
const programs = JSON.parse(
  readFileSync(
    resolve(repositoryRoot, 'data/seeds/initial_programs.json'),
    'utf8',
  ),
) as Array<Record<string, unknown>>;
const contract = JSON.parse(
  readFileSync(
    resolve(
      repositoryRoot,
      'data/fixtures/contracts/eligibility_evidence_cases.json',
    ),
    'utf8',
  ),
) as ContractFixture;
const webHandoff = contract.source_handoff.find(
  (item) => item.source_id === 'cheonan-youthcenter-web',
);

function publicSeedFields(): Record<string, unknown> {
  const internalFields = new Set([
    'provenance',
    'keywords',
    'life_stages',
    'target_groups',
    'coverage_scope',
    'region_rules',
    'eligibility_summary',
  ]);
  return Object.fromEntries(
    Object.entries(programs[0] ?? {}).filter(
      ([field]) => !internalFields.has(field),
    ),
  );
}

function detailResponse(
  policyId: number,
  summary: EligibilitySummaryDto,
): Record<string, unknown> {
  return {
    ...publicSeedFields(),
    id: policyId,
    source_id: 'eligibility-contract-fixture',
    external_id: `eligibility-${policyId}`,
    title: 'Eligibility Summary 브라우저 검증 정책',
    source_name: 'Eligibility 계약 Fixture',
    source_url: 'https://fixture.invalid/eligibility/detail',
    data_quality_status: 'partial',
    eligibility_summary: summary,
    created_at: '2026-08-10T00:00:00Z',
    updated_at: '2026-08-10T00:00:00Z',
  };
}

test('ES3 제외조건·필요서류·시설 문의처를 상세 화면에서 접근 가능하게 제공한다', async ({
  page,
}) => {
  test.skip(
    process.env.VITE_USE_MOCK !== 'false',
    '계약 응답을 HTTP로 주입하는 ES3 Browser 검증에서만 실행합니다.',
  );
  expect(webHandoff).toBeTruthy();

  const response = {
    ...detailResponse(674, webHandoff!.eligibility_summary),
    source_id: webHandoff!.source_id,
    external_id: webHandoff!.external_id,
    title: webHandoff!.title,
    source_name: '천안청년센터',
    source_url:
      'https://www.ch2030youth.kr/bbs/board.php?bo_table=notice&wr_id=674',
  };

  await page.route('**/api/v1/policies/674**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });

  await page.goto('/programs/674?include_partial=true');

  const summary = page.getByRole('region', { name: '핵심 신청 조건' });
  await expect(summary).toBeVisible();
  await expect(summary).toHaveAttribute('data-coverage', 'partial');
  await expect(summary.getByRole('note')).toContainText(
    '실제 자격 충족이나 선정을 확정하지 않습니다',
  );

  await expect(
    summary.getByRole('heading', { name: '제외 조건' }),
  ).toBeVisible();
  await expect(
    summary.getByText(webHandoff!.eligibility_summary.exclusions[0]!.text),
  ).toBeVisible();
  await expect(
    summary.getByRole('heading', { name: '필요 서류' }),
  ).toBeVisible();
  await expect(
    summary.getByText(webHandoff!.eligibility_summary.documents[0]!.text),
  ).toBeVisible();

  const phoneLink = summary.getByRole('link', { name: /전화 걸기/ });
  await expect(phoneLink).toHaveAttribute('href', /^tel:/);
  await phoneLink.focus();
  await expect(phoneLink).toBeFocused();
  await expect(
    summary.getByText(
      webHandoff!.eligibility_summary.institutional_contacts.find(
        (contact) => contact.kind === 'official_channel',
      )!.value,
    ),
  ).toBeVisible();

  const evidenceLinks = summary.getByRole('link', {
    name: /근거 \d+ 원문 열기/,
  });
  await expect(evidenceLinks.first()).toHaveAttribute(
    'rel',
    /noopener noreferrer/,
  );
  expect(await evidenceLinks.count()).toBeGreaterThan(0);

  await page.setViewportSize({ width: 390, height: 844 });
  const gridColumns = await summary
    .locator('.eligibility-summary__grid')
    .evaluate((element) => getComputedStyle(element).gridTemplateColumns);
  expect(gridColumns.trim().split(/\s+/)).toHaveLength(1);
});

test('ES3 unknown 빈 값과 긴 조건을 단정·가로 넘침 없이 표시한다', async ({
  page,
}) => {
  test.skip(process.env.VITE_USE_MOCK !== 'false');
  const unknown = contract.cases.find(
    (item) => item.case_id === 'unknown_missing_source_fields',
  );
  const longCondition = contract.cases.find(
    (item) => item.case_id === 'partial_long_condition',
  );
  expect(unknown).toBeTruthy();
  expect(longCondition).toBeTruthy();

  await page.route('**/api/v1/policies/675**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(detailResponse(675, unknown!.summary)),
    });
  });
  await page.goto('/programs/675?include_partial=true');

  const unknownSummary = page.getByRole('region', {
    name: '핵심 신청 조건',
  });
  await expect(unknownSummary).toHaveAttribute('data-coverage', 'unknown');
  await expect(unknownSummary).toContainText('구조화된 조건 미확인');
  await expect(unknownSummary).toContainText(
    '공식 원문에서 구조화된 제외 조건을 확인하지 못했습니다.',
  );
  await expect(unknownSummary).toContainText(
    '공개된 시설 문의처를 확인하지 못했습니다.',
  );

  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/v1/policies/676**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(detailResponse(676, longCondition!.summary)),
    });
  });
  await page.goto('/programs/676?include_partial=true');
  const longItem = page.locator('.eligibility-items__text').first();
  await expect(longItem).toBeVisible();
  const fitsViewport = await longItem.evaluate(
    (element) => element.scrollWidth <= element.clientWidth,
  );
  expect(fitsViewport).toBeTruthy();
});

test('ES3 상세 API 오류에서 기존 재시도 상태를 유지한다', async ({ page }) => {
  test.skip(process.env.VITE_USE_MOCK !== 'false');
  await page.route('**/api/v1/policies/677**', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'temporary failure' }),
    });
  });

  await page.goto('/programs/677?include_partial=true');
  await expect(
    page.getByText('정책 상세를 불러오지 못했습니다.'),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: '다시 시도' })).toBeVisible();
});

test('ES4 실제 PostgreSQL 상세 API 응답과 Browser 표시가 일치한다', async ({
  page,
  request,
}) => {
  const policyId = process.env.ES4_POLICY_ID;
  const apiBaseUrl = process.env.ES4_API_BASE_URL;
  test.skip(
    process.env.VITE_USE_MOCK !== 'false' || !policyId || !apiBaseUrl,
    'ES4 전용 PostgreSQL·Backend 환경에서만 실행합니다.',
  );

  const apiResponse = await request.get(
    `${apiBaseUrl}/api/v1/policies/${policyId}?include_partial=true`,
  );
  expect(apiResponse.status()).toBe(200);
  const policy = (await apiResponse.json()) as Record<string, unknown> & {
    eligibility_summary: EligibilitySummaryDto;
  };
  expect('provenance' in policy).toBeFalsy();

  await page.goto(`/programs/${policyId}?include_partial=true`);
  const summary = page.getByRole('region', { name: '핵심 신청 조건' });
  await expect(summary).toBeVisible();
  await expect(summary).toHaveAttribute(
    'data-coverage',
    policy.eligibility_summary.coverage,
  );

  const textGroups = [
    policy.eligibility_summary.requirements,
    policy.eligibility_summary.exclusions,
    policy.eligibility_summary.preferences,
    policy.eligibility_summary.documents,
    policy.eligibility_summary.unknowns,
  ];
  for (const items of textGroups) {
    for (const item of items) {
      await expect(summary.getByText(item.text, { exact: true }).first()).toBeVisible();
    }
  }

  for (const contact of policy.eligibility_summary.institutional_contacts) {
    if (contact.kind === 'phone') {
      const phoneLink = summary
        .getByRole('link', { name: /전화 걸기/ })
        .first();
      await expect(phoneLink).toContainText(contact.value);
      await expect(phoneLink).toHaveAttribute('href', /^tel:/);
    } else {
      await expect(
        summary.getByText(contact.value, { exact: true }).first(),
      ).toBeVisible();
    }
  }

  const apiEvidenceUrls = new Set(
    [
      ...policy.eligibility_summary.requirements,
      ...policy.eligibility_summary.exclusions,
      ...policy.eligibility_summary.preferences,
      ...policy.eligibility_summary.documents,
      ...policy.eligibility_summary.unknowns,
      ...policy.eligibility_summary.institutional_contacts,
    ].flatMap((item) => item.evidence.map((evidence) => evidence.source_url)),
  );
  const browserEvidenceUrls = new Set(
    await summary
      .getByRole('link', { name: /근거 \d+ 원문 열기/ })
      .evaluateAll((links) => links.map((link) => (link as HTMLAnchorElement).href)),
  );
  expect(browserEvidenceUrls).toEqual(apiEvidenceUrls);
});
