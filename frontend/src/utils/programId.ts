import type { NormalizedProgram } from '@/types/policy';

const ROUTE_SEPARATOR = '--';

export function encodeProgramRouteId(program: NormalizedProgram): string {
  if (!program.external_id) {
    throw new Error('Program external_id is required for routing.');
  }

  return `${program.source_id}${ROUTE_SEPARATOR}${program.external_id}`;
}

export function decodeProgramRouteId(
  routeId: string,
): { sourceId: string; externalId: string } | null {
  const separatorIndex = routeId.indexOf(ROUTE_SEPARATOR);
  if (separatorIndex <= 0 || separatorIndex === routeId.length - ROUTE_SEPARATOR.length) {
    return null;
  }

  return {
    sourceId: routeId.slice(0, separatorIndex),
    externalId: routeId.slice(separatorIndex + ROUTE_SEPARATOR.length),
  };
}

export function matchesProgramIdentity(
  program: NormalizedProgram,
  sourceId: string,
  externalId: string,
): boolean {
  return program.source_id === sourceId && program.external_id === externalId;
}
