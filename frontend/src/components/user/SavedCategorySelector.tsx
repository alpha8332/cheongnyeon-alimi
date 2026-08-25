import type { PolicyCategory } from '@/types/policy';
import {
  SAVED_CONDITIONS_CATEGORY_OPTIONS,
} from '@/utils/savedConditionsForm';
import { getCategoryLabel } from '@/utils/policyDisplay';

interface SavedCategorySelectorProps {
  value: readonly PolicyCategory[];
  onChange: (categories: PolicyCategory[]) => void;
  disabled?: boolean;
}

export default function SavedCategorySelector({
  value,
  onChange,
  disabled = false,
}: SavedCategorySelectorProps) {
  const selected = new Set(value);

  const toggle = (category: PolicyCategory, checked: boolean) => {
    onChange(
      checked
        ? SAVED_CONDITIONS_CATEGORY_OPTIONS.filter(
            (option) => selected.has(option) || option === category,
          )
        : value.filter((option) => option !== category),
    );
  };

  return (
    <fieldset className="saved-conditions-form__categories">
      <legend className="saved-conditions-form__label">관심 분야 (복수 선택)</legend>
      <div className="saved-conditions-form__category-options">
        {SAVED_CONDITIONS_CATEGORY_OPTIONS.map((category) => (
          <label
            key={category}
            className="saved-conditions-form__category-option"
          >
            <input
              type="checkbox"
              checked={selected.has(category)}
              onChange={(event) => toggle(category, event.target.checked)}
              disabled={disabled}
            />
            <span>{getCategoryLabel(category)}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
