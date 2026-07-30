export function parsePolicyId(routeId: string | undefined): number | null {
  if (!routeId || !/^[1-9]\d*$/.test(routeId)) {
    return null;
  }

  const policyId = Number(routeId);
  return Number.isSafeInteger(policyId) ? policyId : null;
}
