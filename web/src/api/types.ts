export interface SourceRef {
  name: string | null;
  url: string | null;
  accessed_at: string | null;
}

export interface ProductListItem {
  id: string;
  name: string;
  tagline_zh: string | null;
  category: string | null;
  official_url: string | null;
  github_repo_id: string | null;
}

export interface ProductPricing {
  summary_zh: string | null;
  value: number | string | null;
  unit: string | null;
  source: SourceRef | null;
}

export interface ProductMetric {
  key: string | null;
  label_zh: string | null;
  value: number | string | null;
  unit: string | null;
  source_name: string | null;
  source_url: string | null;
  accessed_at: string | null;
}

export interface ProductDetail {
  id: string;
  name: string;
  tagline_zh: string | null;
  overview_zh: string | null;
  category: string | null;
  official_url: string | null;
  data_as_of: string | null;
  pricing: ProductPricing | null;
  metrics: ProductMetric[];
  github_repo_id: string | null;
  github_full_name: string | null;
}

export interface PageResult<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface GithubPeriod {
  year_month: string | null;
  start_date: string | null;
  end_date: string | null;
  timezone: string | null;
  data_as_of: string | null;
  is_fallback_previous_month: boolean;
  fallback_reason: string | null;
  label_zh: string | null;
  methodology_zh: string | null;
}

export interface GithubRankItem {
  rank: number | null;
  repo_id: string;
  full_name: string;
  html_url: string | null;
  tagline_zh: string | null;
  stars_start: number | null;
  stars_end: number | null;
  net_gain: number | null;
  stars_total: number | null;
  product_id: string | null;
}

export interface GithubRankings extends PageResult<GithubRankItem> {
  period: GithubPeriod;
}

export interface Meta {
  categories: string[];
  period: GithubPeriod | null;
}

export interface RepoMetricField {
  key: string;
  label: string;
  value: number | string | null;
}

export interface GithubRepoDetail {
  id: string | null;
  full_name: string | null;
  html_url: string | null;
  tagline_zh: string | null;
  product_id: string | null;
  metrics: RepoMetricField[];
}

export interface AskCitation {
  field: string | null;
  label_zh: string | null;
  source_name: string | null;
  source_url: string | null;
  name: string | null;
  url: string | null;
  accessed_at: string | null;
  text: string | null;
}

export interface AskResult {
  answer: string | null;
  status: string | null;
  citations: AskCitation[];
}

export interface AskRequest {
  target_type: "product" | "github_repo";
  target_id: string;
  question: string;
}
