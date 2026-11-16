export function Unavailable() {
  return <span data-testid="field-unavailable">暂无</span>;
}

export function LoadingState({ label = "正在加载。" }: { label?: string }) {
  return (
    <p className="loading-state" data-testid="loading-state" role="status">
      {label}
    </p>
  );
}

export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="empty-state" data-testid="empty-state">
      <p className="empty-title">{title}</p>
      {detail ? <p>{detail}</p> : null}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="error-banner" data-testid="error-banner" role="alert">
      {message}
    </div>
  );
}
