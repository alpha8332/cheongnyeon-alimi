import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import Input from '@/components/common/Input';

export default function HomePage() {
  return (
    <div>
      <h2>청년 정책 알리미 메인</h2>

      {/* 메인 검색창 영역 */}
      <div>
        <Input placeholder="원하는 정책이나 프로그램을 검색해보세요" />
        <Button>검색</Button>
      </div>

      {/* 카드 영역 와이어프레임 */}
      <div style={{ marginTop: '20px' }}>
        <Card>
          <p>주요 정책 / 프로그램 카드가 들어갈 영역입니다.</p>
        </Card>
      </div>
    </div>
  );
}