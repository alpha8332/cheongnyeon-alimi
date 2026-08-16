import type { ReactNode } from 'react';
import { splitPolicyTextToItems } from '@/utils/policyDetailContent';

interface PolicyDetailTextContentProps {
  text: string | null | undefined;
  fallback: string;
  preferOrdered?: boolean;
}

export default function PolicyDetailTextContent({
  text,
  fallback,
  preferOrdered = false,
}: PolicyDetailTextContentProps) {
  const { items, ordered } = splitPolicyTextToItems(text);
  const useOrdered = ordered || (preferOrdered && items.length >= 2);

  if (items.length === 0) {
    return <p className="policy-detail-text policy-detail-text--empty">{fallback}</p>;
  }

  if (items.length === 1) {
    return <p className="policy-detail-text">{items[0]}</p>;
  }

  if (useOrdered) {
    return (
      <ol className="policy-detail-text-list policy-detail-text-list--ordered">
        {items.map((item, index) => (
          <li key={`${index}-${item}`} className="policy-detail-text-list__item">
            {item}
          </li>
        ))}
      </ol>
    );
  }

  return (
    <ul className="policy-detail-text-list">
      {items.map((item) => (
        <li key={item} className="policy-detail-text-list__item">
          {item}
        </li>
      ))}
    </ul>
  );
}

interface PolicyDetailSectionProps {
  title: string;
  children: ReactNode;
  id?: string;
}

export function PolicyDetailSection({ title, children, id }: PolicyDetailSectionProps) {
  return (
    <section className="policy-detail-section panel" aria-labelledby={id ?? undefined}>
      <h2 className="policy-detail-section__title" id={id}>
        {title}
      </h2>
      <div className="policy-detail-section__body">{children}</div>
    </section>
  );
}
