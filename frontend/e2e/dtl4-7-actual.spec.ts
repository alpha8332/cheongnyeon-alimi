import { rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

const API_BASE_URL = process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';
const ACTUAL_ARCHIVE_ID = 'app.log.dtl4-7-e2e';
const ACTUAL_ARCHIVE_PATH = path.resolve(
  process.cwd(),
  '..',
  'backend',
  'logs',
  ACTUAL_ARCHIVE_ID,
);
const GOLDEN_QUERY = '천안 사는 27살 청년 단기숙소 지원 받을 수 있나?';

function requireActualEnvironment() {
  test.skip(
    process.env.DTL47_ACTUAL !== 'true' || process.env.VITE_USE_MOCK !== 'false',
    'DTL47_ACTUAL=true + VITE_USE_MOCK=false actual 통합 환경에서만 실행합니다.',
  );
}

async function loginAsAdmin(page: Page) {
  await page.goto('/admin/login');
  await page.getByLabel('관리자 PIN (4자리)').fill('0000');
  await page.getByRole('button', { name: '로그인' }).click();
  await expect(page).toHaveURL(/\/admin$/);
}

async function createAdminToken(request: APIRequestContext) {
  const response = await request.post(`${API_BASE_URL}/api/v1/admin/session`, {
    data: { pin: '0000' },
  });
  expect(response.status()).toBe(200);
  const payload = (await response.json()) as { access_token: string };
  expect(payload.access_token).toBeTruthy();
  return payload.access_token;
}

async function waitForHomePolicies(page: Page) {
  await expect(page.getByText('주요 정책을 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
  await expect(page.locator('article.policy-card').first()).toBeVisible();
}

test.describe('DTL4-7 actual PostgreSQL → FastAPI → React acceptance', () => {
  test.beforeAll(async () => {
    if (process.env.DTL47_ACTUAL === 'true') {
      await writeFile(
        ACTUAL_ARCHIVE_PATH,
        '{"timestamp":"2026-08-14T00:00:00Z","level":"INFO","component":"e2e","event":"dtl4_7_archive_fixture"}\n',
        'utf8',
      );
    }
  });

  test.afterAll(async () => {
    await rm(ACTUAL_ARCHIVE_PATH, { force: true });
  });

  test('A. 관리자 actual: Policy·CollectionRun·log maintenance·인증 경계', async ({
    page,
    request,
  }) => {
    requireActualEnvironment();

    await loginAsAdmin(page);
    await page.getByRole('link', { name: '정책 데이터' }).click();
    await expect(page.getByText('정책 데이터를 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(page.getByRole('table')).toBeVisible();
    await page.getByRole('button', { name: /상세보기/ }).first().click();
    await expect(page.getByRole('dialog', { name: 'Policy row 상세' })).toContainText(
      'provenance·Raw payload·internal DB field는 표시하지 않습니다.',
    );
    await page.keyboard.press('Escape');

    await page.getByRole('link', { name: '실행 기록' }).click();
    await expect(page.getByText('실행 기록을 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    const firstRunLink = page.getByRole('table').getByRole('link').first();
    await expect(firstRunLink).toBeVisible();
    await firstRunLink.click();
    await expect(page.getByText('실행 상세')).toBeVisible();

    await page.getByRole('link', { name: '구조화 Log' }).click();
    await expect(page.getByText('로그 이벤트를 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(page.getByText(ACTUAL_ARCHIVE_ID)).toBeVisible();

    await page.getByRole('button', { name: '현재 log rotate' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'rotate 실행' }).click();
    await expect(
      page.getByText('Current log rotated and its generated archive deleted successfully.'),
    ).toBeVisible();

    await page.getByRole('button', { name: 'archive 삭제' }).click();
    const deleteDialog = page.getByRole('dialog').filter({ hasText: 'archive 삭제 확인' });
    await deleteDialog.locator('select').selectOption(ACTUAL_ARCHIVE_ID);
    await deleteDialog.locator('input[type="text"]').fill(ACTUAL_ARCHIVE_ID);
    const deleteResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === 'DELETE' &&
        response.url().endsWith(`/api/v1/admin/logs/archives/${ACTUAL_ARCHIVE_ID}`),
    );
    await deleteDialog.getByRole('button', { name: 'archive 삭제' }).click();
    const deleteResponse = await deleteResponsePromise;
    expect(deleteResponse.status()).toBe(200);
    const deletePayload = (await deleteResponse.json()) as {
      deleted: boolean;
      audit_id: string;
    };
    expect(deletePayload.deleted).toBe(true);
    expect(deletePayload.audit_id).toMatch(/^audit-[0-9a-f]{8}$/);

    const invalidTokenResponse = await request.get(
      `${API_BASE_URL}/api/v1/admin/collection-runs`,
      { headers: { Authorization: 'Bearer invalid-token' } },
    );
    expect(invalidTokenResponse.status()).toBe(401);

    const token = await createAdminToken(request);
    const activeDeleteResponse = await request.delete(
      `${API_BASE_URL}/api/v1/admin/logs/archives/app.log`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    expect(activeDeleteResponse.status()).toBe(400);

    const wrongPinStatuses: number[] = [];
    for (let attempt = 0; attempt < 5; attempt += 1) {
      const response = await request.post(`${API_BASE_URL}/api/v1/admin/session`, {
        data: { pin: '9999' },
      });
      wrongPinStatuses.push(response.status());
      expect(await response.text()).not.toContain('9999');
    }
    expect(wrongPinStatuses.slice(0, 4)).toEqual([401, 401, 401, 401]);
    expect(wrongPinStatuses[4]).toBe(429);
  });

  test('B. 웹 Source actual: golden 검색·자격요건·대표 지역 정책', async ({
    page,
  }) => {
    requireActualEnvironment();
    const eligibilityPolicyId = process.env.DTL47_ELIGIBILITY_POLICY_ID;
    const regionalPolicyId = process.env.DTL47_REGIONAL_POLICY_ID;
    expect(eligibilityPolicyId).toBeTruthy();
    expect(regionalPolicyId).toBeTruthy();

    await page.goto(`/search?q=${encodeURIComponent(GOLDEN_QUERY)}`);
    await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
      timeout: 15_000,
    });
    const results = page.getByRole('region', { name: '검색 결과' });
    await expect(results.getByText('청년단기숙소 지원사업')).toBeVisible();
    await expect(results).toContainText('실제 자격 충족을 확정하지 않습니다');

    await page.goto(`/programs/${eligibilityPolicyId}?include_partial=true`);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText('핵심 신청 조건')).toBeVisible();
    await expect(
      page.getByText(/실제 자격 충족이나 선정을 확정하지 않습니다/),
    ).toBeVisible();
    await expect(page.getByRole('link', { name: /원문 열기/ }).first()).toHaveAttribute(
      'href',
      /^https:\/\//,
    );

    await page.goto(`/programs/${regionalPolicyId}?include_partial=true`);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText('부산청년플랫폼')).toBeVisible();
    await expect(
      page.getByRole('region', { name: '핵심 신청 조건' }).getByText('일부 조건만 확인됨'),
    ).toBeVisible();
  });

  test('C. 사용자 actual: 추천·북마크·달력·알림·ICS·손상 저장소 복구', async ({
    page,
  }) => {
    requireActualEnvironment();
    const deadlinePolicyId = process.env.DTL47_DEADLINE_POLICY_ID;
    expect(deadlinePolicyId).toBeTruthy();

    await page.goto('/recommendations');
    const form = page.getByRole('form', { name: '맞춤 추천 조건 편집' });
    await form.getByPlaceholder('예: 서울특별시').fill('천안시');
    await form.getByPlaceholder('예: 24').fill('27');
    await form.getByLabel('관심 분야').selectOption('housing');
    await form.getByRole('button', { name: '추천 받기' }).click();
    await expect(page.getByLabel('추천 결과 로딩 중')).toHaveCount(0, {
      timeout: 15_000,
    });
    const recommendationResults = page.getByRole('region', { name: '추천 결과' });
    await expect(recommendationResults.locator('article').first()).toBeVisible();
    await expect(recommendationResults).toContainText('자격을 확정하지 않으며');
    await expect(recommendationResults).not.toContainText(/자격 확률/i);

    await page.goto('/');
    await waitForHomePolicies(page);
    await page.locator('article.policy-card').first().getByRole('button', {
      name: '북마크 추가',
    }).click();
    await page.getByRole('link', { name: '북마크' }).click();
    await expect(page.locator('article.policy-card').first()).toBeVisible();
    await page.reload();
    await expect(page.locator('article.policy-card').first()).toBeVisible();

    await page.goto('/calendar');
    await page.getByRole('tab', { name: '전체 정책' }).click();
    await expect(page.getByText('달력 데이터를 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    const hasDeadline = (await page.locator('.calendar-deadline-list__day').count()) > 0;
    const hasEmptyCalendar = await page
      .getByText('표시할 신청 마감일이 있는 정책이 없습니다.')
      .isVisible();
    expect(hasDeadline || hasEmptyCalendar).toBe(true);

    await page.goto('/notifications');
    await expect(page.getByText('알림 대상 정책을 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(page.getByText(/외부 push·이메일·Service Worker 알림은 사용하지 않습니다/)).toBeVisible();

    await page.goto(`/programs/${deadlinePolicyId}?include_partial=true`);
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: '캘린더 (.ics) 다운로드' }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.ics$/);

    await page.evaluate(() => {
      window.localStorage.setItem('cheongnyeon-alimi.user-local.v1', '{broken-json');
    });
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /안녕하세요/, level: 1 })).toBeVisible();
    await expect(page.getByText('아직 저장된 조건이 없습니다.')).toBeVisible();
  });
});
