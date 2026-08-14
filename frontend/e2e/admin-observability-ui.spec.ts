import { expect, test, type Page } from '@playwright/test';

const MOCK_ARCHIVE_LOG_FILE_ID = 'app.log.1';
const MOCK_POLICY_TITLE = '합성 청년 주거 지원';
const MOCK_PARTIAL_POLICY_TITLE = '합성 청년 자산 지원 상세';

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
  await expect(page.getByText('로그 이벤트를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function openPoliciesPage(page: Page) {
  await loginAsAdmin(page);
  await page.getByRole('link', { name: '정책 데이터' }).click();
  await expect(page).toHaveURL(/\/admin\/policies$/);
  await waitForPolicyDataLoaded(page);
}

async function openLogsPage(page: Page) {
  await loginAsAdmin(page);
  await page.getByRole('link', { name: '구조화 Log' }).click();
  await expect(page).toHaveURL(/\/admin\/logs$/);
  await waitForLogEventsLoaded(page);
}

test.describe('Admin Observability browser flow (FE8-05)', () => {
  test('1. 보호 route — 미로그인 /admin/policies·/admin/logs → login redirect', async ({
    page,
  }) => {
    await page.goto('/admin/policies');
    await expect(page).toHaveURL(/\/admin\/login$/);
    await expect(page.getByRole('heading', { name: '관리자 로그인' })).toBeVisible();

    await page.goto('/admin/logs');
    await expect(page).toHaveURL(/\/admin\/login$/);
  });

  test('2. policy data table — list·pagination·sort', async ({ page }) => {
    await openPoliciesPage(page);

    await expect(page.getByRole('heading', { name: '정책 데이터', level: 1 })).toBeVisible();
    await expect(
      page.getByRole('table').getByText('승인 Policy projection'),
    ).toBeVisible();
    await expect(page.getByText(MOCK_POLICY_TITLE)).toBeVisible();

    const titleSort = page.getByRole('button', { name: '제목' });
    await titleSort.click();
    await waitForPolicyDataLoaded(page);
    await expect(titleSort).toBeVisible();

    await expect(page.getByRole('navigation', { name: '정책 pagination' })).toBeVisible();
  });

  test('3. policy filter — data_quality_status partial', async ({ page }) => {
    await openPoliciesPage(page);

    const filters = page.getByLabel('정책 데이터 필터');
    await filters.getByLabel('data_quality_status').selectOption('partial');
    await filters.getByRole('button', { name: '필터 적용' }).click();
    await waitForPolicyDataLoaded(page);

    await expect(page.getByText(MOCK_PARTIAL_POLICY_TITLE)).toBeVisible();
    await expect(page.getByText(MOCK_POLICY_TITLE)).toHaveCount(0);
  });

  test('4. policy row detail drawer — open·fields·close', async ({ page }) => {
    await openPoliciesPage(page);

    await page.getByRole('button', { name: `${MOCK_POLICY_TITLE} 상세보기` }).click();

    const drawer = page.getByRole('dialog', { name: 'Policy row 상세' });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByRole('heading', { name: 'Policy row 상세', level: 2 })).toBeVisible();
    await expect(drawer.getByText(MOCK_POLICY_TITLE)).toBeVisible();
    await expect(drawer.getByText('provenance·Raw payload·internal DB field는 표시하지 않습니다.')).toBeVisible();

    await drawer.getByRole('button', { name: '닫기' }).click();
    await expect(drawer).toBeHidden();
  });

  test('5. policy drawer — Escape keyboard close', async ({ page }) => {
    await openPoliciesPage(page);

    await page.getByRole('button', { name: `${MOCK_POLICY_TITLE} 상세보기` }).click();
    const drawer = page.getByRole('dialog', { name: 'Policy row 상세' });
    await expect(drawer).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(drawer).toBeHidden();
  });

  test('6. log files summary·event list·filter', async ({ page }) => {
    await openLogsPage(page);

    await expect(page.getByRole('heading', { name: '로그 조회 및 정리', level: 1 })).toBeVisible();
    await expect(page.getByLabel('로그 파일 목록')).toBeVisible();
    await expect(page.getByText('app.log', { exact: true })).toBeVisible();
    await expect(page.getByText(MOCK_ARCHIVE_LOG_FILE_ID).first()).toBeVisible();

    await expect(page.getByRole('table').getByText('로그 이벤트')).toBeVisible();
    await expect(page.getByText('request_completed')).toBeVisible();

    const filters = page.getByLabel('Log event 필터');
    await filters.getByLabel('level').selectOption('ERROR');
    await filters.getByRole('button', { name: '필터 적용' }).click();
    await waitForLogEventsLoaded(page);

    await expect(page.getByText('collection_step_failed')).toBeVisible();
    await expect(page.getByText('request_completed')).toHaveCount(0);
  });

  test('7. log event detail — safe allowlist·no Raw/SQL parameter', async ({ page }) => {
    await openLogsPage(page);

    const filters = page.getByLabel('Log event 필터');
    await filters.getByLabel('level').selectOption('ERROR');
    await filters.getByRole('button', { name: '필터 적용' }).click();
    await waitForLogEventsLoaded(page);

    await page.getByRole('button', { name: /2026\./ }).first().click();

    const detail = page.getByLabel('로그 이벤트 상세');
    await expect(detail).toBeVisible();
    await expect(detail.getByText('ValidationError')).toBeVisible();
    await expect(
      detail.getByText('스택 추적, 자격 증명, 원문 및 SQL 매개변수는 표시하지 않습니다.'),
    ).toBeVisible();
    await expect(page.getByText('Traceback (most recent call last)')).toHaveCount(0);
  });

  test('8. log explicit refresh', async ({ page }) => {
    await openLogsPage(page);

    await page.getByLabel('Log event 필터').getByRole('button', { name: '새로고침' }).click();
    await waitForLogEventsLoaded(page);
    await expect(page.getByRole('table').getByText('로그 이벤트')).toBeVisible();
  });

  test('9. log rotate confirm — Mock success', async ({ page }) => {
    await openLogsPage(page);

    await page.getByRole('button', { name: '현재 log rotate' }).click();
    const dialog = page.getByRole('dialog').filter({ hasText: '현재 log rotate 확인' });
    await expect(dialog).toBeVisible();
    await dialog.getByRole('button', { name: 'rotate 실행' }).click();

    await expect(
      page.getByText('Current log rotated and its generated archive deleted successfully.'),
    ).toBeVisible();
  });

  test('10. archive delete typed confirm — Mock success', async ({ page }) => {
    await openLogsPage(page);

    await page.getByRole('button', { name: 'archive 삭제' }).click();
    const dialog = page.getByRole('dialog').filter({ hasText: 'archive 삭제 확인' });
    await expect(dialog).toBeVisible();

    const archiveSelect = dialog.locator('select');
    await archiveSelect.selectOption({ index: 0 });
    const selectedArchiveId = await archiveSelect.inputValue();
    await dialog.locator('input[type="text"]').fill(selectedArchiveId);
    await expect(dialog.getByRole('button', { name: 'archive 삭제' })).toBeEnabled();
    await dialog.getByRole('button', { name: 'archive 삭제' }).click();

    await expect(page.getByText(/Log archive file 'app\.log\..+' deleted successfully\./)).toBeVisible();
  });

  test('11. admin nav cross-route — policies ↔ logs', async ({ page }) => {
    await openPoliciesPage(page);
    await page.getByRole('link', { name: '구조화 Log' }).click();
    await expect(page).toHaveURL(/\/admin\/logs$/);
    await waitForLogEventsLoaded(page);

    await page.getByRole('link', { name: '정책 데이터' }).click();
    await expect(page).toHaveURL(/\/admin\/policies$/);
    await waitForPolicyDataLoaded(page);
  });

  test('12. mobile viewport — policies·logs layout', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await openPoliciesPage(page);
    await expect(page.getByRole('heading', { name: '정책 데이터', level: 1 })).toBeVisible();
    await expect(page.getByLabel('정책 데이터 필터')).toBeVisible();

    await page.getByRole('link', { name: '구조화 Log' }).click();
    await waitForLogEventsLoaded(page);
    await expect(page.getByLabel('Log maintenance')).toBeVisible();
  });

  test('13. Real API admin observability golden', async ({ page }) => {
    test.skip(
      process.env.VITE_USE_MOCK !== 'false',
      'VITE_USE_MOCK=false + Backend admin observability API가 준비된 환경에서만 실행합니다.',
    );

    await openPoliciesPage(page);
    await expect(page.getByRole('table')).toBeVisible();

    await page.getByRole('link', { name: '구조화 Log' }).click();
    await waitForLogEventsLoaded(page);
    await expect(page.getByLabel('로그 파일 목록')).toBeVisible();
    await expect(page.getByRole('table').getByText('로그 이벤트')).toBeVisible();
  });
});
