import { useState } from 'react';
import ConditionEditorDrawer, {
  type ConditionEditorValues,
} from '@/components/policySearch/ConditionEditorDrawer';
import type { InterpretedConditionDimension } from '@/types/policySearch';
import {
  getInterpretedChipClassName,
  mapChipDimensionToFilterDimension,
  type InterpretedFilterChip,
} from '@/utils/interpretedConditionChips';
import type { PolicySearchFilterValue } from '@/utils/policySearchFilterMutations';
import './InterpretedConditionChips.css';

interface InterpretedConditionChipsProps {
  chips: InterpretedFilterChip[];
  onRemove: (dimension: InterpretedFilterChip['dimension']) => void;
  onUpdate: (
    dimension: Exclude<InterpretedConditionDimension, never>,
    value: PolicySearchFilterValue,
  ) => void;
  onAdd: (
    dimension: InterpretedConditionDimension,
    value: PolicySearchFilterValue,
  ) => void;
  disabled?: boolean;
}

function readChipEditValue(chip: InterpretedFilterChip): PolicySearchFilterValue {
  if (
    chip.dimension === 'include_partial' ||
    chip.value === null ||
    chip.value === undefined
  ) {
    return '';
  }

  return chip.value as PolicySearchFilterValue;
}

export default function InterpretedConditionChips({
  chips,
  onRemove,
  onUpdate,
  onAdd,
  disabled = false,
}: InterpretedConditionChipsProps) {
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorMode, setEditorMode] = useState<'add' | 'edit'>('add');
  const [editingChip, setEditingChip] = useState<InterpretedFilterChip | null>(
    null,
  );

  const openAddEditor = () => {
    setEditorMode('add');
    setEditingChip(null);
    setEditorOpen(true);
  };

  const openEditEditor = (chip: InterpretedFilterChip) => {
    if (!chip.editable || chip.dimension === 'include_partial') {
      return;
    }

    setEditorMode('edit');
    setEditingChip(chip);
    setEditorOpen(true);
  };

  const handleSave = (values: ConditionEditorValues) => {
    if (editorMode === 'add') {
      onAdd(values.dimension, values.value);
    } else {
      onUpdate(values.dimension, values.value);
    }

    setEditorOpen(false);
    setEditingChip(null);
  };

  return (
    <>
      <div className="interpreted-chips">
        <div className="interpreted-chips__head">
          <p className="chips-label">추출된 검색 조건</p>
          <button
            type="button"
            className="interpreted-chips__add btn btn-secondary"
            onClick={openAddEditor}
            disabled={disabled}
          >
            + 조건 추가
          </button>
        </div>

        {chips.length > 0 ? (
          <div className="chips-row">
            {chips.map((chip) => (
              <span key={chip.id} className={getInterpretedChipClassName(chip)}>
                <button
                  type="button"
                  className="chip__label"
                  onClick={() => openEditEditor(chip)}
                  disabled={disabled || !chip.editable}
                  title={
                    chip.editable
                      ? `${chip.label} 수정`
                      : '검색어에서 해석된 조건은 검색어를 수정해 주세요'
                  }
                >
                  {chip.label}
                </button>
                {chip.removable ? (
                  <button
                    type="button"
                    className="chip-x"
                    onClick={() => {
                      const filterDimension = mapChipDimensionToFilterDimension(
                        chip.dimension,
                      );
                      if (filterDimension) {
                        onRemove(chip.dimension);
                      }
                    }}
                    disabled={disabled}
                    aria-label={`${chip.label} 제거`}
                  >
                    ✕
                  </button>
                ) : null}
              </span>
            ))}
          </div>
        ) : (
          <p className="interpreted-chips__empty">
            아직 추출된 조건이 없습니다. 조건을 추가하거나 검색어를 입력해 보세요.
          </p>
        )}
      </div>

      <ConditionEditorDrawer
        key={`${editorMode}-${editingChip?.id ?? 'add'}`}
        open={editorOpen}
        mode={editorMode}
        initialDimension={
          editingChip && editingChip.dimension !== 'include_partial'
            ? editingChip.dimension
            : 'region'
        }
        initialValue={
          editingChip ? readChipEditValue(editingChip) : undefined
        }
        onClose={() => {
          setEditorOpen(false);
          setEditingChip(null);
        }}
        onSave={handleSave}
      />
    </>
  );
}
