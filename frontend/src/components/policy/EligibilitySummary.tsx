import type {
  EligibilityConditionDto,
  EligibilityDocumentDto,
  EligibilityEvidenceDto,
  EligibilitySummaryDto,
  InstitutionalContactDto,
} from '@/types/policy';
import {
  ELIGIBILITY_CATEGORY_LABELS,
  ELIGIBILITY_COVERAGE_LABELS,
  ELIGIBILITY_COVERAGE_MESSAGES,
  getInstitutionalContactActionLabel,
  getInstitutionalContactHref,
  getPublicHttpUrl,
} from '@/utils/eligibilitySummary';
import { formatCollectedAt } from '@/utils/policyDisplay';
import './EligibilitySummary.css';

interface EvidenceListProps {
  evidence: EligibilityEvidenceDto[];
}

function EvidenceList({ evidence }: EvidenceListProps) {
  return (
    <ul className="eligibility-evidence" aria-label="출처 근거">
      {evidence.map((item, index) => {
        const sourceUrl = getPublicHttpUrl(item.source_url);
        return (
          <li
            key={`${item.source_id}-${item.source_url}-${item.locator}-${item.collected_at}`}
            className="eligibility-evidence__item"
          >
            {sourceUrl ? (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="eligibility-evidence__link"
              >
                근거 {index + 1} 원문 열기
              </a>
            ) : (
              <span className="eligibility-evidence__unavailable">
                근거 {index + 1} 링크 확인 불가
              </span>
            )}
            <span className="eligibility-evidence__meta">
              {item.source_id} · {formatCollectedAt(item.collected_at)} ·{' '}
              {item.locator}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

interface ConditionSectionProps {
  id: string;
  title: string;
  emptyMessage: string;
  items: EligibilityConditionDto[];
  tone?: 'default' | 'danger' | 'warning';
}

function ConditionSection({
  id,
  title,
  emptyMessage,
  items,
  tone = 'default',
}: ConditionSectionProps) {
  return (
    <section
      className={`eligibility-group eligibility-group--${tone}`}
      aria-labelledby={id}
    >
      <h3 id={id} className="eligibility-group__title">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="eligibility-group__empty">{emptyMessage}</p>
      ) : (
        <ul className="eligibility-items">
          {items.map((item, index) => (
            <li
              key={`${item.category}-${item.text}-${index}`}
              className="eligibility-items__item"
            >
              <span className="eligibility-items__category">
                {ELIGIBILITY_CATEGORY_LABELS[item.category]}
              </span>
              <p className="eligibility-items__text">{item.text}</p>
              <EvidenceList evidence={item.evidence} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function DocumentSection({ items }: { items: EligibilityDocumentDto[] }) {
  return (
    <section
      className="eligibility-group"
      aria-labelledby="eligibility-documents-title"
    >
      <h3
        id="eligibility-documents-title"
        className="eligibility-group__title"
      >
        필요 서류
      </h3>
      {items.length === 0 ? (
        <p className="eligibility-group__empty">
          공식 원문에서 구조화된 필요 서류를 확인하지 못했습니다.
        </p>
      ) : (
        <ul className="eligibility-items">
          {items.map((item, index) => (
            <li
              key={`${item.text}-${index}`}
              className="eligibility-items__item"
            >
              <p className="eligibility-items__text">{item.text}</p>
              <EvidenceList evidence={item.evidence} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ContactValue({ contact }: { contact: InstitutionalContactDto }) {
  const href = getInstitutionalContactHref(contact);
  if (!href) {
    return <span className="eligibility-contact__value">{contact.value}</span>;
  }

  return (
    <a
      href={href}
      className="eligibility-contact__action"
      {...(contact.kind === 'official_channel'
        ? { target: '_blank', rel: 'noopener noreferrer' }
        : {})}
      aria-label={`${contact.label} ${contact.value} ${getInstitutionalContactActionLabel(contact)}`}
    >
      {contact.value}
      <span aria-hidden="true">
        {' '}
        · {getInstitutionalContactActionLabel(contact)}
      </span>
    </a>
  );
}

function ContactSection({ items }: { items: InstitutionalContactDto[] }) {
  return (
    <section
      className="eligibility-group eligibility-group--contact"
      aria-labelledby="eligibility-contacts-title"
    >
      <h3
        id="eligibility-contacts-title"
        className="eligibility-group__title"
      >
        문의처
      </h3>
      {items.length === 0 ? (
        <p className="eligibility-group__empty">
          공개된 시설 문의처를 확인하지 못했습니다.
        </p>
      ) : (
        <ul className="eligibility-items">
          {items.map((contact, index) => (
            <li
              key={`${contact.kind}-${contact.label}-${contact.value}-${index}`}
              className="eligibility-items__item"
            >
              <p className="eligibility-contact__label">{contact.label}</p>
              <ContactValue contact={contact} />
              <EvidenceList evidence={contact.evidence} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function EligibilitySummary({
  summary,
}: {
  summary: EligibilitySummaryDto;
}) {
  return (
    <section
      className="eligibility-summary panel"
      aria-labelledby="eligibility-summary-title"
      data-coverage={summary.coverage}
    >
      <div className="eligibility-summary__header">
        <div>
          <p className="eligibility-summary__eyebrow">공식 원문 기반</p>
          <h2 id="eligibility-summary-title">핵심 신청 조건</h2>
        </div>
        <span className="eligibility-summary__coverage">
          {ELIGIBILITY_COVERAGE_LABELS[summary.coverage]}
        </span>
      </div>

      <p className="eligibility-summary__notice" role="note">
        {ELIGIBILITY_COVERAGE_MESSAGES[summary.coverage]} 이 정보는 실제 자격
        충족이나 선정을 확정하지 않습니다.
      </p>

      <div className="eligibility-summary__grid">
        <ConditionSection
          id="eligibility-requirements-title"
          title="신청 조건"
          emptyMessage="공식 원문에서 구조화된 신청 조건을 확인하지 못했습니다."
          items={summary.requirements}
        />
        <ConditionSection
          id="eligibility-exclusions-title"
          title="제외 조건"
          emptyMessage="공식 원문에서 구조화된 제외 조건을 확인하지 못했습니다."
          items={summary.exclusions}
          tone="danger"
        />
        <ConditionSection
          id="eligibility-preferences-title"
          title="우대 조건"
          emptyMessage="공식 원문에서 구조화된 우대 조건을 확인하지 못했습니다."
          items={summary.preferences}
        />
        <DocumentSection items={summary.documents} />
        <ConditionSection
          id="eligibility-unknowns-title"
          title="추가 확인 필요"
          emptyMessage="별도로 분류된 확인 필요 조건이 없습니다."
          items={summary.unknowns}
          tone="warning"
        />
        <ContactSection items={summary.institutional_contacts} />
      </div>
    </section>
  );
}
