"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

import { ErrorState } from "@/components/ui/states";

interface Props {
  children: ReactNode;
  /** Short name of the widget, shown in the error title. */
  label: string;
}

interface State {
  error: Error | null;
}

/**
 * Isolates a widget: if it throws while rendering, only that card shows an error (with a working
 * "Retry" that re-mounts it) instead of the whole page failing.
 */
export class WidgetBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(`[widget:${this.props.label}]`, error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <ErrorState
          title={`${this.props.label} failed to render`}
          error={this.state.error}
          onRetry={() => this.setState({ error: null })}
        />
      );
    }
    return this.props.children;
  }
}
