import { expect, test, type Page } from '@playwright/test';

const USER_LOCAL_STORAGE_KEY = 'cheongnyeon-alimi.user-local.v1';

const MOCK_POLICY_WITH_DEADLINE_TITLE = '합성 청년 주거 지원';
const MOCK_POLICY_ALWAYS_OPEN_TITLE = '합성 상시 생활 지원';

async function clearUserLocalStorage(page: Page) {
  await page.goto('/');
  await page.evaluate((key) => {
    window.localStorage.removeItem(key);
  }, USER_LOCAL_STORAGE_KEY);
}

async function acceptAllDialogsDuring(page: Page, action: () => Promise<void>) {
  const handler = (dialog: { accept: () => Promise<void> }) => {
    void dialog.accept();
  };

  page.on('dialog', handler);

  try {
    await action();
  } finally {
    page.off('dialog', handler);
  }
}

async function waitForHomePolicies(page: Page) {
  await expect(page.getByText('주요 정책을 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
  await expect(page.locator('article.policy-card').first()).toBeVisible();
}

async function favoritePolicyOnHome(page: Page, title: string) {
  await waitForHomePolicies(page);

  const card = page.locator('article.policy-card').filter({ hasText: title });
  await expect(card).toBeVisible();
  await card.getByRole('button', { name: '북마크 추가' }).click();
  await expect(card.getByRole('button', { name: '북마크 해제' })).toBeVisible();
}

test.describe('User Service browser flow (FE5-07)', () => {
  test.beforeEach(async ({ page }) => {
    await clearUserLocalStorage(page);
  });

  test('1. 홈 — 저장 조건 저장 및 reload 유지', async ({ page }) => {
    await page.goto('/');

    const form = page.getByRole('form', { name: '저장 조건 편집' });
    await form.getByPlaceholder('예: 서울특별시').fill('서울특별시');
    await form.getByPlaceholder('예: 24').fill('24');
    await form.getByLabel('관심 분야').selectOption('housing');
    await form.getByRole('button', { name: '조건 저장' }).click();

    await expect(page.getByText('저장 조건을 브라우저에 저장했습니다.')).toBeVisible();
    await expect(page.getByText(/저장됨:.*서울특별시/)).toBeVisible();

    await page.reload();
    await expect(page.getByText(/저장됨:.*서울특별시/)).toBeVisible();
    await expect(form.getByPlaceholder('예: 서울특별시')).toHaveValue('서울특별시');
  });

  test('2. 북마크 toggle — 홈→북마크→상세 cross-route', async ({ page }) => {
    await page.goto('/');
    await favoritePolicyOnHome(page, MOCK_POLICY_WITH_DEADLINE_TITLE);

    await page.getByRole('link', { name: '북마크' }).click();
    await expect(page).toHaveURL(/\/favorites$/);
    await expect(page.getByText(MOCK_POLICY_WITH_DEADLINE_TITLE)).toBeVisible();

    await page
      .locator('article.policy-card')
      .filter({ hasText: MOCK_POLICY_WITH_DEADLINE_TITLE })
      .getByRole('link', { name: MOCK_POLICY_WITH_DEADLINE_TITLE })
      .click();

    await expect(page).toHaveURL(/\/programs\/\d+/);
    await expect(page.getByRole('button', { name: '북마크 해제' })).toBeVisible();
  });

  test('3. 북마크 reload 후 유지', async ({ page }) => {
    await page.goto('/');
    await favoritePolicyOnHome(page, MOCK_POLICY_ALWAYS_OPEN_TITLE);

    await page.reload();
    await waitForHomePolicies(page);

    const card = page.locator('article.policy-card').filter({
      hasText: MOCK_POLICY_ALWAYS_OPEN_TITLE,
    });
    await expect(card.getByRole('button', { name: '북마크 해제' })).toBeVisible();

    await page.getByRole('link', { name: '북마크' }).click();
    await expect(page.getByText(MOCK_POLICY_ALWAYS_OPEN_TITLE)).toBeVisible();
  });

  test('4. 조건-only 초기화 — 북마크 유지', async ({ page }) => {
    await page.goto('/');
    await favoritePolicyOnHome(page, MOCK_POLICY_WITH_DEADLINE_TITLE);

    const form = page.getByRole('form', { name: '저장 조건 편집' });
    await form.getByPlaceholder('예: 서울특별시').fill('대전광역시');
    await form.getByRole('button', { name: '조건 저장' }).click();
    await expect(page.getByText(/저장됨:.*대전광역시/)).toBeVisible();

    await acceptAllDialogsDuring(page, async () => {
      await form.getByRole('button', { name: '조건 초기화' }).click();
    });

    await expect(page.getByText('저장 조건을 초기화했습니다.')).toBeVisible();
    await expect(page.getByText('아직 저장된 조건이 없습니다.')).toBeVisible();

    await page.getByRole('link', { name: '북마크' }).click();
    await expect(page.getByText(MOCK_POLICY_WITH_DEADLINE_TITLE)).toBeVisible();
  });

  test('5. 북마크 empty·loading shell', async ({ page }) => {
    await page.goto('/favorites');
    await expect(page.getByRole('heading', { name: '북마크' })).toBeVisible();
    await expect(
      page.getByText('저장한 정책이 없습니다. 정책 카드의 ☆ 버튼으로 북마크를 추가해 보세요.'),
    ).toBeVisible();
  });

  test('6. 마감 달력 — scope toggle·empty states', async ({ page }) => {
    await page.goto('/calendar');

    await expect(page.getByRole('heading', { name: '마감 달력' })).toBeVisible();
    await expect(
      page.getByText('북마크한 정책이 없습니다. 정책 카드에서 ☆ 버튼으로 추가해 보세요.'),
    ).toBeVisible();

    await page.getByRole('tab', { name: '전체 정책' }).click();
    await expect(page.getByText('달력 데이터를 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });

    const deadlineList = page.locator('.calendar-deadline-list__day');
    const emptyMessage = page.getByText('표시할 신청 마감일이 있는 정책이 없습니다.');
    const hasDeadlines = (await deadlineList.count()) > 0;

    expect(hasDeadlines || (await emptyMessage.isVisible())).toBeTruthy();
  });

  test('7. 알림 — empty shell (북마크 없음·마감 임박 없음)', async ({ page }) => {
    await page.goto('/notifications');

    await expect(page.getByRole('heading', { name: '알림' })).toBeVisible();
    await expect(
      page.getByText('북마크한 정책이 없습니다. 마감 임박 알림은 북마크한 정책에만 표시됩니다.'),
    ).toBeVisible();
    await expect(
      page.getByText('외부 push·이메일·Service Worker 알림은 사용하지 않습니다.'),
    ).toBeVisible();

    await page.goto('/');
    await favoritePolicyOnHome(page, MOCK_POLICY_ALWAYS_OPEN_TITLE);

    await page.getByRole('link', { name: '알림' }).click();
    await expect(page.getByText('알림 대상 정책을 불러오는 중입니다.')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(
      page.getByText(
        '마감 임박 알림이 없습니다. 상시·일정 미정·D-7 초과 정책은 알림에 포함되지 않습니다.',
      ),
    ).toBeVisible();
  });

  test('8. 사용자 데이터 전체 삭제 — reset→reload', async ({ page }) => {
    await page.goto('/');
    await favoritePolicyOnHome(page, MOCK_POLICY_WITH_DEADLINE_TITLE);

    const form = page.getByRole('form', { name: '저장 조건 편집' });
    await form.getByPlaceholder('예: 서울특별시').fill('부산광역시');
    await form.getByRole('button', { name: '조건 저장' }).click();

    await page.getByRole('link', { name: '북마크' }).click();
    await expect(page.getByText(MOCK_POLICY_WITH_DEADLINE_TITLE)).toBeVisible();

    page.on('dialog', (dialog) => {
      void dialog.accept();
    });
    await page.getByRole('button', { name: '모든 사용자 데이터 삭제' }).click();

    await expect
      .poll(async () =>
        page.evaluate((key) => window.localStorage.getItem(key), USER_LOCAL_STORAGE_KEY),
      )
      .toBeNull();
    await expect(
      page.getByText('저장한 정책이 없습니다. 정책 카드의 ☆ 버튼으로 북마크를 추가해 보세요.'),
    ).toBeVisible();

    await page.reload();
    await expect(
      page.getByText('저장한 정책이 없습니다. 정책 카드의 ☆ 버튼으로 북마크를 추가해 보세요.'),
    ).toBeVisible();

    await page.goto('/');
    await expect(page.getByText('아직 저장된 조건이 없습니다.')).toBeVisible();
  });

  test('9. 상세 — 종료일 없으면 ICS 버튼 disabled', async ({ page }) => {
    await page.goto('/programs/2');

    await expect(page.getByRole('heading', { name: MOCK_POLICY_ALWAYS_OPEN_TITLE })).toBeVisible({
      timeout: 15_000,
    });

    const icsButton = page.getByRole('button', { name: '캘린더 (.ics) 다운로드' });
    await expect(icsButton).toBeDisabled();
  });

  test('10. sidebar nav — 추천·달력 cross-route', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('link', { name: '맞춤 추천' }).click();
    await expect(page).toHaveURL(/\/recommendations$/);
    await expect(page.getByRole('heading', { name: '맞춤 추천', level: 1 })).toBeVisible();
    await expect(page.getByRole('link', { name: '/search' })).toBeVisible();

    await page.getByRole('link', { name: '마감 달력' }).click();
    await expect(page).toHaveURL(/\/calendar$/);
    await expect(page.getByRole('tab', { name: '북마크' })).toBeVisible();
  });

  test('11. keyboard — favorite toggle aria-pressed', async ({ page }) => {
    await page.goto('/');
    await waitForHomePolicies(page);

    const card = page.locator('article.policy-card').first();
    const toggle = card.getByRole('button', { name: '북마크 추가' });

    await toggle.focus();
    await page.keyboard.press('Enter');
    await expect(card.getByRole('button', { name: '북마크 해제' })).toBeVisible();
    await expect(card.getByRole('button', { name: '북마크 해제' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  test('12. mobile viewport — 홈·북마크 페이지', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page.getByRole('form', { name: '저장 조건 편집' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /안녕하세요/, level: 1 })).toBeVisible();

    await page.goto('/favorites');
    await expect(page.getByRole('heading', { name: '북마크', level: 1 })).toBeVisible();
  });

  test('13. 홈→검색 golden entry', async ({ page }) => {
    await page.goto('/');

    await page.getByLabel('정책 검색어').fill('서울 주거');
    await page.getByRole('button', { name: '검색하기' }).click();

    await expect(page).toHaveURL(/\/search\?.*q=/);
    await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(page.getByRole('region', { name: '검색 결과' })).toBeVisible();
  });

  test('14. Real API favorites persistence golden', async ({ page }) => {
    test.skip(
      process.env.VITE_USE_MOCK !== 'false',
      'VITE_USE_MOCK=false + Policy API가 준비된 환경에서만 실행합니다.',
    );

    await page.goto('/');
    await waitForHomePolicies(page);

    await page.locator('article.policy-card').first().getByRole('button', {
      name: '북마크 추가',
    }).click();

    await page.getByRole('link', { name: '북마크' }).click();
    await expect(page.locator('article.policy-card').first()).toBeVisible({
      timeout: 15_000,
    });

    await page.reload();
    await expect(page.locator('article.policy-card').first()).toBeVisible({
      timeout: 15_000,
    });
  });
});
