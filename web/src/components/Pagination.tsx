export function Pagination({
  page,
  pageSize,
  total,
  onPage,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}) {
  if (total <= 0) return null;
  const size = Math.max(pageSize, 1);
  const totalPages = Math.max(1, Math.ceil(total / size));
  if (totalPages <= 1 && page <= 1) return null;
  return (
    <nav className="pager" aria-label="分页">
      <button type="button" data-testid="pager-prev" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        上一页
      </button>
      <span>
        第 {page} 页，共 {total} 条，每页 {size} 条
      </span>
      <button type="button" data-testid="pager-next" disabled={page >= totalPages} onClick={() => onPage(page + 1)}>
        下一页
      </button>
    </nav>
  );
}
