import { expect, test, type Page } from '@playwright/test';

/**
 * FE9-02 W4-F10 + W4-I3 Mock-first regression matrix.
 * Maps to develop_plan/frontend/09_integration_and_regression.md § FE9-02.
 */

const USER_LOCAL_STORAGE_KEY = 'cheongnyeon-alimi.user-local.v1';

const MOCK_HOUSING_POLICY_TITLE = '합성 청년 주거 지원';
/** Seed id 1 — has `application_end` but `application_status: closed` (ICS disabled in Mock). */
const MOCK_HOUSING_POLICY_ID = 1;

async function clearUserLocalStorage(page: Page) {
  await page.goto('/');
  await page.evaluate((key) => {
    window.localStorage.removeItem(key);
  }, USER_LOCAL_STORAGE_KEY);
}

async function loginAsAdmin(page: Page, pin = '0000') {
  await page.goto('/admin/login');
  await page.getByLabel('관리자 PIN (4자리)').fill(pin);
  await page.getByRole('button', { name: '로그인' }).click();
  await expect(page).toHaveURL(/\/admin$/);
}

async function waitForRunsLoaded(page: Page) {
  await expect(page.getByText('실행 기록을 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
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

async function waitForSearchSettled(page: Page) {
  await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function waitForProgramDetailSettled(page: Page) {
  await expect(page.getByText('정책 상세를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function waitForHomePolicies(page: Page) {
  await expect(page.getByText('주요 정책을 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function waitForRecommendationSettled(page: Page) {
  await expect(page.getByLabel('추천 결과 로딩 중')).toHaveCount(0, {
    timeout: 15_000,
  });
}

function eligibilitySummary(page: Page) {
  return page.getByRole('region', { name: '핵심 신청 조건' });
}

test.describe('Week 4 Frontend regression matrix (FE9-02)', () => {
  test('Path A — admin: PIN → runs → manual trigger → policies → logs (W4-I1)', async ({
    page,
  }) => {
    await loginAsAdmin(page);

    await page.getByRole('link', { name: '실행 기록' }).click();
    await expect(page).toHaveURL(/\/admin\/runs$/);
    await waitForRunsLoaded(page);
    await expect(
      page.getByRole('table').getByText('CollectionRun 실행 기록'),
    ).toBeVisible();

    const filters = page.getByLabel('실행 기록 필터');
    await filters.getByLabel('status').selectOption('succeeded');
    await filters.getByRole('button', { name: '필터 적용' }).click();
    await waitForRunsLoaded(page);

    const triggerButton = page.getByRole('button', { name: '수동 실행 요청' });
    await expect(triggerButton).toBeEnabled();
    await triggerButton.click();
    const runDialog = page.getByRole('dialog');
    await expect(runDialog.getByRole('heading', { name: '수동 실행 확인' })).toBeVisible();
    await runDialog.getByRole('button', { name: '실행' }).click();
    await expect(page.getByText(/수동 실행을 요청했습니다/)).toBeVisible();

    await page.getByRole('link', { name: '정책 데이터' }).click();
    await expect(page).toHaveURL(/\/admin\/policies$/);
    await waitForPolicyDataLoaded(page);
    await expect(
      page.getByRole('table').getByText('승인 Policy projection'),
    ).toBeVisible();
    await expect(page.getByText(MOCK_HOUSING_POLICY_TITLE).first()).toBeVisible();

    await page.getByRole('link', { name: '구조화 Log' }).click();
    await expect(page).toHaveURL(/\/admin\/logs$/);
    await waitForLogEventsLoaded(page);
    await expect(page.getByRole('table').getByText('로그 이벤트')).toBeVisible();
    await expect(page.getByText('request_completed')).toBeVisible();
  });

  test('Path B — eligibility: detail → card → evidence → 원문 (W4-IE1)', async ({
    page,
  }) => {
    await page.goto(`/programs/${MOCK_HOUSING_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_HOUSING_POLICY_TITLE }),
    ).toBeVisible();

    const summary = eligibilitySummary(page);
    await expect(summary.getByRole('heading', { name: '핵심 신청 조건', level: 2 })).toBeVisible();
    await expect(summary.getByRole('link', { name: /근거 1 원문 열기/ }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: '원문 링크 열기' })).toBeVisible();
    await expect(summary.getByRole('note')).toContainText(
      '실제 자격 충족이나 선정을 확정하지 않습니다',
    );
  });

  test('Path C — user: conditions → recommend → favorite → calendar → notify → .ics (W4-I2)', async ({
    page,
  }) => {
    await clearUserLocalStorage(page);

    await page.goto('/');
    const conditionsForm = page.getByRole('form', { name: '저장 조건 편집' });
    await conditionsForm.getByPlaceholder('예: 서울특별시').fill('서울특별시');
    await conditionsForm.getByPlaceholder('예: 24').fill('24');
    await conditionsForm.getByLabel('관심 분야').selectOption('housing');
    await conditionsForm.getByRole('button', { name: '조건 저장' }).click();
    await expect(page.getByText('저장 조건을 브라우저에 저장했습니다.')).toBeVisible();

    await page.getByRole('link', { name: '맞춤 추천' }).click();
    await page.getByRole('button', { name: '추천 받기' }).click();
    await waitForRecommendationSettled(page);
    await expect(page.getByRole('region', { name: '추천 결과' })).toBeVisible();

    await page.getByRole('link', { name: '홈' }).click();
    await waitForHomePolicies(page);
    const homeCard = page
      .locator('article.policy-card')
      .filter({ hasText: MOCK_HOUSING_POLICY_TITLE });
    await homeCard.getByRole('button', { name: '북마크 추가' }).click();
    await expect(homeCard.getByRole('button', { name: '북마크 해제' })).toBeVisible();

    await page.getByRole('link', { name: '마감 달력' }).click();
    await expect(page.getByRole('heading', { name: '마감 달력' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '북마크' })).toHaveAttribute(
      'aria-selected',
      'true',
    );

    await page.getByRole('link', { name: '알림' }).click();
    await expect(page.getByRole('heading', { name: '알림' })).toBeVisible();
    await expect(page.getByText('알림 대상 정책을 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });

    await page.goto(`/programs/${MOCK_HOUSING_POLICY_ID}`);
    await waitForProgramDetailSettled(page);
    await expect(
      page.getByRole('heading', { name: MOCK_HOUSING_POLICY_TITLE }),
    ).toBeVisible();
    const icsButton = page.getByRole('button', { name: '캘린더 (.ics) 다운로드' });
    await expect(icsButton).toBeVisible();
    // Mock seed policy 1 is closed — ICS UI is present but download stays disabled.
    await expect(icsButton).toBeDisabled();
  });

  test('Path Release 1 — home → /search golden → detail include_partial (W4-I3)', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /안녕하세요/ })).toBeVisible();

    await page.getByRole('button', { name: '서울 주거' }).click();
    await expect(page).toHaveURL(/\/search\?.*q=/);

    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');
    await waitForSearchSettled(page);

    const partialCard = page.locator('a.policy-card[href*="include_partial=true"]').first();
    await expect(partialCard).toBeVisible();
    await partialCard.click();

    await expect(page).toHaveURL(/\/programs\/\d+\?include_partial=true/);
    await waitForProgramDetailSettled(page);
    await expect(page.getByText('📄 정책 정보')).toBeVisible();
    await expect(page.locator('.policy-eligibility-notice')).toContainText(
      '실제 자격 충족을 확정하지 않습니다',
    );
  });

  test('Path Cross — mobile viewport·keyboard favorite spot checks (W4-F5)', async ({
    page,
  }) => {
    await clearUserLocalStorage(page);
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');
    await waitForHomePolicies(page);
    await expect(page.getByRole('form', { name: '저장 조건 편집' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /안녕하세요/, level: 1 })).toBeVisible();

    const card = page.locator('article.policy-card').first();
    const toggle = card.getByRole('button', { name: '북마크 추가' });
    await toggle.focus();
    await page.keyboard.press('Space');
    await expect(card.getByRole('button', { name: '북마크 해제' })).toBeVisible();

    await page.goto('/search');
    await expect(page).toHaveURL(/\/search$/);
    await page.getByLabel('정책 검색어').fill('복지로');
    await page.getByRole('button', { name: '검색하기' }).click();
    await waitForSearchSettled(page);
    await expect(page.getByRole('region', { name: '검색 결과' })).toBeVisible();
  });

  test('Real API week4 golden — conditional skip', async ({ page }) => {
    test.skip(
      process.env.VITE_USE_MOCK !== 'false',
      'VITE_USE_MOCK=false + Backend actual API 환경에서만 실행합니다.',
    );

    await page.goto(
      '/search?q=%EC%B2%9C%EC%95%88+%EC%82%AC%EB%8A%94+27%EC%82%B4+%EC%B2%AD%EB%85%84+%EB%8B%A8%EA%B8%B0%EC%88%99%EC%86%8C+%EC%A7%80%EC%9B%90+%EB%B0%9B%EC%9D%84+%EC%88%98+%EC%9E%88%EB%82%98%3F',
    );
    await waitForSearchSettled(page);
    await expect(page.getByRole('region', { name: '검색 결과' })).toBeVisible();
  });
});
