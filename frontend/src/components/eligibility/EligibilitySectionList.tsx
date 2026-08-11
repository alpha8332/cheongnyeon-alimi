import { useState, type ReactNode } from 'react';
import EligibilityComparisonBadge from '@/components/eligibility/EligibilityComparisonBadge';
import EligibilityEvidenceLink from '@/components/eligibility/EligibilityEvidenceLink';
import type {
  EligibilitySummaryDto,
  ItemConditionDto,
  ItemDocumentDto,
} from '@/types/eligibilitySummary';
import type { PolicyDto } from '@/types/policy';
import type { UserSavedConditions } from '@/types/userLocalStorage';
import {
  compareEligibilityCondition,
  hasSavedConditionsForComparison,
} from '@/utils/eligibilityComparison';
import {
  getEligibilityCategoryLabel,
  shouldExpandEligibilityText,
  truncateEligibilityText,
} from '@/utils/eligibilitySummaryDisplay';

interface EligibilitySectionListProps {
  summary: EligibilitySummaryDto;
  policy: PolicyDto;
  savedConditions: UserSavedConditions | null;
}

function ExpandableText({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const canExpand = shouldExpandEligibilityText(text);
  const displayText =
    expanded || !canExpand ? text : truncateEligibilityText(text);

  return (
    <div className="eligibility-section-list__text-block">
      <p className="eligibility-section-list__content">{displayText}</p>
      {canExpand ? (
        <button
          type="button"
          className="eligibility-section-list__expand-btn"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? '접기' : '더 보기'}
        </button>
      ) : null}
    </div>
  );
}

function ConditionItems({
  items,
  policy,
  savedConditions,
}: {
  items: ItemConditionDto[];
  policy: PolicyDto;
  savedConditions: UserSavedConditions | null;
}) {
  const showComparison = hasSavedConditionsForComparison(savedConditions);

  return (
    <ul className="eligibility-section-list__items">
      {items.map((item, index) => {
        const comparisonStatus =
          showComparison && savedConditions
            ? compareEligibilityCondition(item, policy, savedConditions)
            : null;

        return (
          <li
            key={`${item.category}-${index}`}
            className="eligibility-section-list__item"
          >
            <div className="eligibility-section-list__item-head">
              <span className="eligibility-section-list__category-badge">
                {getEligibilityCategoryLabel(item.category)}
              </span>
              {comparisonStatus ? (
                <EligibilityComparisonBadge status={comparisonStatus} />
              ) : null}
            </div>
            <ExpandableText text={item.content} />
            <EligibilityEvidenceLink evidence={item.evidence} />
          </li>
        );
      })}
    </ul>
  );
}

function DocumentItems({ items }: { items: ItemDocumentDto[] }) {
  return (
    <ul className="eligibility-section-list__items">
      {items.map((item, index) => (
        <li key={`${item.name}-${index}`} className="eligibility-section-list__item">
          <div className="eligibility-section-list__item-head">
            <strong className="eligibility-section-list__document-name">
              {item.name}
            </strong>
          </div>
          {item.content ? <ExpandableText text={item.content} /> : null}
          <EligibilityEvidenceLink evidence={item.evidence} />
        </li>
      ))}
    </ul>
  );
}

function UnknownConditionItems({ items }: { items: string[] }) {
  return (
    <ul className="eligibility-section-list__items">
      {items.map((item, index) => (
        <li key={`unknown-${index}`} className="eligibility-section-list__item">
          <ExpandableText text={item} />
        </li>
      ))}
    </ul>
  );
}

function SectionBlock({
  title,
  children,
  isEmpty,
}: {
  title: string;
  children: ReactNode;
  isEmpty?: boolean;
}) {
  if (isEmpty) {
    return null;
  }

  return (
    <section className="eligibility-section-list__section">
      <h3 className="eligibility-section-list__section-title">{title}</h3>
      {children}
    </section>
  );
}

export default function EligibilitySectionList({
  summary,
  policy,
  savedConditions,
}: EligibilitySectionListProps) {
  return (
    <div className="eligibility-section-list">
      <SectionBlock
        title="필수 조건"
        isEmpty={summary.requirements.length === 0}
      >
        <ConditionItems
          items={summary.requirements}
          policy={policy}
          savedConditions={savedConditions}
        />
      </SectionBlock>

      <SectionBlock title="제외 조건" isEmpty={summary.exclusions.length === 0}>
        <ConditionItems
          items={summary.exclusions}
          policy={policy}
          savedConditions={savedConditions}
        />
      </SectionBlock>

      <SectionBlock title="우대 조건" isEmpty={summary.preferences.length === 0}>
        <ConditionItems
          items={summary.preferences}
          policy={policy}
          savedConditions={savedConditions}
        />
      </SectionBlock>

      <SectionBlock
        title="제출 서류"
        isEmpty={summary.required_documents.length === 0}
      >
        <DocumentItems items={summary.required_documents} />
      </SectionBlock>

      <SectionBlock
        title="확인 필요"
        isEmpty={summary.unknown_conditions.length === 0}
      >
        <UnknownConditionItems items={summary.unknown_conditions} />
      </SectionBlock>
    </div>
  );
}
