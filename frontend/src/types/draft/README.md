# W3-F0 Policy Search contract drafts

Gate G1 pending consumption drafts for Frontend 04. **Not approved API contracts.**
Do not import from production UI, API Client, Mock, or MSW until `G1_APPROVED`.

## Authority order

1. [Gate G1 handoff](../../../docs/development/weekly_plan/week_03_search_contract_handoff.md)
2. Backend 06 W3-B0 request·response (Gate G1 integration)
3. This directory after G1 sync

## G1 integration summary

| Area | Draft file | Notes |
| --- | --- | --- |
| Request/response | `policySearch.contract.ts` | `PolicySearchQueryParams`, `PolicySearchInterpretedConditions`, nested `PolicySearchHit`, `UnconfirmedCondition`, nullable `DimensionVerdicts` |
| URL state types | `policySearchUrlState.ts` | Types only; no parse/build functions pre-G1 |
| Display labels | `policySearchDisplay.ts` | Constants only; no mapper functions pre-G1 |
| Error types | `policySearchErrors.ts` | Types only; HTTP mapping in Forest plan |

## URL rule (G1)

- URL may store: `q`, `keyword`, `region`, `age`, `category`, `status`, `include_partial`, `page`, `limit`
- URL must **not** store Backend response JSON (`interpreted_conditions`, verdicts, `reason_codes`, `score`, per-row unconfirmed blob)

## Reason-code fallback (G1)

`ReasonCode` is an extensible string. Post-G1 UI maps known codes when copy exists; otherwise display Backend `message` from `UnconfirmedCondition` or error body without failing.

Promote to `frontend/src/types/policySearch.ts` only after Team Leader records `G1_APPROVED`.
