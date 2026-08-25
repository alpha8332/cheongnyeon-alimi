import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { postRecommendations } from '@/api/recommendation';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';
import type { PolicyDto } from '@/types/policy';
import type { RecommendationItemDto } from '@/types/recommendation';
import type { UserSavedConditions } from '@/types/userLocalStorage';
import {
  buildHomeRecommendationRequest,
  HOME_RECOMMENDED_POLICY_LIMIT,
  hasHomeSavedConditions,
  mapHomeRecommendationItemsToPolicies,
  pickHomeFallbackPolicies,
} from '@/utils/homeRecommendedPolicies';
import { buildSavedConditionsKey } from '@/utils/savedConditionsForm';

export interface HomeRecommendedPoliciesState {
  policies: PolicyDto[];
  recommendationItems: RecommendationItemDto[];
  isPersonalized: boolean;
  isLoading: boolean;
}

export function useHomeRecommendedPolicies(
  savedConditions: UserSavedConditions | null,
): HomeRecommendedPoliciesState {
  const isPersonalizedRequest = hasHomeSavedConditions(savedConditions);

  const fallbackQuery = usePoliciesQuery({
    page: 1,
    limit: 12,
    status: 'open',
    include_partial: true,
  });

  const recommendationQuery = useQuery({
    queryKey: [
      'home-recommendations',
      buildSavedConditionsKey(savedConditions),
    ],
    queryFn: () =>
      postRecommendations(
        buildHomeRecommendationRequest(savedConditions as UserSavedConditions),
      ),
    enabled: isPersonalizedRequest,
  });

  return useMemo(() => {
    const fallbackPolicies = pickHomeFallbackPolicies(
      fallbackQuery.data?.items ?? [],
    );

    if (!isPersonalizedRequest) {
      return {
        policies: fallbackPolicies,
        recommendationItems: [],
        isPersonalized: false,
        isLoading: fallbackQuery.isLoading,
      };
    }

    if (recommendationQuery.isLoading) {
      return {
        policies: [],
        recommendationItems: [],
        isPersonalized: true,
        isLoading: true,
      };
    }

    if (recommendationQuery.isError) {
      return {
        policies: fallbackPolicies,
        recommendationItems: [],
        isPersonalized: false,
        isLoading: fallbackQuery.isLoading,
      };
    }

    const recommendationItems = (recommendationQuery.data?.items ?? []).slice(
      0,
      HOME_RECOMMENDED_POLICY_LIMIT,
    );
    return {
      policies: mapHomeRecommendationItemsToPolicies(recommendationItems),
      recommendationItems,
      isPersonalized: true,
      isLoading: false,
    };
  }, [
    fallbackQuery.data?.items,
    fallbackQuery.isLoading,
    isPersonalizedRequest,
    recommendationQuery.data?.items,
    recommendationQuery.isError,
    recommendationQuery.isLoading,
  ]);
}
