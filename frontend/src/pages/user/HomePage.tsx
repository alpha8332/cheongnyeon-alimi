import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';

export default function HomePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const { data: policyList, isLoading } = usePoliciesQuery({
    page: 1,
    limit: 3,
    include_partial: false,
  });
  const featuredPolicies = policyList?.items ?? [];

  const handleSearch = (event?: FormEvent) => {
    if (event) {
      event.preventDefault();
    }

    if (!searchTerm.trim()) {
      navigate('/programs');
      return;
    }

    navigate(`/programs?search=${encodeURIComponent(searchTerm)}`);
  };

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">안녕하세요, 청년님 👋</h1>
        <p className="greeting__subtitle">
          맞춤 지원금·정책을 한 문장으로 찾아보세요
        </p>
      </header>

      <form onSubmit={handleSearch}>
        <div className="search-wrap">
          <span className="search-wrap__icon" aria-hidden="true">
            🔍
          </span>
          <input
            className="search-wrap__input"
            type="search"
            placeholder="예: 천안 사는 24세 청년 지원금"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            aria-label="정책 검색어"
          />
          <Button type="submit">검색하기</Button>
        </div>
      </form>

      <div className="section-head">
        <h2 className="section-title">조건 맞춤 TOP 추천</h2>
        <span className="section-badge">주요 정책</span>
      </div>

      {isLoading ? (
        <LoadingState message="주요 정책을 불러오는 중입니다." />
      ) : (
        <div className="cards-grid">
          {featuredPolicies.map((policy) => (
            <PolicyCard key={policy.id} policy={policy} />
          ))}
        </div>
      )}

      <Card title="📋 더 많은 정책 보기">
        <p className="hint-text">
          전체 정책 목록과 필터는 정책 목록 페이지에서 확인할 수 있습니다.
        </p>
        <div style={{ marginTop: '16px' }}>
          <Button variant="secondary" onClick={() => navigate('/programs')}>
            정책 목록 보기
          </Button>
        </div>
      </Card>
    </div>
  );
}
