import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import Input from '@/components/common/Input';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';

export default function HomePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const { data: policyList, isLoading } = usePoliciesQuery({
    page: 1,
    limit: 2,
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
    <div>
      <h2>청년 정책 알리미 메인</h2>

      <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
        <Input
          placeholder="원하는 정책이나 프로그램을 검색해보세요"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />
        <Button onClick={() => handleSearch()}>검색</Button>
      </form>

      <div>
        <h3>주요 정책 미리보기</h3>
        {isLoading ? (
          <LoadingState message="주요 정책을 불러오는 중입니다." />
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            {featuredPolicies.map((policy) => (
              <PolicyCard key={policy.id} policy={policy} />
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: '16px' }}>
        <Card>
          <p>전체 정책 목록과 필터는 정책 검색 페이지에서 확인할 수 있습니다.</p>
          <Button onClick={() => navigate('/programs')}>정책 목록 보기</Button>
        </Card>
      </div>
    </div>
  );
}
