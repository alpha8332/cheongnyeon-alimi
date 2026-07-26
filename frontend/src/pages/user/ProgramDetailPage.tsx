import Button from '@/components/common/Button';
import Card from '@/components/common/Card';

export default function ProgramDetailPage() {
  return (
    <div>
      <h2>정책 상세 정보 (와이어프레임)</h2>

      <Card>
        <h3>선택한 정책 제목</h3>
        <p>상세 내용 / 지원 자격 / 신청 방법 들어갈 영역</p>
        <Button>신청 사이트로 이동</Button>
      </Card>
    </div>
  );
}