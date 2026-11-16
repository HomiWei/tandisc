import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchMeta, fetchProducts } from "../api/client";
import { isAbortError, toUserMessage } from "../api/errors";
import { CATEGORY_VALUES, categoryLabel } from "../api/labels";
import type { ProductListItem } from "../api/types";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBanner, LoadingState, Unavailable } from "../components/States";
import { usePageTitle } from "../lib/usePageTitle";

function pageFrom(value: string | null): number {
  const parsed = Number(value ?? "1");
  if (!Number.isFinite(parsed) || parsed < 1) return 1;
  return Math.floor(parsed);
}

export function ProductListPage() {
  usePageTitle("海外产品收录榜 · 探盘");
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const category = params.get("category") ?? "";
  const sort = params.get("sort") === "name" ? "name" : "display_order";
  const page = pageFrom(params.get("page"));
  const [draft, setDraft] = useState(q);
  const [categories, setCategories] = useState<string[]>([...CATEGORY_VALUES]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [items, setItems] = useState<ProductListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(q);
  }, [q]);

  useEffect(() => {
    const controller = new AbortController();
    fetchMeta(controller.signal)
      .then((meta) => {
        const next = [...meta.categories];
        if (category && !next.includes(category)) next.push(category);
        setCategories(next);
      })
      .catch((err: unknown) => {
        if (isAbortError(err)) return;
        setCategories((current) => (category && !current.includes(category) ? [...current, category] : current));
      });
    return () => controller.abort();
  }, [category]);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setError(null);
    fetchProducts(
      {
        q: q.trim() || undefined,
        category: category || undefined,
        sort,
        page,
      },
      controller.signal,
    )
      .then((result) => {
        setItems(result.items);
        setTotal(result.total);
        setPageSize(result.page_size || 30);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (isAbortError(err)) return;
        setItems([]);
        setError(toUserMessage(err));
        setStatus("error");
      });
    return () => controller.abort();
  }, [q, category, sort, page]);

  function update(next: { q?: string; category?: string; sort?: string; page?: number }) {
    const search = new URLSearchParams(params);
    const write = (key: string, value: string | undefined) => {
      if (!value) search.delete(key);
      else search.set(key, value);
    };
    if ("q" in next) write("q", next.q);
    if ("category" in next) write("category", next.category);
    if ("sort" in next) write("sort", next.sort === "display_order" ? undefined : next.sort);
    if ("page" in next) write("page", next.page && next.page > 1 ? String(next.page) : undefined);
    setParams(search);
  }

  function onSearch(event: FormEvent) {
    event.preventDefault();
    update({ q: draft.trim(), page: 1 });
  }

  return (
    <div className="stack">
      <header className="page-head">
        <h1>海外产品收录榜</h1>
        <p className="lede">按收录顺序浏览。列表不展示价格、收入或指标数字。</p>
      </header>
      <form className="filters" onSubmit={onSearch}>
        <label className="field">
          名称
          <input
            className="input"
            data-testid="product-search"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
        </label>
        <label className="field">
          类目
          <select
            className="select"
            data-testid="product-category-filter"
            value={category}
            onChange={(event) => update({ category: event.target.value, page: 1 })}
          >
            <option value="">全部类目</option>
            {categories.map((value) => (
              <option key={value} value={value}>
                {categoryLabel(value) ?? value}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          排序
          <select
            className="select"
            data-testid="product-sort"
            value={sort}
            onChange={(event) => update({ sort: event.target.value, page: 1 })}
          >
            <option value="display_order">收录顺序</option>
            <option value="name">名称</option>
          </select>
        </label>
        <button className="button-primary" type="submit">
          搜索
        </button>
      </form>
      {status === "loading" ? <LoadingState /> : null}
      {status === "error" && error ? <ErrorBanner message={error} /> : null}
      {status === "ready" ? (
        <div data-testid="product-list">
          {items.length === 0 ? (
            <EmptyState
              title="暂无收录"
              detail={total > 0 ? "这一页没有记录。" : "没有符合当前筛选的产品。"}
            />
          ) : (
            items.map((item) => (
            <Link className="product-card" data-testid="product-card" key={item.id} to={`/products/${encodeURIComponent(item.id)}`}>
              <p className="category">{item.category ? (categoryLabel(item.category) ?? item.category) : <Unavailable />}</p>
              <p className="product-card-name" data-testid="product-card-name">
                {item.name}
              </p>
              <p className="product-card-tagline" data-testid="product-card-tagline">
                {item.tagline_zh ?? <Unavailable />}
              </p>
            </Link>
            ))
          )}
        </div>
      ) : null}
      {status === "ready" ? (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={total}
          onPage={(next) => update({ page: next })}
        />
      ) : null}
    </div>
  );
}
