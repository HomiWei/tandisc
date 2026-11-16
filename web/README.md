# 探盘前端

`web/` 是探盘的中文单页应用，技术栈为 Vite、React、TypeScript。仓库根目录留给后端，前端业务代码只在本目录。

契约来源：

- PRD：<https://cursor.com/canvas/store-4b50b212-978b-40d8-9b28-4ca217a118d6/2e0c457a-aa8d-4bff-aca0-b042d3c96df9>
- API：<https://cursor.com/canvas/store-4b50b212-978b-40d8-9b28-4ca217a118d6/b71962ec-04b9-423a-ae4b-b710fe05735b>

页面只渲染契约里的字段。接口没有给出的数字不会补，缺失值显示「暂无」。列表 `items` 为空数组时是空态，不是错误。

## 本地命令

在 `web/` 目录执行：

```bash
npm install
npm run dev
npm run build
npm run preview
```

- `npm run dev`：开发服务器。`/api` 与 `/health` 代理到 `http://127.0.0.1:8080`。
- `npm run build`：先做 TypeScript 检查，再打包。产物目录是 `web/dist`。
- `npm run preview`：本地预览 `dist`。同样把 `/api` 与 `/health` 代理到 `http://127.0.0.1:8080`，并按 SPA 回退到 `index.html`。

## 环境变量

只使用 `VITE_` 前缀。示例见 `.env.example`。

| 变量 | 默认 | 含义 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | 空字符串 | 接口源。留空时走当前站点同源，开发时由 Vite 代理到本机 8080。 |

不要把密钥、Token 或模型配置写进仓库。问答与 GitHub 快照用的密钥由后端环境注入，前端不读取。

## 路由

| 路径 | 页面 |
| --- | --- |
| `/` | 首页，产品收录与 GitHub 月榜两个入口 |
| `/products` | 海外产品收录榜 |
| `/products/:id` | 产品详情与条目内追问 |
| `/github` | GitHub 当月净增 star 榜 |
| `/github/:id` | 仓库详情与条目内追问 |

无登录。产品榜与 GitHub 榜分开。有 `github_repo_id` 或 `product_id` 时可以互相跳转，两榜不合并。涨星不是收入。

## 给运维：SPA 回退

前端使用 History 路由。静态站点需要把未知路径回退到 `index.html`，否则刷新 `/products` 或详情页会 404。

Nginx 示例见 `deploy/nginx.conf.example`：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

同时把 `/api/` 和 `/health` 反代到后端（默认端口 8080）。`/health` 只给活性检查，页面不展示它。

Vite 的 dev 与 preview 已是 SPA，会自行回退。生产构建本身不包含这层服务器配置。

## 接口用法

Base path 为 `/api/v1`。前端会发送：

- 产品榜：`page` 从 1，`page_size=30`，`sort` 只传 `display_order`（默认，不传）或 `name`，以及可选的 `category`、`q`。
- GitHub 月榜：`page` 从 1，`page_size=50`，可选 `month=YYYY-MM`。不传月份时由后端选择当前展示月。
- 追问：`POST /api/v1/ask`，正文只有 `target_type`（`product` 或 `github_repo`）、`target_id`、`question`。

错误体里的英文 `message` 不直接展示。前端按 `error.code` 与 HTTP 状态显示中文：

| 状态 | 页面文案 |
| --- | --- |
| 400 `VALIDATION_ERROR` | 请求参数不正确。 |
| 404 `NOT_FOUND` | 没有找到这条记录。 |
| 503 `UPSTREAM_UNAVAILABLE` | 问答服务暂时不可用。榜单和详情仍可查看，请稍后再试。 |
| 500 `INTERNAL_ERROR` | 服务暂时出错，请稍后再试。 |
| 网络失败 | 无法连接服务。请确认网络后重试。 |

问答在 HTTP 200 时按 `status` 显示：

| status | 呈现 |
| --- | --- |
| `answered` | 展示 `answer`，状态为「已回答」 |
| `insufficient_data` | 展示返回的 `answer`；若答案为空，使用契约固定句「当前档案没有这项数据」。状态为「资料不足」 |
| `out_of_scope` | 展示返回的 `answer`；若答案为空则数值位为「暂无」。状态为「超出范围」 |

`status` 原值放在 `ask-status` 的 `data-status` 上，界面文字是中文。

契约没有给出 `GET /api/v1/meta` 与 `GET /api/v1/github/repos/{id}` 的完整示例：

