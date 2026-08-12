import { expect, test, type Page } from '@playwright/test';

const MOCK_ARCHIVE_DELETE_409_FILE_ID = 'log-file-archive-mock409';
const MOCK_POLICY_TITLE = '합성 청년 주거 지원';

async function loginAsAdmin(page: Page, pin = '0000') {
  await page.goto('/admin/login');
  await page.getByLabel('관리자 PIN (4자리)').fill(pin);
  await page.getByRole('button', { name: '로그인' }).click();
}

async function waitForPolicyDataLoaded(page: Page) {
  await expect(page.getByText('정책 데이터를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function waitForLogEventsLoaded(page: Page) {
  await expect(page.getByText('Log event를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

function apiErrorToast(page: Page) {
  return page.getByLabel('API 오류 알림');
}

test.describe('Admin observability Toast and a11y (FE8-06)', () => {
  test('1. policy list MOCK_503 — retryable Toast·table 유지', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '정책 데이터' }).click();
    await waitForPolicyDataLoaded(page);
    await expect(page.getByText(MOCK_POLICY_TITLE)).toBeVisible();

    const filters = page.getByLabel('정책 데이터 필터');
    await filters.getByLabel('source_id').fill('MOCK_503');
    await filters.getByRole('button', { name: '필터 적용' }).click();

    const toast = apiErrorToast(page);
    await expect(toast).toBeVisible();
    await expect(toast.getByText(/policy list audit test|서버 오류/i)).toBeVisible();
    await expect(toast.getByRole('button', { name: '다시 시도' })).toBeVisible();
    await expect(page.getByText(MOCK_POLICY_TITLE)).toBeVisible();
  });

  test('2. policy list MOCK_401 — login redirect', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '정책 데이터' }).click();
    await waitForPolicyDataLoaded(page);

    const filters = page.getByLabel('정책 데이터 필터');
    await filters.getByLabel('source_id').fill('MOCK_401');
    await filters.getByRole('button', { name: '필터 적용' }).click();

    await expect(page).toHaveURL(/\/admin\/login$/);
  });

  test('3. log event MOCK_503 — retryable Toast·event table 유지', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '구조화 Log' }).click();
    await waitForLogEventsLoaded(page);
    await expect(page.getByText('request_completed')).toBeVisible();

    const filters = page.getByLabel('Log event 필터');
    await filters.getByLabel('component').fill('MOCK_503');
    await filters.getByRole('button', { name: '필터 적용' }).click();

    const toast = apiErrorToast(page);
    await expect(toast).toBeVisible();
    await expect(toast.getByText(/log event list audit test|서버 오류/i)).toBeVisible();
    await expect(page.getByText('request_completed')).toBeVisible();
  });

  test('4. archive delete MOCK_409 — conflict Toast·dialog 유지', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '구조화 Log' }).click();
    await waitForLogEventsLoaded(page);

    await page.getByRole('button', { name: 'archive 삭제' }).click();
    const dialog = page.getByRole('dialog', { name: 'archive 삭제 확인' });
    await expect(dialog).toBeVisible();

    await dialog.getByLabel('archive file 선택').selectOption(MOCK_ARCHIVE_DELETE_409_FILE_ID);
    await expect(dialog.getByText(`삭제 대상 file_id: ${MOCK_ARCHIVE_DELETE_409_FILE_ID}`)).toBeVisible();

    const confirmLabel = `삭제하려면 file_id "${MOCK_ARCHIVE_DELETE_409_FILE_ID}"를 입력하세요`;
    await dialog.getByLabel(confirmLabel).fill(MOCK_ARCHIVE_DELETE_409_FILE_ID);
    await dialog.getByRole('button', { name: 'archive 삭제' }).click();

    const toast = apiErrorToast(page);
    await expect(toast).toBeVisible();
    await expect(toast.getByText(/audit test|conflict/i)).toBeVisible();
    await expect(dialog).toBeVisible();
  });

  test('5. keyboard — policy table sort·row Enter', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '정책 데이터' }).click();
    await waitForPolicyDataLoaded(page);

    const titleSort = page.getByRole('button', { name: '제목 정렬' });
    await titleSort.focus();
    await titleSort.press('Enter');
    await waitForPolicyDataLoaded(page);

    const firstRow = page.locator('.admin-policy-table__row--interactive').first();
    await firstRow.focus();
    await firstRow.press('Enter');
    await expect(page.getByRole('dialog')).toBeVisible();
  });

  test('6. column toggle — Escape closes panel', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '정책 데이터' }).click();
    await waitForPolicyDataLoaded(page);

    const trigger = page.getByRole('button', { name: '표시 열 설정' });
    await trigger.click();
    await expect(page.getByRole('group', { name: '표시 열' })).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.getByRole('group', { name: '표시 열' })).toHaveCount(0);
  });

  test('7. mobile viewport — table caption·filter stack', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await loginAsAdmin(page);
    await page.getByRole('link', { name: '구조화 Log' }).click();
    await waitForLogEventsLoaded(page);

    await expect(page.getByLabel('Log event 필터')).toBeVisible();
    await expect(page.getByText('Log events')).toBeVisible();
  });
});
