export class PolicySearchApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'PolicySearchApiError';
    this.status = status;
    this.detail = detail;
  }
}
