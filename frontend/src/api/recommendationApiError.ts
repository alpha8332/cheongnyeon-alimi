export class RecommendationApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'RecommendationApiError';
    this.status = status;
    this.detail = detail;
  }
}
