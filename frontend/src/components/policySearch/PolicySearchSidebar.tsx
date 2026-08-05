import type { PolicySearchHit, PolicySearchResponse } from '@/types/policySearch';
import SearchReasonBlock from '@/components/policySearch/SearchReasonBlock';
import UnconfirmedBanner from '@/components/policySearch/UnconfirmedBanner';
import UninterpretedNotice from '@/components/policySearch/UninterpretedNotice';
import {
  buildConditionAnalysisRows,
  buildQueryLevelWarnings,
  buildUninterpretedNotices,
  hasQueryLevelWarnings,
  resolvePolicySearchReasonMessage,
} from '@/utils/policySearchReason';
import './PolicySearchSidebar.css';

interface PolicySearchSidebarProps {
  response: PolicySearchResponse | null | undefined;
  selectedHit: PolicySearchHit | null | undefined;
}

export default function PolicySearchSidebar({
  response,
  selectedHit,
}: PolicySearchSidebarProps) {
  const interpreted = response?.interpreted_conditions;
  const analysisRows = buildConditionAnalysisRows(interpreted, selectedHit);
  const reasonMessage = resolvePolicySearchReasonMessage(selectedHit ?? null);
  const uninterpretedNotices = buildUninterpretedNotices(interpreted);
  const queryWarnings = hasQueryLevelWarnings(interpreted)
    ? buildQueryLevelWarnings(interpreted)
    : [];

  return (
    <aside className="policy-search-sidebar" aria-label="검색 조건 분석">
      <SearchReasonBlock
        rows={analysisRows}
        reasonMessage={reasonMessage}
        selectedTitle={selectedHit?.policy.title ?? null}
      />

      {queryWarnings.length > 0 ? (
        <UnconfirmedBanner warnings={queryWarnings} />
      ) : null}

      {uninterpretedNotices.length > 0 ? (
        <UninterpretedNotice notices={uninterpretedNotices} />
      ) : null}
    </aside>
  );
}
