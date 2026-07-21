import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({
  page,
  totalPages,
  onPrev,
  onNext,
  testIdPrefix = "pagination"
}: {
  page: number;
  totalPages: number;
  onPrev: () => void;
  onNext: () => void;
  testIdPrefix?: string;
}) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between pt-3" data-testid={`${testIdPrefix}-pagination`}>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Page <span className="font-mono">{page + 1}</span> of <span className="font-mono">{totalPages}</span>
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onPrev}
          disabled={page === 0}
          data-testid={`${testIdPrefix}-prev-btn`}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-300 hover:border-brand/40 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
          Prev
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={page >= totalPages - 1}
          data-testid={`${testIdPrefix}-next-btn`}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-300 hover:border-brand/40 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Next
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
