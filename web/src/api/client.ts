import { isAbortError, ApiError, userMessageForStatus } from "./errors";
import { parseAsk, parseMeta, parseProductDetail, parseProductPage, parseRankings, parseRepoDetail } from "./parse";
import type { AskRequest, AskResult, GithubRankings, GithubRepoDetail, Meta, PageResult, ProductDetail, ProductListItem } from "./types";

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL ?? "";
  return raw.replace(/\/+$/, "");
}

function queryString(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

function errorCode(payload: unknown): string | undefined {
  if (typeof payload !== "object" || payload === null) return undefined;
  const error = (payload as { error?: unknown }).error;
  if (typeof error !== "object" || error === null) return undefined;
  const code = (error as { code?: unknown }).code;
  return typeof code === "string" ? code : undefined;
}

async function request(path: string, init: RequestInit | undefined, signal?: AbortSignal): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`${apiBase()}${path}`, {
      ...init,
      signal,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch (err) {
    if (isAbortError(err)) throw err;
    throw new ApiError(0, undefined, "无法连接服务。请确认网络后重试。");
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text) as unknown;
    } catch {
      throw new ApiError(response.status, undefined, response.ok ? "服务返回的数据无法识别。" : userMessageForStatus(response.status));
    }
  }

  if (!response.ok) {
    const code = errorCode(payload);
    throw new ApiError(response.status, code, userMessageForStatus(response.status, code));
  }
  return payload;
}

export interface ProductQuery {
  category?: string;
  q?: string;
  sort?: "display_order" | "name";
  page?: number;
}

export function fetchProducts(query: ProductQuery, signal?: AbortSignal): Promise<PageResult<ProductListItem>> {
  const path = `/api/v1/products${queryString({
    category: query.category,
    q: query.q,
    sort: query.sort,
    page: query.page ?? 1,
    page_size: 30,
  })}`;
  return request(path, undefined, signal).then(parseProductPage);
}

export function fetchProduct(id: string, signal?: AbortSignal): Promise<ProductDetail> {
  return request(`/api/v1/products/${encodeURIComponent(id)}`, undefined, signal).then(parseProductDetail);
}

export function fetchRankings(query: { month?: string; page?: number }, signal?: AbortSignal): Promise<GithubRankings> {
  const path = `/api/v1/github/monthly-rankings${queryString({
    month: query.month,
    page: query.page ?? 1,
    page_size: 50,
  })}`;
  return request(path, undefined, signal).then(parseRankings);
}

export function fetchRepo(id: string, signal?: AbortSignal): Promise<GithubRepoDetail> {
  return request(`/api/v1/github/repos/${encodeURIComponent(id)}`, undefined, signal).then(parseRepoDetail);
}

export function fetchMeta(signal?: AbortSignal): Promise<Meta> {
  return request("/api/v1/meta", undefined, signal).then(parseMeta);
}

export function postAsk(body: AskRequest, signal?: AbortSignal): Promise<AskResult> {
  return request(
    "/api/v1/ask",
    { method: "POST", body: JSON.stringify(body) },
    signal,
  ).then(parseAsk);
}
