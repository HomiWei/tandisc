import type { ReactNode } from "react";
import { safeHttpUrl } from "../lib/format";
import { Unavailable } from "./States";

export function ExternalLink({
  href,
  children,
  testId,
}: {
  href: string | null;
  children?: ReactNode;
  testId?: string;
}) {
  const safe = safeHttpUrl(href);
  if (!href) {
    return (
      <span data-testid={testId}>
        <Unavailable />
      </span>
    );
  }
  if (!safe) {
    return <span data-testid={testId}>{href}</span>;
  }
  return (
    <a data-testid={testId} href={safe} target="_blank" rel="noreferrer">
      {children ?? href}
    </a>
  );
}
