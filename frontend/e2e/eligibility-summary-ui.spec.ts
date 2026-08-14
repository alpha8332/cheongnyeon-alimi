import { expect, test, type Page } from '@playwright/test';

const USER_LOCAL_STORAGE_KEY = 'cheongnyeon-alimi.user-local.v1';

const MOCK_COMPLETE_POLICY_ID = 9101;
const MOCK_PARTIAL_POLICY_ID = 9102;
const MOCK_UNKNOWN_POLICY_ID = 9103;
const MOCK_COMPLETE_POLICY_TITLE = 'Mock Complete Eligibility Policy';
const MOCK_PARTIAL_POLICY_TITLE = 'Mock Partial Eligibility Policy';
const MOCK_UNKNOWN_POLICY_TITLE = 'Mock Unknown Eligibility Policy';

async function clearUserLocalStorage(page: Page) {
  await page.goto('/');
  await page.evaluate((key) => {
    window.localStorage.removeItem(key);
  }, USER_LOCAL_STORAGE_KEY);
}

async function saveConditionsOnHome(
  page: Page,
  values: { region: string; age: string; category: string },
) {
  await page.goto('/');

  const form = page.getByRole('form', { name: '저장 조건 편집' });
  await form.getByPlaceholder('예: 서울특별시').fill(values.region);
  await form.getByPlaceholder('예: 24').fill(values.age);
  await form.getByLabel('관심 분야').selectOption(values.category);
  await form.getByRole('button', { name: '조건 저장' }).click();

  await expect(page.getByText('저장 조건을 브라우저에 저장했습니다.')).toBeVisible();
}

