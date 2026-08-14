import seedPrograms from '@seed/initial_programs.json';
import {
  createMockPolicies,
  createMockPolicyDetails,
} from './policyContract.js';

export const mockPolicies = createMockPolicies(seedPrograms);
export const mockPolicyDetails = createMockPolicyDetails(seedPrograms);
