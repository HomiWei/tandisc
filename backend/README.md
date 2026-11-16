# 探盘后端

Python 3.12、FastAPI、SQLAlchemy。P0 没有登录。列表和详情只返回已经入库、并且能指出来源的字段；没有可靠来源时数值和 `source` 都是 `null`，前端显示「暂无」。

## 安装和运行

在 `backend/` 目录：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8080}"
```

默认端口 `8080`（`APP_PORT`）。启动会 `create_all`，并插入目录里还不存在的产品。重复启动不会清空已有行。

手动重写目录文案（不改已绑定的 `github_repo_id`、已有 metrics、已填写的价格数字）：

```bash
python -m app.seed
```

健康检查：`GET /health` → `200` `{"status":"ok"}`。

交互式文档：`GET /docs`。

## 环境变量

复制 `.env.example` 为 `.env`。示例文件只有空占位，不要提交真实密钥。

| 变量 | 作用 |
| --- | --- |
| `APP_PORT` | 监听端口，默认 `8080`。由 uvicorn / 容器命令读取。 |
| `APP_ENV` | 环境名，只写进日志，例如 `local`、`staging`。 |
| `DATABASE_URL` | Postgres 连接串。留空则使用 `backend/data/tandisc.db`。`postgres://` 和 `postgresql://` 会自动改成 `postgresql+psycopg://`。 |
| `GITHUB_TOKEN` | 预留给以后的 star 快照任务。不配置也能启动，也能返回产品列表。 |
| `LLM_BASE_URL` | OpenAI 兼容接口根地址。三个 `LLM_*` 要同时有值，`POST /api/v1/ask` 才会调用模型。 |
| `LLM_API_KEY` | 模型密钥。不会写进日志或错误响应。 |
| `LLM_MODEL` | 模型名。 |
| `APP_TIMEZONE` | 榜单日历时区，默认 `Asia/Shanghai`。 |

本骨架的 CORS 对所有来源开放，方便本地和 staging。生产收紧时再改成可配置白名单。

## 迁移

表结构以 Alembic 修订 `20261116_0001` 为准，和当前模型一致。

本地 SQLite 可以不跑迁移，直接启动，由 `create_all` 建表。

Staging / Postgres：

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/tandisc'
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

先启动过、表已经由 `create_all` 建好时，不要再 `upgrade` 去建同一批表。对齐版本表用 `alembic stamp head`，之后的新修订再用 `upgrade`。

## Docker

仓库根目录：

```bash
docker build -t tandisc-backend backend
docker run --rm -p 8080:8080 tandisc-backend
```

容器内健康检查请求 `GET /health`。镜像默认 `APP_PORT=8080`。SQLite 数据在容器的 `/app/data`，不挂卷就会随容器消失。

## 接口

JSON，UTF-8。日期 `YYYY-MM-DD`，月份 `YYYY-MM`。错误体：

```json
{"error": {"code": "VALIDATION_ERROR", "message": "..."}}
```

`VALIDATION_ERROR` 400，`NOT_FOUND` 404，`UPSTREAM_UNAVAILABLE` 503，`INTERNAL_ERROR` 500。

### `GET /api/v1/meta`

分类枚举，以及当前默认的 GitHub 榜周期。响应字段是 `categories` 和 `github_period`。`github_period` 与月榜响应里的 `period` 是同一个对象（`year_month`、`start_date`、`end_date`、`label_zh`、`is_fallback_previous_month`、`fallback_reason` 等）。

分类：`developer_tools`、`productivity`、`ai`、`infra`、`design`、`payment`、`analytics`、`communication`、`other`。

### `GET /api/v1/products`

查询参数：`category`、`q`（名称模糊）、`sort`（`display_order` 默认，或 `name`）、`page`（从 1）、`page_size`（默认 30，最大 50）。

```json
{"items": [{"id": "prd_linear", "name": "Linear", "tagline_zh": "...", "category": "productivity", "official_url": "https://linear.app", "github_repo_id": null}], "page": 1, "page_size": 30, "total": 30}
```

列表不含定价、metrics、简介，也不含收入或流量。

### `GET /api/v1/products/{id}`

详情字段：`id`、`name`、`tagline_zh`、`overview_zh`、`category`、`official_url`、`data_as_of`、`pricing`、`metrics`、`github_repo_id`、`github_full_name`。不存在时 404 `NOT_FOUND`。

`pricing` 形如 `{value, unit, summary_zh, source}`。`source` 是 `{name, url, accessed_at}`，或在没有可用链接时为 `null`。种子数据的金额未核对，所以 `value` 和 `unit` 为 `null`；已保存的官方定价页 URL 会包成 `source`，`name` 为「官网定价页」，`accessed_at` 用该产品的 `data_as_of`。存的不是 http(s) URL 时，不编造链接，`value`、`unit` 和 `source` 都是 `null`。`summary_zh` 只说明以官方页面为准，不写具体价格。`metrics` 每项的 `source` 用同一个对象：有可用 URL 才给出，否则该项的 `value` 和 `source` 为 `null`。种子数据的 `metrics` 目前是空数组。`data_as_of` 是官方 URL 核对日期（`2026-11-16`），不是经营数据的截止日期。

