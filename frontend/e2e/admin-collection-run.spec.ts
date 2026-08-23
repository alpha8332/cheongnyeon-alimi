import { expect, test, type Page } from '@playwright/test';

const MOCK_SUCCEEDED_RUN_ID = '11111111-1111-4111-8111-111111111111';
const MOCK_STALE_RUNNING_RUN_ID = '44444444-4444-4444-8444-444444444444';

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

function adminNav(page: Page) {
  return page.getByRole('navigation', { name: '관리자 내비게이션' });
}

test.describe('Admin CollectionRun browser flow (FE3-05)', () => {
  test('1. 보호 route — 미로그인 /admin/runs → login redirect', async ({
    page,
  }) => {
    await page.goto('/admin/runs');
    await expect(page).toHaveURL(/\/admin\/login$/);
    await expect(page.getByRole('heading', { name: '관리자 로그인' })).toBeVisible();
  });

  test('2. 잘못된 PIN — 401 inline error', async ({ page }) => {
    await loginAsAdmin(page, '1234');
    await expect(page).toHaveURL(/\/admin\/login$/);
    await expect(page.getByRole('alert')).toContainText(/PIN|인증|로그인/i);
  });

  test('3. PIN login — Mock 0000 → admin shell', async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole('navigation', { name: '관리자 내비게이션' })).toBeVisible();
    await expect(page.getByRole('button', { name: '로그아웃' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '관리 대시보드' })).toBeVisible();
    await expect(page.getByText('최신 수집 실행을 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(page.getByRole('heading', { name: '최신 수집 실행' })).toBeVisible();
    await expect(page.getByLabel('상태: 실행 중')).toBeVisible();
  });

  test('4. 실행 기록 list·pagination·filter', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await expect(page).toHaveURL(/\/admin\/runs$/);

    await waitForRunsLoaded(page);

    await expect(
      page.getByRole('table').getByText('CollectionRun 실행 기록'),
    ).toBeVisible();
    await expect(page.getByLabel('상태: 실행 중').first()).toBeVisible();

    const filters = page.getByLabel('실행 기록 필터');
    await filters.getByLabel('status').selectOption('succeeded');
    await filters.getByRole('button', { name: '필터 적용' }).click();

    await waitForRunsLoaded(page);
    await expect(page.getByLabel('상태: 성공').first()).toBeVisible();
    await expect(page.getByLabel('상태: 실행 중')).toHaveCount(0);
  });

  test('5. run detail — status·stale·counts', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await waitForRunsLoaded(page);

    await page
      .getByRole('link', { name: new RegExp(`${MOCK_STALE_RUNNING_RUN_ID.slice(0, 8)}`) })
      .click();

    await expect(page.getByRole('heading', { name: '실행 상세' })).toBeVisible();
    await expect(page.getByLabel('상태: 실행 중')).toBeVisible();
    await expect(page.getByLabel('Stale 실행')).toBeVisible();
    await expect(page.getByText(/stale로 표시/)).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Count aggregates' })).toBeVisible();
    await expect(page.getByText('inserted', { exact: true })).toBeVisible();
  });

  test('6. detail 404 shell', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await waitForRunsLoaded(page);

    await page.evaluate(() => {
      window.history.pushState({}, '', '/admin/runs/not-a-real-run-id');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });

    await expect(
      page.getByRole('heading', { name: '실행 기록을 찾을 수 없습니다' }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test('7a. 수동 실행 — running run 존재 시 disable', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await waitForRunsLoaded(page);

    const triggerButton = page.getByRole('button', { name: '수동 실행 요청' });
    await expect(triggerButton).toBeDisabled();
    await expect(
      page.getByText(/실행 중인 run이 있어 수동 실행을 일시 중지/),
    ).toBeVisible();
  });

  test('7b. 수동 실행 confirm — succeeded filter 후 trigger', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await waitForRunsLoaded(page);

    const filters = page.getByLabel('실행 기록 필터');
    await filters.getByLabel('status').selectOption('succeeded');
    await filters.getByRole('button', { name: '필터 적용' }).click();
    await waitForRunsLoaded(page);

    const triggerButton = page.getByRole('button', { name: '수동 실행 요청' });
    await expect(triggerButton).toBeEnabled();
    await triggerButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog.getByRole('heading', { name: '수동 실행 확인' })).toBeVisible();
    await dialog.getByRole('button', { name: '실행' }).click();

    await expect(page.getByText(/수동 실행을 요청했습니다/)).toBeVisible();
  });

  test('8. list → detail navigation', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await waitForRunsLoaded(page);

    await page
      .getByRole('link', { name: new RegExp(`${MOCK_SUCCEEDED_RUN_ID.slice(0, 8)}`) })
      .click();

    await expect(page).toHaveURL(
      new RegExp(`/admin/runs/${MOCK_SUCCEEDED_RUN_ID}`),
    );
    await expect(page.getByLabel('상태: 성공')).toBeVisible();
  });

  test('9. Real API admin run path golden', async ({ page }) => {
    test.skip(
      process.env.VITE_USE_MOCK !== 'false',
      'VITE_USE_MOCK=false + Backend admin API가 준비된 환경에서만 실행합니다.',
    );

    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '실행 기록', exact: true }).click();
    await waitForRunsLoaded(page);

    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    const firstRunLink = table.getByRole('link').first();
    await expect(firstRunLink).toBeVisible();
    await firstRunLink.click();

    await expect(page.getByRole('heading', { name: '실행 상세' })).toBeVisible();
    await expect(page.getByText('run_id', { exact: true })).toBeVisible();
  });

  test('10. data quality — 회차별 집계·drill-down', async ({ page }) => {
    await loginAsAdmin(page);
    await adminNav(page).getByRole('link', { name: '데이터 품질', exact: true }).click();
    await expect(page).toHaveURL(/\/admin\/quality$/);
    await expect(page.getByRole('heading', { name: '데이터 품질' })).toBeVisible();
    await expect(page.getByText('수집 실행 목록을 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });

    const table = page.getByRole('table');
    await expect(table.getByText('최근 수집 회차 품질 집계')).toBeVisible();
    await expect(table.getByLabel('상태: 실행 중').first()).toBeVisible();

    const failedRunLink = table.getByRole('link', { name: '50' }).first();
    await expect(failedRunLink).toBeVisible();
    await failedRunLink.click();

    await expect(page.getByRole('heading', { name: '실행 상세' })).toBeVisible();
    await expect(page.getByLabel('상태: 실패')).toBeVisible();
  });
});
