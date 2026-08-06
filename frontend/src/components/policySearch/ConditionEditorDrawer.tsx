import { useId, useState, type FormEvent } from 'react';
import type { InterpretedConditionDimension } from '@/types/policySearch';
import type { ApplicationStatus, PolicyCategory } from '@/types/policy';
import {
  formatApplicationStatus,
  getCategoryLabel,
} from '@/utils/policyDisplay';
import type { PolicySearchFilterValue } from '@/utils/policySearchFilterMutations';
import './ConditionEditorDrawer.css';

const CATEGORY_OPTIONS: PolicyCategory[] = [
  'housing',
  'finance',
  'welfare',
  'employment',
  'startup',
  'education',
  'other',
];

const STATUS_OPTIONS: ApplicationStatus[] = ['open', 'closed', 'scheduled'];

const DIMENSION_LABELS: Record<InterpretedConditionDimension, string> = {
  keyword: '키워드',
  region: '지역',
  age: '연령',
  category: '카테고리',
  status: '신청상태',
};

const ADDABLE_DIMENSIONS: InterpretedConditionDimension[] = [
  'region',
  'age',
  'category',
  'status',
  'keyword',
];

export interface ConditionEditorValues {
  dimension: InterpretedConditionDimension;
  value: PolicySearchFilterValue;
}

interface ConditionEditorDrawerProps {
  open: boolean;
  mode: 'add' | 'edit';
  initialDimension?: InterpretedConditionDimension;
  initialValue?: PolicySearchFilterValue;
  onClose: () => void;
  onSave: (values: ConditionEditorValues) => void;
}

function readInitialDraft(
  dimension: InterpretedConditionDimension,
  value?: PolicySearchFilterValue,
): string {
  if (value === undefined || value === null) {
    return '';
  }

  if (dimension === 'age') {
    return String(value);
  }

  return String(value);
}

export default function ConditionEditorDrawer({
  open,
  mode,
  initialDimension = 'region',
  initialValue,
  onClose,
  onSave,
}: ConditionEditorDrawerProps) {
  const titleId = useId();
  const [dimension, setDimension] = useState<InterpretedConditionDimension>(
    initialDimension,
  );
  const [draft, setDraft] = useState(() =>
    readInitialDraft(initialDimension, initialValue),
  );

  if (!open) {
    return null;
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();

    if (dimension === 'age') {
      const parsed = Number(draft);
      if (!Number.isSafeInteger(parsed) || parsed < 0 || parsed > 150) {
        return;
      }

      onSave({ dimension, value: parsed });
      return;
    }

    if (dimension === 'category') {
      if (!CATEGORY_OPTIONS.includes(draft as PolicyCategory)) {
        return;
      }

      onSave({ dimension, value: draft as PolicyCategory });
      return;
    }

    if (dimension === 'status') {
      if (!STATUS_OPTIONS.includes(draft as ApplicationStatus)) {
        return;
      }

      onSave({ dimension, value: draft as ApplicationStatus });
      return;
    }

    const trimmed = draft.trim();
    if (!trimmed) {
      return;
    }

    onSave({ dimension, value: trimmed });
  };

  return (
    <div className="condition-editor-backdrop" onClick={onClose}>
      <div
        className="condition-editor-drawer panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="condition-editor-drawer__header">
          <h2 id={titleId} className="panel-title">
            {mode === 'add' ? '검색 조건 추가' : '검색 조건 수정'}
          </h2>
          <button
            type="button"
            className="condition-editor-drawer__close"
            onClick={onClose}
            aria-label="닫기"
          >
            ✕
          </button>
        </div>

        <form className="condition-editor-form" onSubmit={handleSubmit}>
          {mode === 'add' ? (
            <label className="condition-editor-form__field">
              <span className="condition-editor-form__label">조건 유형</span>
              <select
                className="condition-editor-form__input"
                value={dimension}
                onChange={(event) => {
                  const nextDimension = event.target
                    .value as InterpretedConditionDimension;
                  setDimension(nextDimension);
                  setDraft('');
                }}
              >
                {ADDABLE_DIMENSIONS.map((option) => (
                  <option key={option} value={option}>
                    {DIMENSION_LABELS[option]}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="condition-editor-form__hint">
              {DIMENSION_LABELS[dimension]} 조건을 수정합니다.
            </p>
          )}

          {dimension === 'category' ? (
            <label className="condition-editor-form__field">
              <span className="condition-editor-form__label">카테고리</span>
              <select
                className="condition-editor-form__input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
              >
                <option value="">선택</option>
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {getCategoryLabel(option)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {dimension === 'status' ? (
            <label className="condition-editor-form__field">
              <span className="condition-editor-form__label">신청상태</span>
              <select
                className="condition-editor-form__input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
              >
                <option value="">선택</option>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {formatApplicationStatus(option)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {dimension === 'age' ? (
            <label className="condition-editor-form__field">
              <span className="condition-editor-form__label">연령</span>
              <input
                className="condition-editor-form__input"
                type="number"
                min={0}
                max={150}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="예: 24"
              />
            </label>
          ) : null}

          {dimension === 'region' || dimension === 'keyword' ? (
            <label className="condition-editor-form__field">
              <span className="condition-editor-form__label">
                {DIMENSION_LABELS[dimension]}
              </span>
              <input
                className="condition-editor-form__input"
                type="text"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={
                  dimension === 'region' ? '예: 서울특별시' : '예: 지원금'
                }
              />
            </label>
          ) : null}

          <div className="condition-editor-form__actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              취소
            </button>
            <button type="submit" className="btn btn-primary">
              적용
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
