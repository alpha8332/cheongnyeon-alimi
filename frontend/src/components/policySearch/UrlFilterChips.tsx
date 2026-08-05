import type { UrlFilterChip } from '@/utils/policySearchFilterChips';
import './UrlFilterChips.css';

interface UrlFilterChipsProps {
  chips: UrlFilterChip[];
}

export default function UrlFilterChips({ chips }: UrlFilterChipsProps) {
  if (chips.length === 0) {
    return null;
  }

  return (
    <div>
      <p className="chips-label">추출된 검색 조건</p>
      <div className="chips-row">
        {chips.map((chip) => (
          <span key={chip.key} className="chip">
            {chip.label}
          </span>
        ))}
      </div>
    </div>
  );
}
