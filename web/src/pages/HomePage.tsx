import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMeta } from "../api/client";
import { isAbortError, toUserMessage } from "../api/errors";
import type { GithubPeriod } from "../api/types";
import { PeriodLabel } from "../components/PeriodPanel";
import { ErrorBanner, LoadingState, Unavailable } from "../components/States";
import { usePageTitle } from "../lib/usePageTitle";

export function HomePage() {
  usePageTitle("探盘");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [period, setPeriod] = useState<GithubPeriod | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    fetchMeta(controller.signal)
      .then((meta) => {
        setPeriod(meta.period);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (isAbortError(err)) return;
        setError(toUserMessage(err));
        setStatus("error");
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="stack" data-testid="home-page">
      <header className="page-head">
        <h1>探盘</h1>
        <p className="lede">浏览海外产品收录，以及 GitHub 当月净增 star。两榜分开。</p>
      </header>
      <div className="entry-grid">
        <Link className="entry" data-testid="home-link-products" to="/products">
          <h2>海外产品收录榜</h2>
          <p>按收录顺序查看名称、中文一句话和类目。列表不展示价格和指标。</p>
        </Link>
        <Link className="entry" data-testid="home-link-github" to="/github">
          <h2>GitHub 当月净增 star 榜</h2>
          <p>按自然月净增 star 排列。净增来自快照相减，不是收入。</p>
        </Link>
      </div>
      <section className="section">
        <h2>当前月榜口径</h2>
        {status === "loading" ? <LoadingState /> : null}
        {status === "error" && error ? <ErrorBanner message={error} /> : null}
        {status === "ready" && period ? (
          <div className="home-period">
            <p>自然月 {period.year_month ?? <Unavailable />}</p>
            <PeriodLabel period={period} />
            <p>{period.methodology_zh ?? <Unavailable />}</p>
          </div>
        ) : null}
        {status === "ready" && !period ? (
          <p>
            <Unavailable />
          </p>
        ) : null}
      </section>
    </div>
  );
}
