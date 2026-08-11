import type { ResolvedCollectionRunListQuery } from '../api/adminRequest.js';
import type {
  CollectionRunDetailDto,
  CollectionRunListResponse,
  CollectionRunTriggerRequest,
  CollectionRunTriggerResponse,
} from '../types/collectionRun.js';
import {
  findMockCollectionRunDetailById,
  MOCK_COLLECTION_RUN_DETAILS,
  toCollectionRunListItem,
} from './collectionRunFixtures.js';

function compareStartedAtDesc(
  left: CollectionRunDetailDto,
  right: CollectionRunDetailDto,
): number {
  return right.started_at.localeCompare(left.started_at);
}

function matchesListQuery(
  run: CollectionRunDetailDto,
  query: ResolvedCollectionRunListQuery,
): boolean {
  if (query.source_id !== undefined && run.source_id !== query.source_id) {
    return false;
  }

  if (query.status !== undefined && run.status !== query.status) {
    return false;
  }

  if (query.run_type !== undefined && run.run_type !== query.run_type) {
    return false;
  }

  if (query.trigger_type !== undefined && run.trigger_type !== query.trigger_type) {
    return false;
  }

  if (query.start_date !== undefined && run.started_at < query.start_date) {
    return false;
  }

  if (query.end_date !== undefined && run.started_at > query.end_date) {
    return false;
  }

  return true;
}

export function createMockCollectionRunListResponse(
  query: ResolvedCollectionRunListQuery,
): CollectionRunListResponse {
  const filtered = [...MOCK_COLLECTION_RUN_DETAILS]
    .filter((run) => matchesListQuery(run, query))
    .sort(compareStartedAtDesc);

  const start = (query.page - 1) * query.size;
  const pageItems = filtered.slice(start, start + query.size);
  const pages = Math.max(1, Math.ceil(filtered.length / query.size));

  return {
    items: pageItems.map(toCollectionRunListItem),
    page: query.page,
    size: query.size,
    total: filtered.length,
    pages,
  };
}

export type CollectionRunDetailMockResult =
  | { status: 200; body: CollectionRunDetailDto }
  | { status: 404; body: { detail: string } };

export function handleCollectionRunDetailMock(
  runId: string,
): CollectionRunDetailMockResult {
  const run = findMockCollectionRunDetailById(runId);

  if (run === null) {
    return {
      status: 404,
      body: { detail: 'Collection run not found.' },
    };
  }

  return {
    status: 200,
    body: run,
  };
}

export function handleCollectionRunListMock(
  query: ResolvedCollectionRunListQuery,
): CollectionRunListResponse {
  return createMockCollectionRunListResponse(query);
}

export function handleCollectionRunTriggerMock(
  request: CollectionRunTriggerRequest,
): CollectionRunTriggerResponse {
  return {
    run_id: '55555555-5555-4555-8555-555555555555',
    source_id: request.source_id ?? 'youthcenter',
    run_type: 'collection',
    trigger_type: 'admin',
    status: 'running',
    started_at: new Date().toISOString(),
    message: 'Manual collection run initiated successfully.',
  };
}
