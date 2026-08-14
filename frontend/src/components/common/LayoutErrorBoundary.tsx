import { Component, type ErrorInfo, type ReactNode } from 'react';

interface LayoutErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

interface LayoutErrorBoundaryState {
  error: Error | null;
}

export default class LayoutErrorBoundary extends Component<
  LayoutErrorBoundaryProps,
  LayoutErrorBoundaryState
> {
  state: LayoutErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): LayoutErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[LayoutErrorBoundary]', error, info.componentStack);
  }

  private handleReload = (): void => {
    window.location.reload();
  };

  render() {
    if (this.state.error !== null) {
      return (
        <div className="page layout-error-boundary" role="alert">
          <h1 className="layout-error-boundary__title">
            {this.props.fallbackTitle ?? '화면을 불러오지 못했습니다'}
          </h1>
          <p className="layout-error-boundary__message">
            일시적인 오류가 발생했습니다. 새로고침 후에도 문제가 계속되면
            브라우저 저장 데이터를 확인해 주세요.
          </p>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={this.handleReload}
          >
            새로고침
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
