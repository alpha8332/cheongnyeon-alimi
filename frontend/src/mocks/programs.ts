import seedPrograms from '@seed/initial_programs.json';
import type { NormalizedProgram } from '@/types/policy';

export const mockPrograms: NormalizedProgram[] =
  seedPrograms as NormalizedProgram[];
