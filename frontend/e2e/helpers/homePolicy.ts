import { expect, type Page } from '@playwright/test';

export async function waitForHomePolicies(page: Page) {
  await expect(page.getByText('정책을 불러오는 중입니다.')).toHaveCount(0, {
    timeout: 15_000,
  });
  await expect(page.locator('article.policy-card').first()).toBeVisible();
}

/** 홈 featured 첫 카드 제목(링크 텍스트) */
export async function getFirstHomePolicyTitle(page: Page): Promise<string> {
  await waitForHomePolicies(page);
  const titleLink = page.locator('article.policy-card').first().locator('.policy-card__title a');
  const title = (await titleLink.innerText()).trim();
  expect(title.length).toBeGreaterThan(0);
  return title;
}

export async function confirmBookmarkModal(page: Page) {
  const dialog = page.getByRole('dialog', { name: '북마크 저장' });
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: '저장' }).click();
  await expect(dialog).toHaveCount(0);
}

/** Mock title 고정 또는 actual API에서 홈 첫 카드 */
export async function favoritePolicyOnHome(
  page: Page,
  mockTitle?: string,
): Promise<string> {
  const title = mockTitle ?? (await getFirstHomePolicyTitle(page));
  await waitForHomePolicies(page);

  const card = mockTitle
    ? page.locator('article.policy-card').filter({ hasText: mockTitle })
    : page.locator('article.policy-card').first();

  await expect(card).toBeVisible();
  await card.getByRole('button', { name: '북마크 추가' }).click();
  await confirmBookmarkModal(page);
  await expect(card.getByRole('button', { name: '북마크 폴더 관리' })).toBeVisible();
  return title;
}
