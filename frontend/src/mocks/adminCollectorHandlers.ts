import { MOCK_ADMIN_COLLECTOR_STATUS } from './adminCollectorFixtures.js';
import type { AdminCollectorStatusResponse } from '../types/adminCollector.js';

export function handleAdminCollectorStatusMock(): AdminCollectorStatusResponse {
  return structuredClone(MOCK_ADMIN_COLLECTOR_STATUS);
}

