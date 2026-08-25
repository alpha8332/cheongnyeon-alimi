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
    categories: ['finance'],
  });
});

test('parseSavedConditionsDraft는 관심 분야 여러 개를 중복 없이 유지한다', () => {
  const parsed = parseSavedConditionsDraft({
    region: null,
    age: null,
    category: 'housing',
    categories: ['housing', 'finance', 'housing'],
  });

  assert.deepEqual(parsed, {
    region: null,
    age: null,
    category: 'housing',
    categories: ['housing', 'finance'],
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
    categories: ['housing'],
    include_partial: true,
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
      categories: ['employment'],
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

test('다중 관심 분야는 추천 요청과 요약에 모두 반영된다', () => {
  const conditions = parseSavedConditionsDraft({
    region: '경기도',
    age: 29,
    category: 'housing',
    categories: ['housing', 'finance'],
  });

  assert.deepEqual(toRecommendationRequestFromConditions(conditions), {
    region: '경기도',
    age: 29,
    category: 'housing',
    categories: ['housing', 'finance'],
    include_partial: true,
  });
  assert.equal(formatSavedConditionsSummary(conditions), '경기도 · 29세 · 주거, 금융');
  assert.equal(buildSavedConditionsKey(conditions), '경기도|29|housing,finance');
});
