import type { PolicySearchErrorPresentation } from '@/types/policySearchErrors';
import './PolicySearchShell.css';

interface PolicySearchEmptyShellProps {
  presentation: PolicySearchErrorPresentation;
}

export default function PolicySearchEmptyShell({
  presentation,
}: PolicySearchEmptyShellProps) {
  return (
    <section
      className="policy-search-shell policy-search-shell--empty"
      aria-label="검색 결과 없음"
    >
      <div className="policy-search-shell__icon" aria-hidden="true">
        🔍
      </div>
      <h2 className="policy-search-shell__title">{presentation.title}</h2>
      <p className="policy-search-shell__message">{presentation.message}</p>
      <ul className="policy-search-shell__tips">
        <li>검색창에서 조건을 수정한 뒤 다시 검색해 보세요.</li>
        <li>지역·연령·카테고리 필터를 줄이거나 바꿔 보세요.</li>
        <li>결과가 없다고 해서 해당 정책이 없다고 단정하지 않습니다.</li>
      </ul>
    </section>
  );
}
