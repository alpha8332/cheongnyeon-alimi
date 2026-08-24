import { useId, useState, type FormEvent } from 'react';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import { useSavedConditions } from '@/hooks/useSavedConditions';
import {
  SAVED_CONDITIONS_CATEGORY_OPTIONS,
  SAVED_CONDITIONS_MAX_AGE,
  SAVED_CONDITIONS_MIN_AGE,
  buildSavedConditionsKey,
  formatSavedConditionsSummary,
  parseSavedConditionsDraft,
  toSavedConditionsDraft,
} from '@/utils/savedConditionsForm';
import { getCategoryLabel } from '@/utils/policyDisplay';

export default function SavedConditionsPanel() {
  const formId = useId();
  const { conditions, saveConditions, clearConditions } = useSavedConditions();
  const conditionsKey = buildSavedConditionsKey(conditions);
  const [storedConditionsKey, setStoredConditionsKey] = useState(conditionsKey);
  const [draft, setDraft] = useState(() => toSavedConditionsDraft(conditions));
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  if (conditionsKey !== storedConditionsKey) {
    setStoredConditionsKey(conditionsKey);
    setDraft(toSavedConditionsDraft(conditions));
  }

  const summary = formatSavedConditionsSummary(conditions);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const parsed = parseSavedConditionsDraft(draft);
    const result = saveConditions(parsed);

    if (result.changed) {
      setStatusMessage('저장 조건을 브라우저에 저장했습니다.');
    } else {
      setStatusMessage('변경된 조건이 없습니다.');
    }
  };

  const handleClear = () => {
    const confirmed = window.confirm(
      '저장된 지역·연령·관심 분야 조건만 삭제합니다. 북마크는 유지됩니다. 계속할까요?',
    );

    if (!confirmed) {
      return;
    }

    const result = clearConditions();
    if (result.changed) {
      setStatusMessage('저장 조건을 초기화했습니다.');
    }
  };

  return (
    <Card title="🎯 내 조건 저장">
      <p className="hint-text saved-conditions-panel__intro">
        지역·연령·관심 분야를 이 기기 브라우저에만 저장합니다. 서버·URL·로그에는
        기록되지 않으며, 다른 기기와 동기화되지 않습니다.
      </p>

      {summary ? (
        <p className="saved-conditions-panel__summary" role="status">
          저장됨: {summary}
        </p>
      ) : (
        <p className="saved-conditions-panel__summary saved-conditions-panel__summary--empty">
          아직 저장된 조건이 없습니다.
        </p>
      )}

      <form
        id={formId}
        className="saved-conditions-form"
        onSubmit={handleSubmit}
        aria-label="저장 조건 편집"
      >
        <label className="saved-conditions-form__field">
          <span className="saved-conditions-form__label">거주 지역</span>
          <input
            className="saved-conditions-form__input"
            type="text"
            value={draft.region ?? ''}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                region: event.target.value,
              }))
            }
            placeholder="예: 서울특별시"
            maxLength={200}
          />
        </label>

        <label className="saved-conditions-form__field">
          <span className="saved-conditions-form__label">연령</span>
          <input
            className="saved-conditions-form__input"
            type="number"
            min={SAVED_CONDITIONS_MIN_AGE}
            max={SAVED_CONDITIONS_MAX_AGE}
            value={draft.age ?? ''}
            onChange={(event) => {
              const raw = event.target.value;
              setDraft((current) => ({
                ...current,
                age: raw.length === 0 ? null : Number(raw),
              }));
            }}
            placeholder="예: 24"
          />
        </label>

        <label className="saved-conditions-form__field">
          <span className="saved-conditions-form__label">관심 분야</span>
          <select
            className="saved-conditions-form__input"
            value={draft.category ?? ''}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                category: event.target.value.length > 0 ? event.target.value : null,
              }))
            }
          >
            <option value="">선택 안 함</option>
            {SAVED_CONDITIONS_CATEGORY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {getCategoryLabel(option)}
              </option>
            ))}
          </select>
        </label>

        <div className="saved-conditions-form__actions">
          <Button type="submit">조건 저장</Button>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClear}
            disabled={conditions === null}
          >
            조건 초기화
          </Button>
        </div>
      </form>

      {statusMessage ? (
        <p className="saved-conditions-panel__status" role="status">
          {statusMessage}
        </p>
      ) : null}
    </Card>
  );
}
