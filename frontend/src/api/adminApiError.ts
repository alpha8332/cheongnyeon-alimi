export class AdminApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'AdminApiError';
    this.status = status;
    this.detail = detail;
  }
}
