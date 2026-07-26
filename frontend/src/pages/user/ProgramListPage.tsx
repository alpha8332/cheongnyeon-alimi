import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import Input from '@/components/common/Input';

export default function ProgramListPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const querySearch = searchParams.get('search') || '';

  const [searchTerm, setSearchTerm] = useState(querySearch);

  useEffect(() => {
    setSearchTerm(querySearch);
  }, [querySearch]);

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchTerm.trim()) {
      navigate('/programs');
    } else {
      navigate(`/programs?search=${encodeURIComponent(searchTerm)}`);
    }
  };

  return (
    <div>
      <h2>정책 목록</h2>

      {/* 목록 화면 상단 통합 검색 영역 */}
      <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
        <Input
          placeholder="정책명, 키워드 검색 (예: 월세, 취업)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Button onClick={() => handleSearch()}>검색</Button>
      </form>

      {/* 검색어 상태 표시 영역 */}
      {querySearch && (
        <p style={{ fontWeight: 'bold' }}>
          '{querySearch}' 검색 결과 목록입니다.
        </p>
      )}

      {/* 정책 목록 결과 영역 (와이어프레임) */}
      <div>
        <h3>전체 정책 목록 (와이어프레임)</h3>
        <Card>
          <h4>정책 항목 1</h4>
          <p>카테고리 / 간단한 설명 영역</p>
        </Card>
        <Card>
          <h4>정책 항목 2</h4>
          <p>카테고리 / 간단한 설명 영역</p>
        </Card>
      </div>
    </div>
  );
}