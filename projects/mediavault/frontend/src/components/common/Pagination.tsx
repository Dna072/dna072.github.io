interface PaginationProps {
  page: number
  pages: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pages, total, onPageChange }: PaginationProps) {
  if (pages <= 1) return null

  return (
    <div className="mv-flex mv-items-center mv-justify-between" style={{ marginTop: 20 }}>
      <span className="mv-faint" style={{ fontSize: 12 }}>
        {total} asset{total === 1 ? '' : 's'} total
      </span>
      <div className="mv-flex mv-items-center mv-gap-2">
        <button
          className="mv-btn mv-btn-secondary mv-btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </button>
        <span className="mv-muted" style={{ fontSize: 12 }}>
          Page {page} of {pages}
        </span>
        <button
          className="mv-btn mv-btn-secondary mv-btn-sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  )
}
