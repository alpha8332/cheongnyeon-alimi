import type { PolicySearchHit } from '../types/policySearch.js';
import type { RecommendationItemDto } from '../types/recommendation.js';

/**
 * Whether detail route should opt in to partial policy data (FE4-21).
 * True when the hit is partial quality or the active search already includes partial.
 */
export function shouldPassIncludePartialOnDetail(
  hit: PolicySearchHit,
  searchIncludePartial: boolean,
): boolean {
  return (
    searchIncludePartial || hit.policy.data_quality_status === 'partial'
  );
}

/** Build detail route for a recommendation hit (FE6-02 / FE5-06). */
export function buildRecommendationItemDetailPath(
  item: RecommendationItemDto,
  options?: { includePartial?: boolean },
): string {
  const includePartial =
    options?.includePartial ?? item.data_quality_status === 'partial';

  return buildProgramDetailRoutePath(item.id, { includePartial });
}

/** Build frontend route `/programs/{id}` with optional `include_partial=true`. */
export function buildProgramDetailRoutePath(
  policyId: number,
  options?: { includePartial?: boolean },
): string {
  if (options?.includePartial) {
    return `/programs/${policyId}?include_partial=true`;
  }

  return `/programs/${policyId}`;
}

/** Build detail route for a Policy Search hit (golden flow result → detail). */
export function buildPolicySearchHitDetailPath(
  hit: PolicySearchHit,
  searchIncludePartial: boolean,
): string {
  return buildProgramDetailRoutePath(hit.policy.id, {
    includePartial: shouldPassIncludePartialOnDetail(hit, searchIncludePartial),
  });
}
