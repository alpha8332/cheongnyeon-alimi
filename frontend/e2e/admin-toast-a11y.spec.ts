import { expect, test, type Page } from '@playwright/test';

async function loginAsAdmin(page: Page, pin = '0000') {
  await page.goto('/admin/login');
  await page.getByLabel('관리자 PIN (4자리)').fill(pin);
  await page.getByRole('button', { name: '로그인' }).click();
}

async function waitForRunsLoaded(page: Page) {
  await expect(page.getByText('실행 기록을 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

function apiErrorToast(page: Page) {
  return page.getByLabel('API 오류 알림');
}

test.describe('Admin API Toast and a11y (FE3-06)', () => {
  test('1. login 429 — Toast·inline alert·PIN disable', async ({ page }) => {
    await page.goto('/admin/login');
    await page.getByLabel('관리자 PIN (4자리)').fill('4290');
    await page.getByRole('button', { name: '로그인' }).click();

    await expect(page.getByRole('alert')).toContainText(/Too many|로그인/i);
    await expect(apiErrorToast(page)).toBeVisible();
    await expect(page.getByLabel('관리자 PIN (4자리)')).toBeDisabled();
  });

  test('2. login 503 — retryable Toast', async ({ page }) => {
    await page.goto('/admin/login');
    await page.getByLabel('관리자 PIN (4자리)').fill('5000');
    await page.getByRole('button', { name: '로그인' }).click();

    const toast = apiErrorToast(page);
    await expect(toast).toBeVisible();
    await expect(toast.getByText(/unavailable|서버 오류/i)).toBeVisible();
    await expect(toast.getByRole('button', { name: '다시 시도' })).toBeVisible();
  });

  test('3. run list 503 filter — Toast·retry', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '실행 기록' }).click();
    await waitForRunsLoaded(page);

    const filters = page.getByLabel('실행 기록 필터');
    await filters.getByLabel('source_id').fill('MOCK_503');
    await filters.getByRole('button', { name: '필터 적용' }).click();

    const toast = apiErrorToast(page);
    await expect(toast).toBeVisible();
    await expect(toast.getByText('Service unavailable for admin list audit test.')).toBeVisible();
    await expect(toast.getByRole('button', { name: '다시 시도' })).toBeVisible();

    await toast.getByRole('button', { name: '다시 시도' }).click();
    await expect(toast).toHaveCount(0);
  });

  test('4. manual run confirm — Escape closes dialog', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '실행 기록' }).click();
    await waitForRunsLoaded(page);

    const filters = page.getByLabel('실행 기록 필터');
    await filters.getByLabel('status').selectOption('succeeded');
    await filters.getByRole('button', { name: '필터 적용' }).click();
    await waitForRunsLoaded(page);

    await page.getByRole('button', { name: '수동 실행 요청' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog.getByRole('heading', { name: '수동 실행 확인' })).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });

  test('5. keyboard — PIN Enter submit', async ({ page }) => {
    await page.goto('/admin/login');
    const pinInput = page.getByLabel('관리자 PIN (4자리)');
    await pinInput.fill('0000');
    await pinInput.press('Enter');

    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole('navigation', { name: '관리자 내비게이션' })).toBeVisible();
  });

  test('6. mobile viewport — login form·filter stack', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '실행 기록' }).click();
    await waitForRunsLoaded(page);

    await expect(page.getByLabel('실행 기록 필터')).toBeVisible();
    await expect(page.getByRole('table').getByText('CollectionRun 실행 기록')).toBeVisible();
  });
});
