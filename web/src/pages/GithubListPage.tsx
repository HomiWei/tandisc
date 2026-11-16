import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchRankings } from "../api/client";
import { isAbortError, toUserMessage } from "../api/errors";
import type { GithubPeriod, GithubRankItem } from "../api/types";
import { ExternalLink } from "../components/ExternalLink";
import { Pagination } from "../components/Pagination";
import { PeriodPanel } from "../components/PeriodPanel";
import { EmptyState, ErrorBanner, LoadingState, Unavailable } from "../components/States";
import { formatQuantity } from "../lib/format";
import { usePageTitle } from "../lib/usePageTitle";

function pageFrom(value: string | null): number {
  const parsed = Number(value ?? "1");
  if (!Number.isFinite(parsed) || parsed < 1) return 1;
  return Math.floor(parsed);
}

function monthValue(value: string | null): string {
  if (!value || !/^\d{4}-\d{2}$/.test(value)) return "";
  return value;
}

function Count({ value }: { value: number | null }) {
  if (value == null) return <Unavailable />;
  return <span className="num">{formatQuantity(value)}</span>;
}

function RankRow({ item }: { item: GithubRankItem }) {
  return (
    <tr data-testid="github-row">
      <td className="rank">{item.rank == null ? <Unavailable /> : formatQuantity(item.rank)}</td>
      <td>
        <Link to={`/github/${encodeURIComponent(item.repo_id)}`}>{item.full_name}</Link>
        <div className="row-links">
          <ExternalLink href={item.html_url}>仓库</ExternalLink>
          {item.product_id ? (
            <Link to={`/products/${encodeURIComponent(item.product_id)}`}>收录</Link>
          ) : null}
        </div>
      </td>
      <td>{item.tagline_zh ?? <Unavailable />}</td>
      <td className="num">
        <Count value={item.stars_start} />
      </td>
      <td className="num">
        <Count value={item.stars_end} />
      </td>
      <td className="num">
        <Count value={item.net_gain} />
      </td>
      <td className="num">
        <Count value={item.stars_total} />
      </td>
    </tr>
  );
}

export function GithubListPage() {
  usePageTitle("GitHub 当月净增 star 榜 · 探盘");
  const [params, setParams] = useSearchParams();
  const month = monthValue(params.get("month"));
  const page = pageFrom(params.get("page"));
  const [draft, setDraft] = useState(month);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [period, setPeriod] = useState<GithubPeriod | null>(null);
  const [items, setItems] = useState<GithubRankItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(month);
  }, [month]);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setError(null);
    fetchRankings({ month: month || undefined, page }, controller.signal)
      .then((result) => {
        setPeriod(result.period);
        setItems(result.items);
        setTotal(result.total);
        setPageSize(result.page_size || 50);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (isAbortError(err)) return;
        setPeriod(null);
        setItems([]);
        setError(toUserMessage(err));
        setStatus("error");
      });
    return () => controller.abort();
  }, [month, page]);

  function write(nextMonth: string, nextPage: number) {
    const search = new URLSearchParams();
    if (nextMonth) search.set("month", nextMonth);
    if (nextPage > 1) search.set("page", String(nextPage));
    setParams(search);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const value = draft.trim();
    if (value && !/^\d{4}-\d{2}$/.test(value)) {
      setFormError("自然月格式应为 YYYY-MM。");
      return;
    }
    setFormError(null);
    write(value, 1);
  }

  return (
    <div className="stack">
      <header className="page-head">
        <h1>GitHub 当月净增 star 榜</h1>
        <p className="lede">按自然月净增 star 排列。净增不是收入。</p>
      </header>
      <form className="filters filters-month" data-testid="github-month-form" onSubmit={onSubmit}>
        <label className="field">
          自然月
          <input
            className="input"
            data-testid="github-month"
            inputMode="numeric"
            placeholder="YYYY-MM"
            autoComplete="off"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
        </label>
        <button className="button-primary" type="submit">
          查看
        </button>
        <button
          className="button-secondary"
          type="button"
          onClick={() => {
            setDraft("");
            setFormError(null);
            write("", 1);
          }}
        >
          默认月份
        </button>
      </form>
      {status === "loading" ? <LoadingState /> : null}
      {formError ? <ErrorBanner message={formError} /> : null}
      {status === "error" && error ? <ErrorBanner message={error} /> : null}
      {status === "ready" && period ? <PeriodPanel period={period} /> : null}
      {status === "ready" ? (
        <div data-testid="github-list">
          {items.length === 0 ? (
            <EmptyState
              title="暂无月榜"
              detail={total > 0 ? "这一页没有记录。" : "当前没有可用快照，不展示净增。"}
            />
          ) : (
            <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>仓库</th>
                <th>说明</th>
                <th>月初</th>
                <th>月末</th>
                <th>净增</th>
                <th>当前 star</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <RankRow key={item.repo_id} item={item} />
              ))}
            </tbody>
          </table>
            </div>
          )}
        </div>
      ) : null}
      {status === "ready" ? (
        <Pagination page={page} pageSize={pageSize} total={total} onPage={(next) => write(month, next)} />
      ) : null}
    </div>
  );
}