async function waitForProgramDetailSettled(page: Page) {
  await expect(page.getByText('정책 상세를 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
}

async function waitForSearchSettled(page: Page) {
  await expect(page.getByLabel('검색 결과 로딩 중')).toHaveCount(0, {
    timeout: 15_000,
  });
}

function eligibilityCard(page: Page) {
  return page.locator('article.eligibility-summary-card');
}

test.describe('Eligibility Summary browser flow (FE7-05)', () => {
  test.beforeEach(async ({ page }) => {
    await clearUserLocalStorage(page);
  });

  test('1. complete fixture — sections·status·evidence·non-definitive copy', async ({
    page,
  }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_COMPLETE_POLICY_TITLE }),
    ).toBeVisible();

    const card = eligibilityCard(page);
    await expect(card.getByRole('heading', { name: '핵심 신청 조건', level: 2 })).toBeVisible();
    await expect(card.getByText('구조화 완료')).toBeVisible();

    await expect(card.getByRole('heading', { name: '필수 조건', level: 3 })).toBeVisible();
    await expect(card.getByRole('heading', { name: '제외 조건', level: 3 })).toBeVisible();
    await expect(card.getByRole('heading', { name: '우대 조건', level: 3 })).toBeVisible();
    await expect(card.getByRole('heading', { name: '제출 서류', level: 3 })).toBeVisible();
    await expect(card.getByRole('heading', { name: '확인 필요', level: 3 })).toHaveCount(0);

    await expect(card.getByText('만 19세 이상 34세 이하 청년')).toBeVisible();
    await expect(card.getByRole('link', { name: '원문 근거 보기' }).first()).toBeVisible();
    await expect(card.getByText('출처 youthcenter').first()).toBeVisible();

    await expect(card.getByRole('region', { name: '기관 연락처' })).toBeVisible();
    await expect(card.getByText('청년주거 상담')).toBeVisible();

    await expect(card.getByRole('button', { name: '공식 원문 확인' })).toBeVisible();
    await expect(card.getByRole('note')).toContainText(
      '최종 신청 가능 여부를 확정하지 않습니다',
    );
    await expect(card.getByText('신청 가능', { exact: true })).toHaveCount(0);
  });

  test('2. partial fixture — banner·unknown section·missing evidence copy', async ({
    page,
  }) => {
    await page.goto(`/programs/${MOCK_PARTIAL_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_PARTIAL_POLICY_TITLE }),
    ).toBeVisible();

    const card = eligibilityCard(page);
    await expect(card.getByText('일부 확인 필요')).toBeVisible();
    await expect(card.getByRole('note').first()).toContainText(
      '신청 가능 여부를 단정하지 않습니다',
    );

    await expect(card.getByRole('heading', { name: '확인 필요', level: 3 })).toBeVisible();
    await expect(
      card.getByText('가구 단위 소득·재산 기준은 원문 표와 기준연도 확인 필요'),
    ).toBeVisible();

    await expect(
      card.getByText('원문 근거가 없어 추가 확인이 필요합니다.').first(),
    ).toBeVisible();
  });

  test('3. unknown fixture — banner·unknown conditions·empty structured sections', async ({
    page,
  }) => {
    await page.goto(`/programs/${MOCK_UNKNOWN_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(
      page.getByRole('heading', { name: MOCK_UNKNOWN_POLICY_TITLE }),
    ).toBeVisible();

    const card = eligibilityCard(page);
    await expect(card.getByText('구조화 불가')).toBeVisible();
    await expect(card.getByRole('note').first()).toContainText(
      '자격요건을 구조화할 수 없습니다',
    );

    await expect(card.getByRole('heading', { name: '필수 조건', level: 3 })).toHaveCount(0);
    await expect(card.getByRole('heading', { name: '확인 필요', level: 3 })).toBeVisible();
    await expect(
      card.getByText('원문에 자격요건 상세가 없어 구조화할 수 없음'),
    ).toBeVisible();
  });

  test('4. seed policy without summary — empty state', async ({ page }) => {
    await page.goto('/programs/1');
    await waitForProgramDetailSettled(page);

    await expect(page.getByText('구조화된 핵심 신청 조건이 아직 제공되지 않습니다.')).toBeVisible();
    await expect(eligibilityCard(page)).toHaveCount(0);
  });

  test('5. saved conditions — comparison badges on complete fixture', async ({ page }) => {
    await saveConditionsOnHome(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });

    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    await expect(card.getByText('저장된 관심 분야')).toBeVisible();
    await expect(card.getByText('조건상 일치').first()).toBeVisible();
    await expect(card.getByText('조건상 불일치')).toHaveCount(0);
  });

  test('6. partial fixture + saved conditions — needs_review badge coexistence', async ({
    page,
  }) => {
    await saveConditionsOnHome(page, {
      region: '서울특별시',
      age: '24',
      category: 'housing',
    });

    await page.goto(`/programs/${MOCK_PARTIAL_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    await expect(card.getByText('조건상 일치').first()).toBeVisible();
    await expect(card.getByText('추가 확인 필요').first()).toBeVisible();
  });

  test('7. evidence links — rel noopener noreferrer', async ({ page }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const evidenceLinks = page.getByRole('link', { name: '원문 근거 보기' });
    await expect(evidenceLinks.first()).toHaveAttribute('rel', 'noopener noreferrer');
    await expect(evidenceLinks.first()).toHaveAttribute('target', '_blank');
  });

  test('8. keyboard — evidence link focus', async ({ page }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const evidenceLink = page.getByRole('link', { name: '원문 근거 보기' }).first();
    await evidenceLink.focus();
    await expect(evidenceLink).toBeFocused();
  });

  test('9. mobile viewport — complete fixture card layout', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    await expect(card.getByRole('heading', { name: '핵심 신청 조건', level: 2 })).toBeVisible();
    await expect(card.getByRole('button', { name: '공식 원문 확인' })).toBeVisible();
  });

  test('10. Release 1 search golden 회귀 — /search entry', async ({ page }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');

    await waitForSearchSettled(page);
    await expect(page.getByRole('region', { name: '검색 결과' })).toBeVisible();
    await expect(page.locator('a.policy-card').first()).toBeVisible();
  });

  test('11. search → detail navigation regression', async ({ page }) => {
    await page.goto('/search?q=%EB%B3%B5%EC%A7%80%EB%A1%9C+%EC%83%9D%ED%99%9C');
    await waitForSearchSettled(page);

    await page.locator('a.policy-card').first().click();
    await expect(page).toHaveURL(/\/programs\/\d+/);
    await waitForProgramDetailSettled(page);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText('📄 정책 정보')).toBeVisible();
  });

  test('12. golden policy detail — mock complete fixture envelope', async ({ page }) => {
    await page.goto(`/programs/${MOCK_COMPLETE_POLICY_ID}`);
    await waitForProgramDetailSettled(page);

    await expect(page.getByText('데이터 출처')).toBeVisible();
    await expect(page.getByText('Mock Eligibility Fixture')).toBeVisible();
    await expect(page.getByText('수집 시각')).toBeVisible();
    await expect(eligibilityCard(page)).toBeVisible();
    await expect(page.locator('.policy-eligibility-notice')).toContainText(
      '실제 자격 충족을 확정하지 않습니다',
    );
  });

  test('13. Real API eligibility detail golden', async ({ page }) => {
    test.skip(
      process.env.VITE_USE_MOCK !== 'false',
      'VITE_USE_MOCK=false + Backend eligibility summary API가 준비된 환경에서만 실행합니다.',
    );

    await page.goto(
      '/search?q=%EC%B2%9C%EC%95%88+%EC%82%AC%EB%8A%94+27%EC%82%B4+%EC%B2%AD%EB%85%84+%EB%8B%A8%EA%B8%B0%EC%88%99%EC%86%8C+%EC%A7%80%EC%9B%90+%EB%B0%9B%EC%9D%84+%EC%88%98+%EC%9E%88%EB%82%98%3F',
    );
    await waitForSearchSettled(page);

    await page.getByRole('region', { name: '검색 결과' }).locator('a.policy-card').first().click();
    await waitForProgramDetailSettled(page);

    const card = eligibilityCard(page);
    const emptySummary = page.getByText(
      '구조화된 핵심 신청 조건이 아직 제공되지 않습니다.',
    );
    const cardVisible = await card.isVisible().catch(() => false);
    const emptyVisible = await emptySummary.isVisible().catch(() => false);

    expect(cardVisible || emptyVisible).toBeTruthy();

    if (cardVisible) {
      await expect(card.getByRole('heading', { name: '핵심 신청 조건', level: 2 })).toBeVisible();
      await expect(card.getByRole('button', { name: '공식 원문 확인' })).toBeVisible();
      await expect(card.getByRole('note')).toContainText(
        '최종 신청 가능 여부를 확정하지 않습니다',
      );
    }
  });
});
