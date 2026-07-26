import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import Input from '@/components/common/Input';

export default function ProgramListPage() {
  return (
    <div>
      <h2>정책 목록</h2>

      {/* 목록 화면 상단 통합 검색 영역 */}
      <div style={{ marginBottom: '20px' }}>
        <Input placeholder="정책명, 키워드 검색 (예: 월세, 취업)" />
        <Button>검색</Button>
      </div>

      {/* 정책 목록 결과 영역 */}
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