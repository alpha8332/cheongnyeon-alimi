/**
 * Policy Search client error presentation types (Frontend 04).
 *
 * HTTP status → UI mapping tables live in the Forest plan (§ Error UX).
 * mapHttpStatus helpers: {@link ../utils/policySearchErrors.ts} (FE4-15).
 */

/** Client-side search error categories for Empty/Error state components. */
export type PolicySearchClientErrorKind =
  | 'empty_query'
  | 'empty_results'
  | 'bad_request'
  | 'not_found'
  | 'validation'
  | 'server'
  | 'network';

/** Presentation shape for LoadingState / EmptyState / ErrorState. */
export interface PolicySearchErrorPresentation {
  kind: PolicySearchClientErrorKind;
  title: string;
  message: string;
  retryable: boolean;
  /** When true, keep visible filter chips for user edit after error. */
  preserve_filter_chips: boolean;
}

/**
 * Reason-code copy fallback plan (documented in Forest plan § Reason fallback):
 * - Known codes may map to localized labels in FE4-19 UI.
 * - Unknown `reason_code` values must render Backend-provided `message` without throwing.
 */
