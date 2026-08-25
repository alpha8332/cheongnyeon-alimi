import assert from 'node:assert/strict';
import test from 'node:test';
import {
  HOME_REGION_GROUPS,
  splitHomeSearchRegion,
} from '../src/utils/homeSearchRegions.js';

test('홈 지역 선택은 전국 시·도와 양산시를 포함한다', () => {
  assert.equal(
    HOME_REGION_GROUPS.some(({ province }) => province === '서울특별시'),
    true,
  );
  assert.equal(
    HOME_REGION_GROUPS.some(({ province }) => province === '세종특별자치시'),
    true,
  );

  const gyeongnam = HOME_REGION_GROUPS.find(
    ({ province }) => province === '경상남도',
  );
  assert.ok(gyeongnam);
  assert.equal(
    gyeongnam.districts.some(
      ({ value }) => value === '경상남도 양산시',
    ),
    true,
  );
});

test('URL 지역을 시·도와 시·군·구 선택값으로 복원한다', () => {
  assert.deepEqual(splitHomeSearchRegion('경상남도 양산시'), {
    province: '경상남도',
    district: '경상남도 양산시',
  });
  assert.deepEqual(splitHomeSearchRegion('서울특별시'), {
    province: '서울특별시',
    district: '',
  });
  assert.deepEqual(splitHomeSearchRegion('알 수 없는 지역'), {
    province: '',
    district: '',
  });
});
