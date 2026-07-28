/// <reference types="vite/client" />

declare module '@seed/initial_programs.json' {
  import type { NormalizedProgram } from '@/types/policy';

  const value: NormalizedProgram[];
  export default value;
}
