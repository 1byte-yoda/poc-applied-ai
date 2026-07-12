interface NavigationBarProps {
  onPrev?: () => void;
  onNext?: () => void;
}

export function NavigationBar({ onPrev, onNext }: NavigationBarProps) {
  return (
    <div className="flex items-center justify-between px-6 py-3 bg-white border-t border-gray-200">
      <button
        onClick={onPrev}
        disabled={!onPrev}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 hover:bg-gray-100 disabled:hover:bg-transparent"
        aria-label="Previous lecture"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Previous
      </button>
      <button
        onClick={onNext}
        disabled={!onNext}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-indigo-600 hover:bg-indigo-50 disabled:hover:bg-transparent"
        aria-label="Next lecture"
      >
        Next
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
}
