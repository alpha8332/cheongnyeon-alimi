import type { PolicyDto } from '../types/policy.js';
import {
  getPolicyDeadlineInfo,
  isImminentDeadline,
} from './policyDeadline.js';

export interface FavoriteDeadlineAlert {
  policyId: number;
  title: string;
  applicationEnd: string;
  daysRemaining: number;
  label: string;
}

export function buildFavoriteDeadlineAlerts(
  policies: readonly PolicyDto[],
  favoriteIds: readonly number[],
  referenceDate: Date = new Date(),
  imminentWithinDays = 7,
): FavoriteDeadlineAlert[] {
  const favoriteSet = new Set(favoriteIds);
  const alerts: FavoriteDeadlineAlert[] = [];

  for (const policy of policies) {
    if (!favoriteSet.has(policy.id)) {
      continue;
    }

    if (!isImminentDeadline(policy, imminentWithinDays, referenceDate)) {
      continue;
    }

    const info = getPolicyDeadlineInfo(policy, referenceDate);
    if (!info.applicationEnd || info.daysRemaining === null) {
      continue;
    }

    alerts.push({
      policyId: policy.id,
      title: policy.title,
      applicationEnd: info.applicationEnd,
      daysRemaining: info.daysRemaining,
      label: info.label,
    });
  }

  return alerts.sort((left, right) => {
    if (left.daysRemaining !== right.daysRemaining) {
      return left.daysRemaining - right.daysRemaining;
    }

    return left.policyId - right.policyId;
  });
}
