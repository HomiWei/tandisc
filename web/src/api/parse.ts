import { CATEGORY_VALUES } from "./labels";
import type {
  AskCitation,
  AskResult,
  GithubPeriod,
  GithubRankItem,
  GithubRankings,
  GithubRepoDetail,
  Meta,
  PageResult,
  ProductDetail,
  ProductListItem,
  ProductMetric,
  ProductPricing,
  RepoMetricField,
  SourceRef,
} from "./types";
import { ApiError } from "./errors";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function fail(): never {
  throw new ApiError(0, undefined, "服务返回的数据无法识别。");
}

function textOrNull(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function numberOrNull(value: unknown): number | null {
  if (value == null) return null;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  fail();
}

function scalarOrNull(value: unknown): number | string | null {
  if (value == null) return null;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") return textOrNull(value);
  fail();
}

function intOr(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return fallback;
}

function parseSource(value: unknown): SourceRef | null {
  if (value == null) return null;
  if (!isRecord(value)) fail();
  const source: SourceRef = {
    name: textOrNull(value.name),
    url: textOrNull(value.url),
    accessed_at: textOrNull(value.accessed_at),
  };
  if (!source.name && !source.url) return null;
  return source;
}

export function parsePeriod(value: unknown): GithubPeriod | null {
  if (value == null) return null;
  if (!isRecord(value)) fail();
  return {
    year_month: textOrNull(value.year_month),
    start_date: textOrNull(value.start_date),
    end_date: textOrNull(value.end_date),
    timezone: textOrNull(value.timezone),
    data_as_of: textOrNull(value.data_as_of),
    is_fallback_previous_month: value.is_fallback_previous_month === true,
    fallback_reason: textOrNull(value.fallback_reason),
    label_zh: textOrNull(value.label_zh),
    methodology_zh: textOrNull(value.methodology_zh),
  };
}

function parseProductItem(value: unknown): ProductListItem {
  if (!isRecord(value)) fail();
  const id = textOrNull(value.id);
  const name = textOrNull(value.name);
  if (!id || !name) fail();
  return {
    id,
    name,
    tagline_zh: textOrNull(value.tagline_zh),
    category: textOrNull(value.category),
    official_url: textOrNull(value.official_url),
    github_repo_id: textOrNull(value.github_repo_id),
  };
}

function parsePricing(value: unknown): ProductPricing | null {
  if (value == null) return null;
  if (!isRecord(value)) fail();
  return {
    summary_zh: textOrNull(value.summary_zh),
    value: scalarOrNull(value.value),
    unit: textOrNull(value.unit),
    source: parseSource(value.source),
  };
}

function parseMetric(value: unknown): ProductMetric {
  if (!isRecord(value)) fail();
  return {
    key: textOrNull(value.key),
    label_zh: textOrNull(value.label_zh),
    value: scalarOrNull(value.value),
    unit: textOrNull(value.unit),
    source_name: textOrNull(value.source_name),
    source_url: textOrNull(value.source_url),
    accessed_at: textOrNull(value.accessed_at),
  };
}

export function parseProductPage(value: unknown): PageResult<ProductListItem> {
  if (!isRecord(value) || !Array.isArray(value.items)) fail();
  const items = value.items.map(parseProductItem);
  return {
    items,
    page: intOr(value.page, 1),
    page_size: intOr(value.page_size, items.length),
    total: intOr(value.total, items.length),
  };
}

export function parseProductDetail(value: unknown): ProductDetail {
  if (!isRecord(value)) fail();
  const id = textOrNull(value.id);
  const name = textOrNull(value.name);
  if (!id || !name) fail();
  if (value.metrics != null && !Array.isArray(value.metrics)) fail();
  return {
    id,
    name,
    tagline_zh: textOrNull(value.tagline_zh),
    overview_zh: textOrNull(value.overview_zh),
    category: textOrNull(value.category),
    official_url: textOrNull(value.official_url),
    data_as_of: textOrNull(value.data_as_of),
    pricing: parsePricing(value.pricing),
    metrics: Array.isArray(value.metrics) ? value.metrics.map(parseMetric) : [],
    github_repo_id: textOrNull(value.github_repo_id),
    github_full_name: textOrNull(value.github_full_name),
  };
}

function parseRankItem(value: unknown): GithubRankItem {
  if (!isRecord(value)) fail();
  const repoId = textOrNull(value.repo_id);
  const fullName = textOrNull(value.full_name);
  if (!repoId || !fullName) fail();
  return {
    rank: numberOrNull(value.rank),
    repo_id: repoId,
    full_name: fullName,
    html_url: textOrNull(value.html_url),
    tagline_zh: textOrNull(value.tagline_zh),
    stars_start: numberOrNull(value.stars_start),
    stars_end: numberOrNull(value.stars_end),
    net_gain: numberOrNull(value.net_gain),
    stars_total: numberOrNull(value.stars_total),
    product_id: textOrNull(value.product_id),
  };
}

export function parseRankings(value: unknown): GithubRankings {
  if (!isRecord(value) || !Array.isArray(value.items)) fail();
  const period = parsePeriod(value.period);
  if (!period) fail();
  const items = value.items.map(parseRankItem);
  return {
    period,
    items,
    page: intOr(value.page, 1),
    page_size: intOr(value.page_size, items.length),
    total: intOr(value.total, items.length),
  };
}

function parseCategoryList(value: unknown): string[] | null {
  if (!Array.isArray(value)) return null;
  const categories: string[] = [];
  for (const item of value) {
    if (typeof item === "string" && item.trim()) {
      categories.push(item.trim());
      continue;
    }
    if (isRecord(item)) {
      const raw = item.value;
      if (typeof raw === "string" && raw.trim()) categories.push(raw.trim());
    }
  }
  return categories;
}

export function parseMeta(value: unknown): Meta {
  if (!isRecord(value)) {
    return { categories: [...CATEGORY_VALUES], period: null };
  }
  const categories = parseCategoryList(value.categories);
  const period = parsePeriod(value.github_period ?? value.period);
  return {
    categories: categories && categories.length > 0 ? categories : [...CATEGORY_VALUES],
    period,
  };
}

const REPO_METRIC_FIELDS: { key: string; label: string; numeric: boolean }[] = [
  { key: "rank", label: "排名", numeric: true },
  { key: "year_month", label: "自然月", numeric: false },
  { key: "stars_start", label: "月初 star", numeric: true },
  { key: "stars_end", label: "月末 star", numeric: true },
  { key: "net_gain", label: "净增 star", numeric: true },
  { key: "stars_total", label: "当前 star", numeric: true },
  { key: "stars", label: "star", numeric: true },
  { key: "snapshot_date", label: "快照日期", numeric: false },
  { key: "captured_at", label: "采集时间", numeric: false },
  { key: "computed_at", label: "计算时间", numeric: false },
  { key: "data_as_of", label: "数据截止", numeric: false },
];

export function parseRepoDetail(value: unknown): GithubRepoDetail {
  if (!isRecord(value)) fail();
  const metrics: RepoMetricField[] = [];
  for (const field of REPO_METRIC_FIELDS) {
    if (!Object.prototype.hasOwnProperty.call(value, field.key)) continue;
    metrics.push({
      key: field.key,
      label: field.label,
      value: field.numeric ? numberOrNull(value[field.key]) : textOrNull(value[field.key]),
    });
  }
  return {
    id: textOrNull(value.id),
    full_name: textOrNull(value.full_name),
    html_url: textOrNull(value.html_url),
    tagline_zh: textOrNull(value.tagline_zh),
    product_id: textOrNull(value.product_id),
    metrics,
  };
}

function parseCitation(value: unknown): AskCitation {
  if (typeof value === "string") {
    return {
      field: null,
      label_zh: null,
      source_name: null,
      source_url: null,
      name: null,
      url: null,
      accessed_at: null,
      text: textOrNull(value),
    };
  }
  if (!isRecord(value)) fail();
  return {
    field: textOrNull(value.field),
    label_zh: textOrNull(value.label_zh),
    source_name: textOrNull(value.source_name),
    source_url: textOrNull(value.source_url),
    name: textOrNull(value.name),
    url: textOrNull(value.url),
    accessed_at: textOrNull(value.accessed_at),
    text: null,
  };
}

export function parseAsk(value: unknown): AskResult {
  if (!isRecord(value)) fail();
  if (value.citations != null && !Array.isArray(value.citations)) fail();
  return {
    answer: textOrNull(value.answer),
    status: textOrNull(value.status),
    citations: Array.isArray(value.citations) ? value.citations.map(parseCitation) : [],
  };
}
