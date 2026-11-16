import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct } from "../api/client";
import { isAbortError, toUserMessage } from "../api/errors";
import { categoryLabel } from "../api/labels";
import type { ProductDetail, ProductMetric, SourceRef } from "../api/types";
import { AskPanel } from "../components/AskPanel";
import { ExternalLink } from "../components/ExternalLink";
import { ErrorBanner, LoadingState, Unavailable } from "../components/States";
import { formatScalar, safeHttpUrl } from "../lib/format";
import { usePageTitle } from "../lib/usePageTitle";

function SourceView({ source }: { source: SourceRef | null }) {
  if (!source) return <Unavailable />;
  const href = safeHttpUrl(source.url);
  const label = source.name ?? source.url;
  return (
    <>
      {href && label ? (
        <a href={href} target="_blank" rel="noreferrer">
          {label}
        </a>
      ) : (
        <span>{label}</span>
      )}
      {source.accessed_at ? <span>，访问日期 {source.accessed_at}</span> : null}
    </>
  );
}

function MetricRow({ metric }: { metric: ProductMetric }) {
  const hasSource = Boolean(metric.source_name || metric.source_url);
  const value = hasSource ? formatScalar(metric.value) : null;
  return (
    <div className="metric">
      <p className="metric-label">{metric.label_zh ?? metric.key ?? <Unavailable />}</p>
      <p>
        {value == null ? (
          <Unavailable />
        ) : (
          <>
            {value}
            {metric.unit ? ` ${metric.unit}` : ""}
          </>
        )}
      </p>
      <p className="muted">
        来源{" "}
        {hasSource ? (
          <>
            {safeHttpUrl(metric.source_url) ? (
              <a href={safeHttpUrl(metric.source_url) ?? undefined} target="_blank" rel="noreferrer">
                {metric.source_name ?? metric.source_url}
              </a>
            ) : (
              (metric.source_name ?? metric.source_url)
            )}
            {metric.accessed_at ? `，访问日期 ${metric.accessed_at}` : ""}
          </>
        ) : (
          <Unavailable />
        )}
      </p>
    </div>
  );
}

export function ProductDetailPage() {
  const { id = "" } = useParams();
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  usePageTitle(product ? `${product.name} · 探盘` : "产品详情 · 探盘");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setProduct(null);
    setError(null);
    fetchProduct(id, controller.signal)
      .then((detail) => {
        setProduct(detail);
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
        <Link to="/products">返回收录榜</Link>
      </p>
      {status === "loading" ? <LoadingState /> : null}
      {status === "error" && error ? <ErrorBanner message={error} /> : null}
      {status === "ready" && product ? (
        <article className="stack" data-testid="product-detail">
          <header className="page-head">
            <p className="category">
              {product.category ? (categoryLabel(product.category) ?? product.category) : <Unavailable />}
            </p>
            <h1>{product.name}</h1>
            <p className="lede">{product.tagline_zh ?? <Unavailable />}</p>
          </header>
          <section className="section">
            <h2>概述</h2>
            <p>{product.overview_zh ?? <Unavailable />}</p>
          </section>
          <section className="section">
            <h2>官网</h2>
            <p>
              <ExternalLink href={product.official_url} testId="product-official-url" />
            </p>
          </section>
          <section className="section">
            <h2>数据截止</h2>
            <p data-testid="product-data-as-of">{product.data_as_of ?? <Unavailable />}</p>
          </section>
          <section className="section" data-testid="product-pricing">
            <h2>定价</h2>
            {product.pricing ? (
              <dl className="dl">
                <dt>说明</dt>
                <dd>{product.pricing.summary_zh ?? <Unavailable />}</dd>
                <dt>数值</dt>
                <dd>
                  {product.pricing.source && formatScalar(product.pricing.value) != null ? (
                    <>
                      {formatScalar(product.pricing.value)}
                      {product.pricing.unit ? ` ${product.pricing.unit}` : ""}
                    </>
                  ) : (
                    <Unavailable />
                  )}
                </dd>
                <dt>来源</dt>
                <dd>
                  <SourceView source={product.pricing.source} />
                </dd>
              </dl>
            ) : (
              <p>
                <Unavailable />
              </p>
            )}
          </section>
          <section className="section" data-testid="product-metrics">
            <h2>指标</h2>
            {product.metrics.length === 0 ? (
              <p>
                <Unavailable />
              </p>
            ) : (
              <div className="metric-list">
                {product.metrics.map((metric, index) => (
                  <MetricRow key={`${metric.key ?? "metric"}-${index}`} metric={metric} />
                ))}
              </div>
            )}
          </section>
          <section className="section">
            <h2>关联仓库</h2>
            {product.github_repo_id ? (
              <p>
                <Link to={`/github/${encodeURIComponent(product.github_repo_id)}`}>
                  {product.github_full_name ?? "查看仓库"}
                </Link>
              </p>
            ) : (
              <p>
                <Unavailable />
              </p>
            )}
          </section>
          <AskPanel targetType="product" targetId={product.id} />
        </article>
      ) : null}
    </div>
  );
}
