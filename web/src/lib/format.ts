const quantity = new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 4 });

export function formatQuantity(value: number): string {
  return quantity.format(value);
}

export function formatScalar(value: number | string | null): string | null {
  if (value == null) return null;
  if (typeof value === "number") return formatQuantity(value);
  return value;
}

export function safeHttpUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (url.protocol === "http:" || url.protocol === "https:") return url.toString();
  } catch {
    return null;
  }
  return null;
}
