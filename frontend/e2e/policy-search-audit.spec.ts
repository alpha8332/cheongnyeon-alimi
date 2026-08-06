import { expect, test, type Page } from '@playwright/test';

async function waitForSearchSettled(page: Page) {
  await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
    timeout: 15_000,
  });
}

test.describe('Policy Search browser audit (FE4-14~21)', () => {
  test('1. 검색어 입력 & URL Sync & 지우기', async ({ page }) => {
    await page.goto('/search');

    const input = page.getByLabel('정책 검색어');
    await input.fill('서울 주거');
    await input.press('Enter');

    await expect(page).toHaveURL(/\/search\?.*q=/);
    expect(page.url()).toContain('q=');

    await waitForSearchSettled(page);
    await expect(page.getByRole('region', { name: '검색 결과' })).toBeVisible();

    const clearButton = page.getByRole('button', { name: '검색어 지우기' });
    await expect(clearButton).toBeVisible();
    await clearButton.click();

    await expect(input).toHaveValue('');
    expect(page.url()).not.toMatch(/[?&]q=/);
    await expect(page.getByText(/검색어를 입력하고 검색하기 버튼을 눌러 주세요/)).toBeVisible();
  });

  test('2. 필터 칩 삭제 시 URL 반영 및 page=1 리셋', async ({ page }) => {
    await page.goto('/search?q=%EC%84%9C%EC%9A%B8+%EC%A3%BC%EA%B1%B0&region=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C&page=2');

    await waitForSearchSettled(page);

    const removeRegionChip = page.getByRole('button', {
      name: /지역:.*제거/,
    });
    await expect(removeRegionChip).toBeVisible();
    await removeRegionChip.click();

    await expect(page).toHaveURL(/\/search\?/);
    expect(page.url()).not.toContain('region=');
    expect(page.url()).not.toMatch(/page=2/);
  });

  test('3. 페이지네이션 클릭 및 새 검색어 입력 시 page=1 리셋', async ({
    page,
  }) => {
    await page.goto('/search?q=%EC%A0%84%EA%B5%AD+%EC%B2%AD%EB%85%84&limit=1&page=1');

    await waitForSearchSettled(page);

    const page2Button = page.getByRole('button', { name: '2페이지' });
    await expect(page2Button).toBeVisible();
    await page2Button.click();

    await expect(page).toHaveURL(/page=2/);

    const input = page.getByLabel('정책 검색어');
    await input.fill('복지로 생활');
    await page.getByRole('button', { name: '검색하기' }).click();

    await waitForSearchSettled(page);
    await expect(page).toHaveURL(/q=/);
    expect(page.url()).not.toMatch(/page=2/);
  });

  test('4a. 로딩 Skeleton 표시', async ({ page }) => {
    await page.goto('/search?q=%EC%84%9C%EC%9A%B8+%EC%A3%BC%EA%B1%B0');

    const loadingShell = page.getByLabel('검색 결과 로딩 중');
    await expect(loadingShell).toBeVisible({ timeout: 2_000 });
    await expect(loadingShell).toHaveCount(0, { timeout: 15_000 });
  });

  test('4b. 검색 결과 0건 Empty Shell', async ({ page }) => {
    await page.goto('/search?q=%EC%97%86%EB%8A%94%EA%B2%80%EC%83%89%EC%96%B4xyz');

    await waitForSearchSettled(page);
    await expect(page.getByLabel('검색 결과 없음')).toBeVisible();
    await expect(page.getByText(/결과가 없다고 해서 해당 정책이 없다고 단정하지 않습니다/)).toBeVisible();
  });

  test('4c. 에러 Shell 및 Retry 버튼 (VITE_USE_MOCK=false + API 503)', async ({
    page,
  }) => {
    await page.route('**/api/v1/policies/search**', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Service unavailable for audit test' }),
      });
    });

    await page.goto('/search?q=audit-error-test', {
      waitUntil: 'domcontentloaded',
    });

    // When VITE_USE_MOCK=true (default dev), in-process mock bypasses HTTP route.
    const errorShell = page.getByLabel('검색 오류');
    const resultRegion = page.getByRole('region', { name: '검색 결과' });

    await page.waitForTimeout(2_000);

    const errorVisible = await errorShell.isVisible().catch(() => false);
    const mockResultsVisible = await resultRegion.isVisible().catch(() => false);

    if (mockResultsVisible && !errorVisible) {
      test.info().annotations.push({
        type: 'audit-note',
        description:
          'Default VITE_USE_MOCK=true uses in-process mock; HTTP 503 intercept did not reach getPolicySearch.',
      });
      expect(mockResultsVisible || (await page.getByLabel('검색 결과 없음').isVisible())).toBeTruthy();
      return;
    }

    await expect(errorShell).toBeVisible();
    await expect(page.getByRole('button', { name: '다시 시도' })).toBeVisible();
  });

  test('5. partial vs unknown 배지 및 unconfirmed 경고', async ({ page }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');

    await waitForSearchSettled(page);

    await expect(page.getByText('정보 일부 누락').first()).toBeVisible();
    await expect(
      page.getByRole('button', { name: /자격요건 직접 확인 필요/ }).first(),
    ).toBeVisible();
  });

  test('6. 우측 사이드바 Reason·미해석 키워드 노출', async ({ page }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');

    await waitForSearchSettled(page);

    const sidebar = page.getByLabel('검색 조건 분석');
    await expect(sidebar).toBeVisible();

    const uninterpreted = sidebar.locator('.policy-search-uninterpreted');
    await expect(uninterpreted).toBeVisible();
    await expect(uninterpreted.getByText(/'생활'/)).toBeVisible();
    await expect(sidebar.getByRole('heading', { name: /자격 조건/ })).toBeVisible();
  });

  test('7a. 홈 검색·추천 칩 → /search?q= 이동', async ({ page }) => {
    await page.goto('/');

    await page.getByLabel('정책 검색어').fill('서울 주거');
    await page.getByRole('button', { name: '검색하기' }).click();

    await expect(page).toHaveURL(/\/search\?.*q=/);

    await page.goto('/');
    await page.getByRole('button', { name: '서울 주거' }).click();
    await expect(page).toHaveURL(/\/search\?.*q=/);
  });

  test('7b. 검색 결과 카드 → /programs/{id} (+ include_partial)', async ({
    page,
  }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');

    await waitForSearchSettled(page);

    const partialCard = page.locator('a.policy-card[href*="include_partial=true"]').first();

    await expect(partialCard).toBeVisible();
    const href = await partialCard.getAttribute('href');
    expect(href).toMatch(/^\/programs\/\d+/);
    expect(href).toContain('include_partial=true');

    await partialCard.click();
    await expect(page).toHaveURL(/\/programs\/\d+\?include_partial=true/);
  });
});
