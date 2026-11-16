"""Self-curated product catalog.

Official site and pricing-page URLs were checked for HTTP 200 on 2026-11-16.
neon.tech and railway.app redirect to neon.com and railway.com, so those
canonical hosts are stored. Copy is original. Pricing amounts are not recorded:
value and unit stay null, and summary_zh only points at the official page.
"""

from datetime import date

from app.domain import CATEGORIES

URLS_VERIFIED_ON = date(2026, 11, 16)


def _row(
    product_id: str,
    name: str,
    tagline_zh: str,
    overview_zh: str,
    category: str,
    official_url: str,
    pricing_source: str,
    display_order: int,
) -> dict:
    summary = f"{name} 的收费方案以官方页面为准。本档案只保存来源链接，不记录未核对的金额。"
    return {
        "id": product_id,
        "name": name,
        "tagline_zh": tagline_zh,
        "overview_zh": overview_zh,
        "category": category,
        "official_url": official_url,
        "pricing_source": pricing_source,
        "pricing_summary_zh": summary,
        "display_order": display_order,
    }


PRODUCTS: list[dict] = [
    _row(
        "prd_linear",
        "Linear",
        "给软件团队用的议题跟踪工具",
        "Linear 用来登记需求、缺陷和迭代，工程团队可以在同一条工作流里指定负责人和状态。",
        "productivity",
        "https://linear.app",
        "https://linear.app/pricing",
        1,
    ),
    _row(
        "prd_notion",
        "Notion",
        "用页面和数据库一起整理团队资料",
        "Notion 把文档、备忘和轻量表格放在同一套页面里，适合做知识库或简单的项目表。",
        "productivity",
        "https://www.notion.so",
        "https://www.notion.so/pricing",
        2,
    ),
    _row(
        "prd_figma",
        "Figma",
        "可以多人同时改的界面设计工具",
        "Figma 在浏览器里绘制界面和原型，设计稿能直接分给同事评论。",
        "design",
        "https://www.figma.com",
        "https://www.figma.com/pricing",
        3,
    ),
    _row(
        "prd_slack",
        "Slack",
        "按频道组织的团队即时消息工具",
        "Slack 用频道和私信把工作对话收在一起，也可以把其他工具的通知接到频道里。",
        "communication",
        "https://slack.com",
        "https://slack.com/pricing",
        4,
    ),
    _row(
        "prd_stripe",
        "Stripe",
        "给网站和应用用的在线收款接口",
        "Stripe 用来接入收款和订阅扣款。具体费率以官方定价页为准，这里不记录未核对的数字。",
        "payment",
        "https://stripe.com",
        "https://stripe.com/pricing",
        5,
    ),
    _row(
        "prd_vercel",
        "Vercel",
        "用来发布前端和全栈应用的托管平台",
        "Vercel 连接代码仓库后可以预览并发布网站，也提供在边缘运行代码的环境。",
        "infra",
        "https://vercel.com",
        "https://vercel.com/pricing",
        6,
    ),
    _row(
        "prd_supabase",
        "Supabase",
        "以 Postgres 为核心的托管后端",
        "Supabase 提供数据库、登录和文件存储，应用可以直接连这些后端能力。",
        "infra",
        "https://supabase.com",
        "https://supabase.com/pricing",
        7,
    ),
    _row(
        "prd_neon",
        "Neon",
        "可以按负载伸缩的云端 Postgres",
        "Neon 托管 PostgreSQL，并支持把数据库分成独立分支，方便开发和测试分开。",
        "infra",
        "https://neon.com",
        "https://neon.com/pricing",
        8,
    ),
    _row(
        "prd_planetscale",
        "PlanetScale",
        "带分支工作流的托管 MySQL 平台",
        "PlanetScale 提供 MySQL 兼容的托管数据库，变更可以先放在独立分支里再合并。",
        "infra",
        "https://planetscale.com",
        "https://planetscale.com/pricing",
        9,
    ),
    _row(
        "prd_railway",
        "Railway",
        "从代码仓库部署服务的云平台",
        "Railway 用来运行后端服务、数据库和定时任务。费用计算方式以官方定价页为准。",
        "infra",
        "https://railway.com",
        "https://railway.com/pricing",
        10,
    ),
    _row(
        "prd_render",
        "Render",
        "托管网站、后台进程和数据库的云平台",
        "Render 支持静态站、Web 服务和托管数据库，常见用法是推送代码后自动发布。",
        "infra",
        "https://render.com",
        "https://render.com/pricing",
        11,
    ),
    _row(
        "prd_cloudflare",
        "Cloudflare",
        "提供域名解析、加速和网站安全的网络服务",
        "Cloudflare 放在网站前面，提供 DNS、内容分发和安全防护，也可以在边缘运行代码。",
        "infra",
        "https://www.cloudflare.com",
        "https://www.cloudflare.com/plans/",
        12,
    ),
    _row(
        "prd_clerk",
        "Clerk",
        "可以嵌进应用的登录和用户管理组件",
        "Clerk 负责注册、登录和组织成员，开发者把它接到自己的产品里。",
        "developer_tools",
        "https://clerk.com",
        "https://clerk.com/pricing",
        13,
    ),
    _row(
        "prd_auth0",
        "Auth0",
        "托管的登录与访问控制服务",
        "Auth0 用来给应用加上登录、单点登录和权限控制。方案差异见官方定价页。",
        "developer_tools",
        "https://auth0.com",
        "https://auth0.com/pricing",
        14,
    ),
    _row(
        "prd_resend",
        "Resend",
        "给应用发送事务邮件的开发者接口",
        "Resend 提供发信 API，用于验证码、通知和收据这类由产品触发的邮件。",
        "developer_tools",
        "https://resend.com",
        "https://resend.com/pricing",
        15,
    ),
    _row(
        "prd_posthog",
        "PostHog",
        "产品分析、实验和功能开关工具",
        "PostHog 记录用户在产品里的操作，并可以做实验和功能开关。这里不收录事件量或收入。",
        "analytics",
        "https://posthog.com",
        "https://posthog.com/pricing",
        16,
    ),
    _row(
        "prd_mixpanel",
        "Mixpanel",
        "按事件查看用户行为的分析工具",
        "Mixpanel 用来看留存、转化和某个功能有没有被用到。本档案不收录流量数字。",
        "analytics",
        "https://mixpanel.com",
        "https://mixpanel.com/pricing",
        17,
    ),
    _row(
        "prd_amplitude",
        "Amplitude",
        "给产品团队用的用户行为分析平台",
        "Amplitude 用来分析用户如何使用产品，包括留存和操作路径。具体指标数值不在本档案中。",
        "analytics",
        "https://amplitude.com",
        "https://amplitude.com/pricing",
        18,
    ),
    _row(
        "prd_loom",
        "Loom",
        "用短视频代替长文字的异步沟通工具",
        "Loom 录下屏幕和讲解，生成链接发给同事，用来说明一个操作步骤。",
        "communication",
        "https://www.loom.com",
        "https://www.loom.com/pricing",
        19,
    ),
    _row(
        "prd_calcom",
        "Cal.com",
        "公布可约时间并完成预订的日程工具",
        "Cal.com 用来设置可预约时段和预订页，也提供可以自己部署的版本。",
        "productivity",
        "https://cal.com",
        "https://cal.com/pricing",
        20,
    ),
    _row(
        "prd_webflow",
        "Webflow",
        "可视化排版并发布网站的工具",
        "Webflow 在画布上排页面，再把站点发布到它的托管环境，常用于营销页和内容站。",
        "design",
        "https://webflow.com",
        "https://webflow.com/pricing",
        21,
    ),
    _row(
        "prd_framer",
        "Framer",
        "在画布上设计并直接发布网站",
        "Framer 把页面设计和站点发布放在一起，适合做展示页。",
        "design",
        "https://www.framer.com",
        "https://www.framer.com/pricing",
        22,
    ),
    _row(
        "prd_airtable",
        "Airtable",
        "用表格管理结构化信息的协作工具",
        "Airtable 以表格为入口组织记录，并提供不同视图、表单和简单的自动化。",
        "productivity",
        "https://www.airtable.com",
        "https://airtable.com/pricing",
        23,
    ),
    _row(
        "prd_asana",
        "Asana",
        "分配任务并跟踪项目进度的协作工具",
        "Asana 把工作拆成任务、负责人和截止日期，方便跨团队看进度。",
        "productivity",
        "https://asana.com",
        "https://asana.com/pricing",
        24,
    ),
    _row(
        "prd_datadog",
        "Datadog",
        "查看基础设施和应用是否正常的监控平台",
        "Datadog 收集指标、日志和链路，用来查看服务运行状况。计费项以官方定价页为准，这里不写金额。",
        "analytics",
        "https://www.datadoghq.com",
        "https://www.datadoghq.com/pricing",
        25,
    ),
    _row(
        "prd_sentry",
        "Sentry",
        "收集线上错误和性能问题的监控服务",
        "Sentry 在程序报错时记下堆栈和上下文，方便开发者定位是哪一次变更引入的。",
        "developer_tools",
        "https://sentry.io",
        "https://sentry.io/pricing",
        26,
    ),
    _row(
        "prd_gitlab",
        "GitLab",
        "包含代码仓库和持续集成的 DevOps 平台",
        "GitLab 提供 Git 仓库、合并请求和流水线，可以云端使用，也可以自己安装。",
        "developer_tools",
        "https://about.gitlab.com",
        "https://about.gitlab.com/pricing",
        27,
    ),
    _row(
        "prd_huggingface",
        "Hugging Face",
        "托管模型、数据集和演示的人工智能社区",
        "Hugging Face 用来发布和试用机器学习模型与数据集，也有面向团队的计算相关能力。",
        "ai",
        "https://huggingface.co",
        "https://huggingface.co/pricing",
        28,
    ),
    _row(
        "prd_replicate",
        "Replicate",
        "用 API 调用托管模型做推理",
        "Replicate 让开发者通过接口运行已发布的模型，完成文本或图像等生成任务。费用以官方定价页为准。",
        "ai",
        "https://replicate.com",
        "https://replicate.com/pricing",
        29,
    ),
    _row(
        "prd_pinecone",
        "Pinecone",
        "提供相似度检索的托管向量数据库",
        "Pinecone 存储向量并按相似度查询，常用来给应用加上检索。容量说明见官方定价页。",
        "ai",
        "https://www.pinecone.io",
        "https://www.pinecone.io/pricing",
        30,
    ),
]


def _validate(rows: list[dict]) -> None:
    if len(rows) < 30:
        raise RuntimeError("catalog must contain at least 30 products")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate product id in catalog")
    orders = [row["display_order"] for row in rows]
    if orders != list(range(1, len(rows) + 1)):
        raise RuntimeError("display_order must be 1..n")
    for row in rows:
        if not str(row["id"]).startswith("prd_"):
            raise RuntimeError(f"product id must start with prd_: {row['id']}")
        if row["category"] not in CATEGORIES:
            raise RuntimeError(f"unknown category on {row['id']}")
        if not str(row["official_url"]).startswith("https://"):
            raise RuntimeError(f"official_url must be https on {row['id']}")
        if not str(row["pricing_source"]).startswith("https://"):
            raise RuntimeError(f"pricing_source must be https on {row['id']}")


_validate(PRODUCTS)
