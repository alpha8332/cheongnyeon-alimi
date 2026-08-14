export class PolicyDetailApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'PolicyDetailApiError';
    this.status = status;
    this.detail = detail;
  }
}
