import SavedConditionsPanel from '@/components/user/SavedConditionsPanel';

export default function UserProfilePage() {
  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">사용자 프로필</h1>
        <p className="greeting__subtitle">
          지역·연령·관심 분야 등 맞춤 조건을 이 기기에 저장합니다. 저장된 조건은
          맞춤 추천 등에서 공유됩니다.
        </p>
      </header>

      <SavedConditionsPanel />
    </div>
  );
}
