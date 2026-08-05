# Policy Search display label drafts

Gate G1 contract types were promoted to production in FE4-11:

- `frontend/src/types/policySearch.ts`
- `frontend/src/types/policySearchErrors.ts`
- `frontend/src/types/policySearchUrlState.ts`

This directory retains **display label constants** only until FE4-18/FE4-19 UI
Slices promote `policySearchDisplay.ts`.

## Remaining draft file

| File | Notes |
| --- | --- |
| `policySearchDisplay.ts` | Badge labels and help copy; imports `@/types/policySearch` |

Promote display constants to `frontend/src/constants/policySearchDisplay.ts` (or
equivalent) when implementing Partial/Unknown badges (FE4-18).
