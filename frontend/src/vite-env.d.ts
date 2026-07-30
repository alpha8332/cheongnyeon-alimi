/// <reference types="vite/client" />

declare module '@seed/initial_programs.json' {
  import type { SeedPolicyProgram } from '@/mocks/policyContract';

  const value: SeedPolicyProgram[];
  export default value;
}
