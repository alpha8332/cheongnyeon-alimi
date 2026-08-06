import seedPrograms from '@seed/initial_programs.json';
import { createMockPolicies } from './policyContract.js';

export const mockPolicies = createMockPolicies(seedPrograms);
