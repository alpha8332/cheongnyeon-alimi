import assert from 'node:assert/strict';
import test from 'node:test';
import {
  formatBookmarkFolderLabel,
  sortBookmarkFolders,
} from '../src/utils/bookmarkExplorer.js';

const FOLDERS = [
  { id: 'b', name: '주거' },
  { id: 'a', name: '기본 폴더' },
  { id: 'c', name: '취업' },
];

test('sortBookmarkFolders는 이름순으로 정렬한다', () => {
  const counts: Record<string, number> = { a: 2, b: 5, c: 1 };

  const sorted = sortBookmarkFolders(
    FOLDERS,
    (id) => counts[id] ?? 0,
    'name',
    [],
  );

  assert.deepEqual(
    sorted.map((folder) => folder.id),
    ['a', 'b', 'c'],
  );
});

test('sortBookmarkFolders는 담긴 개수순으로 정렬한다', () => {
  const counts: Record<string, number> = { a: 2, b: 5, c: 1 };

  const sorted = sortBookmarkFolders(
    FOLDERS,
    (id) => counts[id] ?? 0,
    'count',
    [],
  );

  assert.deepEqual(
    sorted.map((folder) => folder.id),
    ['b', 'a', 'c'],
  );
});

test('sortBookmarkFolders는 pinned 폴더를 앞에 둔다', () => {
  const counts: Record<string, number> = { a: 10, b: 1, c: 1 };

  const sorted = sortBookmarkFolders(
    FOLDERS,
    (id) => counts[id] ?? 0,
    'count',
    ['c'],
  );

  assert.equal(sorted[0]?.id, 'c');
});

test('formatBookmarkFolderLabel은 이름 (개수) 형식을 만든다', () => {
  assert.equal(formatBookmarkFolderLabel('기본 폴더', 3), '기본 폴더 (3)');
});