- meta 读取 `categories`（字符串，或带 `value` 的对象）。当前月榜口径以官方字段 `github_period` 为准，结构与月榜 `period` 相同。只有响应里没有 `github_period` 这个键时，才暂时读取 `github_ranking_period`，再没有则读 `period`。这是过渡兼容：后端按契约写出 `github_period` 之后，以该字段为准。类目中文是前端标签，不改 API 值。meta 失败时，筛选项回退到契约中的九个类目枚举，不编造产品。
- 产品详情的 `pricing.source` 按契约是 `{name, url, accessed_at}` 或 `null`。对象仍按这三个字段解析。若当前接口仍返回 URL 字符串，暂时当成 `{url, name: null, accessed_at: null}` 显示，避免整页变成「服务返回的数据无法识别。」。后端按契约改为对象后，字符串兼容可以去掉。
- 仓库详情展示 `id`、`full_name`、`html_url`、`tagline_zh`、`product_id`。若响应里带有契约已出现的指标字段（如 `stars_start`、`stars_end`、`net_gain`、`stars_total`、`stars`、`rank`、`snapshot_date`、`captured_at`、`computed_at`、`data_as_of`、`year_month`），按原字段显示；没有这些字段时，「关键指标」为「暂无」。

GitHub 榜页始终展示 `period.methodology_zh`。只要接口带回 `label_zh`，首页「当前月榜口径」和榜页都会显示，包括「本月至今」、空榜和回退月。`is_fallback_previous_month` 为 true 时仍用 `github-fallback-label`（一般为「上一完整月」，缺省为「暂无」）；该标志为 false 且 `label_zh` 有值时用 `github-period-label`。`fallback_reason` 不直接显示，避免把英文原因码丢给用户。`empty_reason_zh`、`note_zh` 不展示。

## 给测试：主流程

1. 打开 `/`。确认两个入口分开，文案不把涨星写成收入。首页「当前月榜口径」展示自然月、`label_zh` 和口径；接口给出「本月至今」时页面上能看到这四个字。
2. 进入 `/products`。用名称搜索、类目和排序（收录顺序 / 名称）。列表只有名称、中文一句话、类目。
3. 让产品接口返回 `items: []`。应看到「暂无收录」，而不是错误条。
4. 进入 `/products/:id`。定价说明可在数值为空时仍显示，数值为「暂无」。指标缺 `value` 或缺来源时，该栏保留并显示「暂无」。
5. 进入 `/github`。页面有统计周期和口径。`label_zh` 有值就显示，例如「本月至今」，回退月时则为「上一完整月」。
6. 月榜 `items` 为空时看到「暂无月榜」，不出现编造的净增。
7. 在产品或仓库详情提交追问，分别核对已回答、资料不足、超出范围，以及 503 的中文说明。
8. 后端未启动时，页面仍能打开，并在请求结束后显示中文错态，不出现样例产品或样例星数。

## data-testid

| testid | 位置 |
| --- | --- |
| `home-page` | 首页 |
| `home-link-products` | 首页进入产品榜 |
| `home-link-github` | 首页进入 GitHub 月榜 |
| `product-list` | 产品榜结果区域（含空态） |
| `product-search` | 产品名称搜索框 |
| `product-category-filter` | 类目筛选 |
| `product-sort` | 排序 |
| `product-card` | 单条产品 |
| `product-card-name` | 产品名称 |
| `product-card-tagline` | 产品一句话 |
| `product-detail` | 产品详情 |
| `product-official-url` | 官网 |
| `product-data-as-of` | 数据截止 |
| `product-pricing` | 定价区块 |
| `product-metrics` | 指标区块 |
| `field-unavailable` | 文案「暂无」 |
| `github-list` | 月榜结果区域（含空态） |
| `github-month` | 自然月选择 |
| `github-month-form` | 月份表单 |
| `github-period` | 统计周期 |
| `github-methodology` | `period.methodology_zh` |
| `github-period-label` | `label_zh` 有值且 `is_fallback_previous_month` 为 false 时出现（如「本月至今」）。首页月榜口径与 GitHub 榜页都有 |
| `github-fallback-label` | 仅当 `is_fallback_previous_month` 为 true 时出现，内容为 `label_zh`（没有则「暂无」）。首页月榜口径与 GitHub 榜页都有 |
| `github-row` | 月榜一行 |
| `repo-detail` | 仓库详情 |
| `ask-form` | 追问表单 |
| `ask-input` | 问题输入 |
| `ask-submit` | 提交 |
| `ask-answer` | 回答正文 |
| `ask-status` | 回答状态；`data-status` 为 API 的 `status` |
| `empty-state` | 空列表 |
| `error-banner` | 中文错态 |
| `loading-state` | 加载中 |
| `pager-prev` / `pager-next` | 分页 |

## 已知限制

- 后端未就绪时不使用假数据。页面可以打开，请求中为加载态，失败后为中文错态。
- 没有历史快照时，GitHub 月榜是空态，净增列不会出现占位数字。
- 问答依赖模型。模型不可用时接口返回 503，追问区域显示可读说明；榜单和详情仍可打开。
- P0 没有登录、付费、国内库、跨库查询和对外 Agent。
