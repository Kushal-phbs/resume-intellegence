import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props { children: ReactNode; }
interface State { hasError: boolean; message: string; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(err: Error): State {
    return { hasError: true, message: err.message };
  }

  componentDidCatch(err: Error) {
    console.error("[ErrorBoundary]", err);
  }

  reset = () => this.setState({ hasError: false, message: "" });

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Something went wrong</h2>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">{this.state.message || "An unexpected error occurred."}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={this.reset}>
            <RefreshCw className="h-4 w-4" /> Try again
          </Button>
          <Button variant="ghost" onClick={() => window.location.assign("/")}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }
}
