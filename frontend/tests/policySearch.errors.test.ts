import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { PolicySearchApiError } from '../src/api/policySearchApiError.js';
import {
  isPolicySearchEmptyResults,
  mapPolicySearchEmptyResults,
  mapPolicySearchError,
  POLICY_SEARCH_EMPTY_RESULTS_COPY,
} from '../src/utils/policySearchErrors.js';

describe('policySearchErrors mapper', () => {
  it('422 PolicySearchApiError maps to validation presentation', () => {
    const error = new PolicySearchApiError(
      422,
      'q is required and must contain non-whitespace characters after trim.',
    );
    const presentation = mapPolicySearchError(error);

    assert.equal(presentation.kind, 'validation');
    assert.equal(presentation.retryable, false);
    assert.equal(presentation.preserve_filter_chips, true);
    assert.match(presentation.message, /q is required/);
  });

  it('5xx maps to retryable server presentation', () => {
    const presentation = mapPolicySearchError(
      new PolicySearchApiError(500, 'Internal Server Error'),
    );

    assert.equal(presentation.kind, 'server');
    assert.equal(presentation.retryable, true);
    assert.equal(presentation.preserve_filter_chips, true);
  });

  it('empty 200 envelope maps to empty_results golden copy', () => {
    const response = {
      total: 0,
      page: 1,
      limit: 20,
      interpreted_conditions: {
        q_raw: '없는조건',
        q_clean: '없는조건',
        conditions: [],
        override_fields: [],
        uninterpreted_terms: ['없는조건'],
      },
      items: [],
    };

    assert.equal(isPolicySearchEmptyResults(response), true);

    const presentation = mapPolicySearchEmptyResults(response);
    assert.equal(presentation.kind, 'empty_results');
    assert.equal(presentation.title, POLICY_SEARCH_EMPTY_RESULTS_COPY.title);
    assert.equal(presentation.preserve_filter_chips, true);
    assert.match(presentation.message, /존재하지 않는다는 뜻이 아닙니다/);
    assert.match(presentation.message, /미해석 키워드/);
  });
});
