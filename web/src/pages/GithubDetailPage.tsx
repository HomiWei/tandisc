import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchRepo } from "../api/client";
import { isAbortError, toUserMessage } from "../api/errors";
import type { GithubRepoDetail } from "../api/types";
import { AskPanel } from "../components/AskPanel";
import { ExternalLink } from "../components/ExternalLink";
import { ErrorBanner, LoadingState, Unavailable } from "../components/States";
import { formatScalar } from "../lib/format";
import { usePageTitle } from "../lib/usePageTitle";

export function GithubDetailPage() {
  const { id = "" } = useParams();
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [repo, setRepo] = useState<GithubRepoDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  usePageTitle(repo?.full_name ? `${repo.full_name} · 探盘` : "仓库详情 · 探盘");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setRepo(null);
    setError(null);
    fetchRepo(id, controller.signal)
      .then((detail) => {
        setRepo(detail);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (isAbortError(err)) return;
        setError(toUserMessage(err));
        setStatus("error");
      });
    return () => controller.abort();
  }, [id]);

  return (
    <div className="stack">
      <p>
        <Link to="/github">返回月榜</Link>
      </p>
      {status === "loading" ? <LoadingState /> : null}
      {status === "error" && error ? <ErrorBanner message={error} /> : null}
      {status === "ready" && repo ? (
        <article className="stack" data-testid="repo-detail">
          <header className="page-head">
            <h1>{repo.full_name ?? <Unavailable />}</h1>
            <p className="lede">{repo.tagline_zh ?? <Unavailable />}</p>
          </header>
          <section className="section">
            <h2>仓库</h2>
            <p>
              <ExternalLink href={repo.html_url} />
            </p>
          </section>
          <section className="section">
            <h2>关联产品</h2>
            {repo.product_id ? (
              <p>
                <Link to={`/products/${encodeURIComponent(repo.product_id)}`}>查看收录</Link>
              </p>
            ) : (
              <p>
                <Unavailable />
              </p>
            )}
          </section>
          <section className="section">
            <h2>关键指标</h2>
            {repo.metrics.length === 0 ? (
              <p>
                <Unavailable />
              </p>
            ) : (
              <dl className="dl">
                {repo.metrics.map((metric) => (
                  <div className="dl-row" key={metric.key}>
                    <dt>{metric.label}</dt>
                    <dd>{formatScalar(metric.value) ?? <Unavailable />}</dd>
                  </div>
                ))}
              </dl>
            )}
          </section>
          <AskPanel targetType="github_repo" targetId={id} />
        </article>
      ) : null}
    </div>
  );
}
