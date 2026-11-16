import type { GithubPeriod } from "../api/types";
import { Unavailable } from "./States";

function TextOrUnavailable({ value }: { value: string | null }) {
  if (!value) return <Unavailable />;
  return <>{value}</>;
}

export function PeriodLabel({ period }: { period: GithubPeriod }) {
  if (period.is_fallback_previous_month) {
    return (
      <p className="fallback" data-testid="github-fallback-label">
        {period.label_zh ?? <Unavailable />}
      </p>
    );
  }
  if (!period.label_zh) return null;
  return (
    <p className="period-label" data-testid="github-period-label">
      {period.label_zh}
    </p>
  );
}

export function PeriodPanel({ period }: { period: GithubPeriod }) {
  return (
    <section className="period" data-testid="github-period">
      <h2>统计周期</h2>
      <dl className="dl">
        <dt>自然月</dt>
        <dd>
          <TextOrUnavailable value={period.year_month} />
        </dd>
        <dt>起止</dt>
        <dd>
          <TextOrUnavailable value={period.start_date} />
          <span> 至 </span>
          <TextOrUnavailable value={period.end_date} />
        </dd>
        <dt>时区</dt>
        <dd>
          <TextOrUnavailable value={period.timezone} />
        </dd>
        <dt>数据截止</dt>
        <dd>
          <TextOrUnavailable value={period.data_as_of} />
        </dd>
      </dl>
      <PeriodLabel period={period} />
      <p className="methodology" data-testid="github-methodology">
        {period.methodology_zh ?? <Unavailable />}
      </p>
    </section>
  );
}
