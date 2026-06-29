import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Optional fallback for narrow failure scopes. */
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary — catches uncaught render errors and shows a recoverable
 * fallback. Logs to the console; in production we send to /api/errors.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Production: POST to /api/errors with request_id, user_id, stack
    // For now, log to console in dev; in prod wire to Sentry/Datadog.
    // eslint-disable-next-line no-console
    console.error("react_error_boundary", error, info.componentStack);
    void fetch("/api/errors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: "react_render_error",
        message: error.message,
        stack: error.stack,
        component_stack: info.componentStack,
      }),
    }).catch(() => {});
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="p-6 rounded-xl bg-danger/5 border border-danger/30 m-6">
          <div className="flex items-start gap-3">
            <div className="p-3 rounded-xl bg-danger/10 text-danger border border-danger/30">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-bold">Something went wrong on this page.</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {this.state.error?.message || "An unexpected error occurred."}
              </p>
              <button
                onClick={this.reset}
                className="mt-4 flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold"
              >
                <RefreshCw className="w-4 h-4" /> Retry
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
