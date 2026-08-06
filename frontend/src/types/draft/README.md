# Policy Search display label drafts

Gate G1 contract types were promoted to production in FE4-11:

- `frontend/src/types/policySearch.ts`
- `frontend/src/types/policySearchErrors.ts`
- `frontend/src/types/policySearchUrlState.ts`

This directory retains **display label constants** only until FE4-19 UI
Slices finish Reason copy wiring.

## Remaining draft file

| File | Notes |
| --- | --- |
| `policySearchDisplay.ts` | Superseded by `frontend/src/constants/policySearchDisplay.ts` (FE4-18) |

Badge labels were promoted in FE4-18. Remove this draft file in a later cleanup
Slice if no longer referenced.
