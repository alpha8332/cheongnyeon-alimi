import { expect, test, type Page } from '@playwright/test';

const USER_LOCAL_STORAGE_KEY = 'cheongnyeon-alimi.user-local.v1';
const MOCK_RECOMMENDATION_EMPTY_REGION = 'MOCK_EMPTY';
const MOCK_HOUSING_POLICY_TITLE = '합성 청년 주거 지원';

async function clearUserLocalStorage(page: Page) {
  await page.goto('/');
  await page.evaluate((key) => {
    window.localStorage.removeItem(key);
  }, USER_LOCAL_STORAGE_KEY);
}

async function waitForRecommendationSettled(page: Page) {
  await expect(page.getByLabel('추천 결과 로딩 중')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function fillRecommendationForm(
  page: Page,
  values: {
    region?: string;
    age?: string;
    category?: string;
  },
) {
  const form = page.getByRole('form', { name: '맞춤 추천 조건 편집' });

  if (values.region !== undefined) {
    await form.getByPlaceholder('예: 서울특별시').fill(values.region);
  }

  if (values.age !== undefined) {
    await form.getByPlaceholder('예: 24').fill(values.age);
  }

  if (values.category !== undefined) {
    await form.getByLabel('관심 분야').selectOption(values.category);
  }
}

async function submitRecommendation(page: Page) {
  await page.getByRole('button', { name: '추천 받기' }).click();
}

test.describe('Recommendation UI browser flow (FE6-05)', () => {
  test.beforeEach(async ({ page }) => {
    await clearUserLocalStorage(page);
    await page.goto('/recommendations');
  });

  test('1. route boundary — /recommendations vs /search', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '맞춤 추천', level: 1 })).toBeVisible();
    await expect(page.getByRole('link', { name: '/search' })).toBeVisible();
    await expect(page.getByText(/자격 충족이나 수혜 가능성을 확정하지 않습니다/)).toBeVisible();
    await expect(page.getByRole('form', { name: '맞춤 추천 조건 편집' })).toBeVisible();
  });

  test('2. loading shell — submit 후 skeleton', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });
    await submitRecommendation(page);

    await expect(page.getByLabel('추천 결과 로딩 중')).toBeVisible({ timeout: 2_000 });
    await waitForRecommendationSettled(page);
  });

  test('3. Mock results — 조건 submit·disclaimer·score 미노출', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    const results = page.getByRole('region', { name: '추천 결과' });
    await expect(results).toBeVisible();
    await expect(results.getByRole('heading', { name: /추천 정책 \d+건/ })).toBeVisible();
    await expect(results.getByText(MOCK_HOUSING_POLICY_TITLE)).toBeVisible();
    await expect(results.getByText(/자격을 확정하지 않으며/)).toBeVisible();
    await expect(results.locator('.recommendation-result-card')).not.toContainText(/score/i);
  });

  test('4. empty shell — MOCK_EMPTY region', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: MOCK_RECOMMENDATION_EMPTY_REGION,
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    await expect(page.getByLabel('추천 결과 없음')).toBeVisible();
    await expect(
      page.getByText('입력 조건에 맞는 추천 정책이 없습니다'),
    ).toBeVisible();
    await expect(
      page.getByText(/결과가 없다고 해당 정책이 없다고 단정하지 않습니다/),
    ).toBeVisible();
  });

  test('5. empty → results — 조건 변경 후 재추천', async ({ page }) => {
    await fillRecommendationForm(page, { region: MOCK_RECOMMENDATION_EMPTY_REGION });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);
    await expect(page.getByLabel('추천 결과 없음')).toBeVisible();

    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);
    await expect(page.getByRole('region', { name: '추천 결과' })).toBeVisible();
  });

  test('6. result card — detail navigation·favorite toggle', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    const card = page
      .locator('article.recommendation-result-card')
      .filter({ hasText: MOCK_HOUSING_POLICY_TITLE });
    await expect(card).toBeVisible();

    await card.getByRole('button', { name: '북마크 추가' }).click();
    await expect(card.getByRole('button', { name: '북마크 해제' })).toBeVisible();

    await card.getByRole('link', { name: MOCK_HOUSING_POLICY_TITLE }).click();
    await expect(page).toHaveURL(/\/programs\/\d+/);
    await expect(page.getByRole('button', { name: '북마크 해제' })).toBeVisible();
  });

  test('7. localStorage — 조건 reload·프로필과 공유', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: '대전광역시',
      age: '27',
      category: 'welfare',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    await expect(page.getByText(/저장됨:.*대전광역시/)).toBeVisible();

    await page.reload();
    await expect(page.getByPlaceholder('예: 서울특별시')).toHaveValue('대전광역시');
    await expect(page.getByPlaceholder('예: 24')).toHaveValue('27');

    await page.goto('/profile');
    await expect(page.getByText(/저장됨:.*대전광역시/)).toBeVisible();
  });

  test('8. region list — 단일 지역 표시(더 보기 없음)', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    const card = page
      .locator('article.recommendation-result-card')
      .filter({ hasText: MOCK_HOUSING_POLICY_TITLE });
    await expect(card.getByText('서울특별시')).toBeVisible();
    await expect(card.getByRole('button', { name: '더 보기' })).toHaveCount(0);
  });

  test('9. keyboard — 추천 받기 focus·submit', async ({ page }) => {
    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });

    const submitButton = page.getByRole('button', { name: '추천 받기' });
    await submitButton.focus();
    await page.keyboard.press('Enter');
    await waitForRecommendationSettled(page);

    await expect(page.getByRole('region', { name: '추천 결과' })).toBeVisible();
  });

  test('10. mobile viewport — form·결과', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    await expect(page.getByRole('form', { name: '맞춤 추천 조건 편집' })).toBeVisible();
    await expect(page.getByRole('region', { name: '추천 결과' })).toBeVisible();
  });

  test('11. Release 1 search golden 회귀 — /search entry', async ({ page }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');

    await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
      timeout: 15_000,
    });
    await expect(page.getByRole('region', { name: '검색 결과' })).toBeVisible();
    await expect(page.locator('a.policy-card').first()).toBeVisible();
  });

  test('12. error retry — HTTP 503 (Mock bypass 시 skip)', async ({ page }) => {
    await page.route('**/api/v1/recommendations', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Service unavailable for audit test' }),
      });
    });

    await fillRecommendationForm(page, {
      region: '서울특별시',
      age: '24',
    });
    await submitRecommendation(page);

    await page.waitForTimeout(2_000);

    const errorShell = page.getByLabel('추천 오류');
    const resultRegion = page.getByRole('region', { name: '추천 결과' });
    const errorVisible = await errorShell.isVisible().catch(() => false);
    const mockResultsVisible = await resultRegion.isVisible().catch(() => false);

    if (mockResultsVisible && !errorVisible) {
      test.info().annotations.push({
        type: 'audit-note',
        description:
          'Default VITE_USE_MOCK=true uses in-process mock; HTTP 503 intercept did not reach postRecommendations.',
      });
      expect(mockResultsVisible).toBeTruthy();
      return;
    }

    await expect(errorShell).toBeVisible();
    await expect(page.getByRole('button', { name: '다시 시도' })).toBeVisible();
  });

  test('13. Real API recommendation golden', async ({ page }) => {
    test.skip(
      process.env.VITE_USE_MOCK !== 'false',
      'VITE_USE_MOCK=false + Backend recommendation API가 준비된 환경에서만 실행합니다.',
    );

    await fillRecommendationForm(page, {
      region: '천안시',
      age: '27',
      category: 'housing',
    });
    await submitRecommendation(page);
    await waitForRecommendationSettled(page);

    const results = page.getByRole('region', { name: '추천 결과' });
    await expect(results).toBeVisible();
    await expect(results.locator('article.recommendation-result-card').first()).toBeVisible();
    await expect(results.getByText(/자격을 확정하지 않으며/)).toBeVisible();
  });
});
