export class ApiError extends Error {
  readonly status: number;
  readonly code: string | undefined;

  constructor(status: number, code: string | undefined, userMessage: string) {
    super(userMessage);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function userMessageForStatus(status: number, code?: string): string {
  if (code === "UPSTREAM_UNAVAILABLE" || status === 503) {
    return "问答服务暂时不可用。榜单和详情仍可查看，请稍后再试。";
  }
  if (code === "NOT_FOUND" || status === 404) {
    return "没有找到这条记录。";
  }
  if (code === "VALIDATION_ERROR" || status === 400) {
    return "请求参数不正确。";
  }
  if (code === "INTERNAL_ERROR" || status === 500) {
    return "服务暂时出错，请稍后再试。";
  }
  return "请求失败，请稍后再试。";
}

export function toUserMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  return "请求失败，请稍后再试。";
}

export function isAbortError(err: unknown): boolean {
  return err instanceof Error && err.name === "AbortError";
}
