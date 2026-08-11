import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildSavedConditionsKey,
  formatSavedConditionsSummary,
  parseSavedConditionsDraft,
  toRecommendationRequestFromConditions,
  toSavedConditionsDraft,
} from '../src/utils/savedConditionsForm.js';
import {
  clearSavedConditions,
  getSavedConditionsSnapshot,
  saveSavedConditions,
} from '../src/utils/userConditionsStorage.js';
import { MemoryStorage } from './helpers/memoryStorage.js';

class PatchedWindowStorage {
  install(storage: Storage): void {
    Object.defineProperty(globalThis, 'window', {
      configurable: true,
      value: {
        localStorage: storage,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      },
    });
  }

  restore(): void {
    Reflect.deleteProperty(globalThis, 'window');
  }
}

test('parseSavedConditionsDraft는 trim과 age 경계를 정규화한다', () => {
  const parsed = parseSavedConditionsDraft({
    region: '  서울특별시 ',
    age: 24,
    category: ' finance ',
  });

  assert.deepEqual(parsed, {
    region: '서울특별시',
    age: 24,
    category: 'finance',
  });
});

test('toRecommendationRequestFromConditions는 RecommendationRequest 필드를 매핑한다', () => {
  const request = toRecommendationRequestFromConditions({
    region: '서울특별시',
    age: 24,
    category: 'housing',
  });

  assert.deepEqual(request, {
    region: '서울특별시',
    age: 24,
    category: 'housing',
  });
});

test('saved conditions storage round-trip은 홈·추천 공유 snapshot을 유지한다', () => {
  const storage = new MemoryStorage();
  const windowPatch = new PatchedWindowStorage();
  windowPatch.install(storage);

  try {
    saveSavedConditions({
      region: '부산광역시',
      age: 27,
      category: 'employment',
    });

    const snapshot = getSavedConditionsSnapshot();
    assert.deepEqual(snapshot, {
      region: '부산광역시',
      age: 27,
      category: 'employment',
    });

    clearSavedConditions();
    assert.equal(getSavedConditionsSnapshot(), null);
  } finally {
    windowPatch.restore();
  }
});

test('buildSavedConditionsKey는 draft sync key를 생성한다', () => {
  const draft = toSavedConditionsDraft({
    region: '대전',
    age: 20,
    category: 'education',
  });

  assert.equal(buildSavedConditionsKey(draft), '대전|20|education');
  assert.equal(
    formatSavedConditionsSummary(draft),
    '대전 · 20세 · 교육',
  );
});
