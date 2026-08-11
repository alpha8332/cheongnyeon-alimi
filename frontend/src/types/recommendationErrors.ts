/**
 * Recommendation client error presentation types (Frontend 06 / FE6-03).
 */

export type RecommendationClientErrorKind =
  | 'validation'
  | 'bad_request'
  | 'server'
  | 'network'
  | 'empty_results';

export interface RecommendationErrorPresentation {
  kind: RecommendationClientErrorKind;
  title: string;
  message: string;
  retryable: boolean;
}
