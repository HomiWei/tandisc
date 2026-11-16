export const CATEGORY_LABELS: Record<string, string> = {
  developer_tools: "开发工具",
  productivity: "效率",
  ai: "人工智能",
  infra: "基础设施",
  design: "设计",
  payment: "支付",
  analytics: "分析",
  communication: "沟通",
  other: "其他",
};

export const CATEGORY_VALUES = [
  "developer_tools",
  "productivity",
  "ai",
  "infra",
  "design",
  "payment",
  "analytics",
  "communication",
  "other",
] as const;

export function categoryLabel(value: string | null | undefined): string | null {
  if (!value) return null;
  return CATEGORY_LABELS[value] ?? value;
}

export function askStatusLabel(status: string | null): string {
  switch (status) {
    case "answered":
      return "已回答";
    case "insufficient_data":
      return "资料不足";
    case "out_of_scope":
      return "超出范围";
    default:
      return "未知状态";
  }
}
