import { expect, test, type Page } from '@playwright/test';
import {
  DATA06_KOSAF_IDENTITY,
  isActualApiMode,
  MOCK_ONLY,
  resolveActualPolicyByIdentity,
  skipIfActualApi,
  skipUnlessActualApi,
} from './helpers/e2eMode';

async function waitForProgramDetailSettled(page: Page) {
  await expect(page.getByText('정책 상세를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function waitForSearchSettled(page: Page) {
  await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
    timeout: 15_000,
  });
}

function eligibilitySummary(page: Page) {
  return page.getByRole('region', { name: '핵심 신청 조건' });
}

test.describe('Eligibility Summary approved contract browser flow', () => {
  test('partial seed detail renders approved sections, evidence, and non-definitive copy', async ({
    page,
  }) => {
    skipIfActualApi(test);

    await page.goto(`/programs/${MOCK_ONLY.PARTIAL_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_ONLY.PARTIAL_POLICY_TITLE }),
    ).toBeVisible();

    const summary = eligibilitySummary(page);
    await expect(summary).toHaveAttribute('data-coverage', 'partial');
    await expect(summary.getByRole('heading', { name: '신청 조건', exact: true })).toBeVisible();
    await expect(summary.getByRole('heading', { name: '제외 조건' })).toBeVisible();
    await expect(summary.getByRole('heading', { name: '우대 조건' })).toBeVisible();
    await expect(summary.getByRole('heading', { name: '필요 서류' })).toBeVisible();
    await expect(summary.getByRole('heading', { name: '추가 확인 필요' })).toBeVisible();
    await expect(summary.getByRole('heading', { name: '문의처' })).toBeVisible();
    await expect(summary.getByText('19세 ~ 34세')).toBeVisible();
    await expect(summary.getByText('합성 청년 대상')).toBeVisible();
    await expect(summary.getByRole('note')).toContainText(
      '실제 자격 충족이나 선정을 확정하지 않습니다',
    );
  });

  test('evidence link is keyboard focusable and protected for a new tab', async ({
    page,
  }) => {
    skipIfActualApi(test);

    await page.goto(`/programs/${MOCK_ONLY.PARTIAL_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const evidenceLink = eligibilitySummary(page)
      .getByRole('link', { name: /근거 1 원문 열기/ })
      .first();
    await evidenceLink.focus();
    await expect(evidenceLink).toBeFocused();
    await expect(evidenceLink).toHaveAttribute('target', '_blank');
    await expect(evidenceLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  test('unknown partial detail keeps empty sections explicit', async ({ page }) => {
    skipIfActualApi(test);

    await page.goto(`/programs/${MOCK_ONLY.UNKNOWN_POLICY_ID}?include_partial=true`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_ONLY.UNKNOWN_POLICY_TITLE }),
    ).toBeVisible();
    const summary = eligibilitySummary(page);
    await expect(summary).toHaveAttribute('data-coverage', 'unknown');
    await expect(summary).toContainText(
      '공식 원문에서 구조화된 신청 조건을 확인하지 못했습니다.',
    );
    await expect(summary).toContainText(
      '공식 원문에서 구조화된 제외 조건을 확인하지 못했습니다.',
    );
    await expect(summary).toContainText(
      '공개된 시설 문의처를 확인하지 못했습니다.',
    );
  });

  test('mobile layout uses one eligibility grid column', async ({ page, request }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const detailPath = isActualApiMode()
      ? `/programs/${(await resolveActualPolicyByIdentity(request)).id}?include_partial=true`
      : `/programs/${MOCK_ONLY.PARTIAL_POLICY_ID}`;
    await page.goto(detailPath);
    await waitForProgramDetailSettled(page);

    const columns = await eligibilitySummary(page)
      .locator('.eligibility-summary__grid')
      .evaluate((element) => getComputedStyle(element).gridTemplateColumns);
    expect(columns.trim().split(/\s+/)).toHaveLength(1);
  });

  test('Release 1 search still navigates to a policy detail', async ({ page }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');
    await waitForSearchSettled(page);

    const policyCard = page.getByRole('region', { name: '검색 결과' })
      .locator('a.policy-card')
      .first();
    await expect(policyCard).toBeVisible();
    await policyCard.click();
    await expect(page).toHaveURL(/\/programs\/\d+/);
    await waitForProgramDetailSettled(page);
    await expect(page.getByText('📄 정책 정보')).toBeVisible();
  });

  test('Real API eligibility detail — unknown coverage and non-definitive copy', async ({
    page,
    request,
  }) => {
    skipUnlessActualApi(test);

    const policy = await resolveActualPolicyByIdentity(request);

    await page.goto(
      `/programs/${policy.id}?include_partial=true`,
    );
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: DATA06_KOSAF_IDENTITY.title }),
    ).toBeVisible();

    const summary = eligibilitySummary(page);
    await expect(summary).toHaveAttribute(
      'data-coverage',
      DATA06_KOSAF_IDENTITY.eligibilityCoverage,
    );
    await expect(summary).toContainText(
      '공식 원문에서 구조화된 신청 조건을 확인하지 못했습니다.',
    );
    await expect(summary.getByRole('note')).toContainText(
      '실제 자격 충족이나 선정을 확정하지 않습니다',
    );
    await expect(page.getByText('접수 중', { exact: true })).toBeVisible();
  });
});
