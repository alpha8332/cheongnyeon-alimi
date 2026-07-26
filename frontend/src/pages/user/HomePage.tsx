import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import Input from '@/components/common/Input';

export default function HomePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

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
      <h2>청년 정책 알리미 메인</h2>

      {/* 메인 검색창 영역 (검색 시 목록 페이지로 이동) */}
      <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
        <Input
          placeholder="원하는 정책이나 프로그램을 검색해보세요"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Button onClick={() => handleSearch()}>검색</Button>
      </form>

      {/* 카드 영역 와이어프레임 */}
      <div>
        <Card>
          <p>주요 정책 / 프로그램 카드가 들어갈 영역입니다.</p>
        </Card>
      </div>
    </div>
  );
}