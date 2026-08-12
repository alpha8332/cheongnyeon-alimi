import { expect, test, type Page } from '@playwright/test';

const MOCK_COMPLETE_POLICY_ID = 9101;
const MOCK_COMPLETE_POLICY_TITLE = 'Mock Complete Eligibility Policy';

async function waitForProgramDetailSettled(page: Page) {
  await expect(page.getByText('정책 상세를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

function eligibilityCard(page: Page) {
  return page.locator('article.eligibility-summary-card');
}

function apiErrorToast(page: Page) {
  return page.getByLabel('API 오류 알림');
}

test.describe('Eligibility detail Toast and a11y (FE7-06)', () => {
  test('1. summary refetch 503 — retryable Toast·detail body 유지', async ({
    page,
  }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_COMPLETE_POLICY_TITLE }),
    ).toBeVisible();
    await expect(page.getByText('📄 정책 정보')).toBeVisible();

    const card = eligibilityCard(page);
    await card.getByRole('button', { name: '핵심 신청 조건 새로고침' }).click();

    const toast = apiErrorToast(page);
    await expect(toast).toBeVisible();
    await expect(toast.getByText(/audit test|불러오지 못했습니다/i)).toBeVisible();
    await expect(toast.getByRole('button', { name: '다시 시도' })).toBeVisible();

    await expect(
      page.getByRole('heading', { name: MOCK_COMPLETE_POLICY_TITLE }),
    ).toBeVisible();
    await expect(card.getByText('만 19세 이상 34세 이하 청년')).toBeVisible();
    await expect(card.getByRole('alert')).toHaveCount(0);
  });

  test('2. long text expand — keyboard toggle·aria-expanded', async ({ page }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    const expandButton = card.getByRole('button', { name: '조건 내용 더 보기' }).first();
    await expect(expandButton).toBeVisible();
    await expect(expandButton).toHaveAttribute('aria-expanded', 'false');

    await expandButton.focus();
    await expandButton.press('Enter');
    await expect(card.getByRole('button', { name: '조건 내용 접기' }).first()).toBeVisible();
    await expect(card.getByRole('button', { name: '조건 내용 접기' }).first()).toHaveAttribute(
      'aria-expanded',
      'true',
    );
  });

  test('3. comparison badge — text·icon accessible name', async ({ page }) => {
    await page.goto('/');
    await page.getByPlaceholder('예: 서울특별시').fill('서울특별시');
    await page.getByPlaceholder('예: 24').fill('24');
    await page.getByLabel('관심 분야').selectOption('housing');
    await page.getByRole('button', { name: '조건 저장' }).click();

    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const badge = eligibilityCard(page).locator('.eligibility-comparison-badge').first();
    await expect(badge).toBeVisible();
    await expect(badge).toHaveAttribute('aria-label', '조건상 일치');
    await expect(badge.getByText('조건상 일치')).toBeVisible();
  });

  test('4. keyboard section nav — evidence link focus', async ({ page }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    await expect(card.getByRole('navigation', { name: '핵심 신청 조건 섹션' })).toBeVisible();

    const evidenceLink = card.getByRole('link', { name: '원문 근거 보기' }).first();
    await evidenceLink.focus();
    await expect(evidenceLink).toBeFocused();
    await expect(evidenceLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  test('5. include_partial refetch 422 — inline validation alert', async ({
    page,
  }) => {
    await page.goto('/programs/9102?include_partial=true');
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    await card.getByRole('button', { name: '핵심 신청 조건 새로고침' }).click();

    await expect(card.getByRole('alert')).toContainText(/include_partial/i);
    await expect(apiErrorToast(page)).toHaveCount(0);
  });

  test('6. mobile viewport — section stack', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    await expect(card.getByRole('heading', { name: '필수 조건', level: 3 })).toBeVisible();
    await expect(card.getByRole('button', { name: '핵심 신청 조건 새로고침' })).toBeVisible();
  });
});
