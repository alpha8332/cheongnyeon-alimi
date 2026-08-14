import { useState } from 'react';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import { resetAllUserLocalStorage } from '@/utils/userDataReset';

export default function UserDataResetPanel() {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleReset = () => {
    const firstConfirmed = window.confirm(
      '북마크·저장 조건 등 이 기기에 저장된 모든 사용자 데이터를 삭제합니다. 계속할까요?',
    );

    if (!firstConfirmed) {
      return;
    }

    const secondConfirmed = window.confirm(
      '모든 북마크·조건·알림 설정이 삭제됩니다. 이 작업은 되돌릴 수 없습니다. 정말 삭제할까요?',
    );

    if (!secondConfirmed) {
      return;
    }

    const cleared = resetAllUserLocalStorage();
    setStatusMessage(
      cleared
        ? '브라우저에 저장된 사용자 데이터를 모두 삭제했습니다.'
        : '저장소를 사용할 수 없어 데이터를 삭제하지 못했습니다.',
    );
  };

  return (
    <Card title="⚠️ 사용자 데이터 전체 삭제">
      <p className="hint-text user-data-reset-panel__intro">
        북마크·저장 조건을 포함한 브라우저 localStorage 데이터를 완전히 삭제합니다.
        서버 API는 호출하지 않으며, 다른 기기 데이터에는 영향을 주지 않습니다.
      </p>
      <p className="hint-text">
        「조건 초기화」(홈)는 저장 조건만 지우고 북마크는 유지합니다. 이 버튼은
        북마크와 조건을 모두 삭제합니다.
      </p>
      <div className="user-data-reset-panel__actions">
        <Button type="button" variant="secondary" onClick={handleReset}>
          모든 사용자 데이터 삭제
        </Button>
      </div>
      {statusMessage ? (
        <p className="user-data-reset-panel__status" role="status">
          {statusMessage}
        </p>
      ) : null}
    </Card>
  );
}