产品 id 前缀 `prd_`。`github_repo_id` 在确认官方公开仓库之前保持 `null`。

### `GET /api/v1/github/monthly-rankings`

可选 `month=YYYY-MM`。不传时按下面的规则选周期。`page_size` 默认 50，最大 50。

```json
{"period": {}, "items": [], "page": 1, "page_size": 50, "total": 0}
```

`period` 字段：

| 字段 | 含义 |
| --- | --- |
| `year_month` | `YYYY-MM` |
| `timezone` | 默认 `Asia/Shanghai` |
| `label_zh` | 回退时固定为「上一完整月」；本月至今为「本月至今」；指定的已结束月份为「完整月」 |
| `is_fallback_previous_month` | 是否因为月初 1–7 日而改看上一完整月。8 日及以后即使没有快照也不回退 |
| `fallback_reason` | 回退时为 `current_month_snapshots_incomplete`，否则 `null` |
| `data_as_of` | 参与计算的最新快照日；没有则为 `null` |
| `start_date` / `end_date` | 这个周期的日历范围 |
| `methodology_zh` | 「净增 = 月末快照 star 减月初快照 star；时区 Asia/Shanghai；数据来自 GitHub 公开接口与我方快照。」 |
| `empty_reason_zh` | `items` 为空时的原因，有数据则为 `null` |
| `note_zh` | 为什么选了这个月 |

条目字段：`rank`、`repo_id`、`full_name`、`html_url`、`tagline_zh`、`stars_start`、`stars_end`、`net_gain`、`stars_total`、`product_id`。没有收入字段。算不出一对快照的仓库不会出现，也不会被填成 0。

规则（2026-11-16 确认）：

- `net_gain` = 结束快照 star − 开始快照 star
- 开始快照：该月 1 日当天的快照；否则取该日 00:00 之前最近的一条
- 已结束月份的结束快照：最后一天；否则取下月 1 日 00:00 之前最近的一条
- 当月 1–7 日：展示上一完整自然月，`is_fallback_previous_month=true`，`label_zh` 为「上一完整月」。当前月没有可用快照时同样如此；上一月也没有快照则 `items` 为空
- 当月 8 日至月末：始终展示本月，`is_fallback_previous_month=false`，`label_zh` 为「本月至今」。没有快照时 `items` 为空，不回退到上一月。有快照时净增 = 最新快照 star 减月初快照，`data_as_of` 为最新快照日期
- 显式传入 `month` 时只计算该月，不自动改到别的月份。未来月份返回 400

这个新服务还没有历史快照。以 Asia/Shanghai 的 2026-11-16 为例，默认请求得到 `items: []`，`period.year_month` 为 `2026-11`，`start_date` 为 `2026-11-01`，`end_date` 为 `2026-11-16`，`label_zh` 为「本月至今」，`is_fallback_previous_month` 为 false，`fallback_reason` 为 null，并带上 `empty_reason_zh`。不会编造 `net_gain`。

`app/services/snapshots.py` 是每日快照任务的空实现。调用它才读取 token；不配置 `GITHUB_TOKEN` 不影响启动。

### `GET /api/v1/github/repos/{id}`

仓库不存在时 404。有快照时返回最新 `stars_total` 和 `data_as_of`，否则这两个字段为 `null`。id 前缀 `gh_`。

### `POST /api/v1/ask`

```json
{"target_type": "product", "target_id": "prd_linear", "question": "这个产品是做什么的？"}
```

`target_type` 为 `product` 或 `github_repo`。HTTP 200 的体是 `{answer, status, citations}`。

- `answered`：只根据该条档案里已有的文字作答
- `insufficient_data`：`answer` 正好是「当前档案没有这项数据」（问收入、用户量、未收录的价格数字等）
- `out_of_scope`：投资建议、股票、医疗诊断等

三个 `LLM_*` 未配齐时，需要组织句子的问题返回 503 `UPSTREAM_UNAVAILABLE`。缺数据和超范围问题不调用模型。模型若写出档案里没有的数字，会被改成 `insufficient_data`。

## 种子数据

30 个海外产品，`display_order` 1–30。文案是原创中文，不是官网口号的照搬。定价只保存官方页面链接。Neon 使用 `https://neon.com`（`neon.tech` 会跳转到这里），Railway 使用 `https://railway.com`（`railway.app` 会跳转到这里）。其余官网和定价页在 2026-11-16 返回 HTTP 200。

## 日志

stdout 上的 JSON 日志，包含时间和级别。访问日志只记方法、路径和状态码。`Bearer`、`token=`、`api_key=` 一类片段会打码。不要把密钥写进异常信息。
