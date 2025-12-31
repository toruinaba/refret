import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationControlsProps {
    page: number;
    total: number;
    limit: number;
    onPageChange: (page: number) => void;
}

export function PaginationControls({ page, total, limit, onPageChange }: PaginationControlsProps) {
    const totalPages = Math.ceil(total / limit);

    if (totalPages <= 1) return null;

    const handlePrev = () => {
        if (page > 1) onPageChange(page - 1);
    };

    const handleNext = () => {
        if (page < totalPages) onPageChange(page + 1);
    };

    // Simple range generation (could be optimized for large page counts)
    const pages = Array.from({ length: totalPages }, (_, i) => i + 1).filter(p => {
        // Show first, last, and around current page
        return p === 1 || p === totalPages || Math.abs(p - page) <= 2;
    });

    // Add gaps if needed (simple logic handled by rendering dots?) 
    // For now iterate pages and check gaps
    const renderPageNumbers = () => {
        const items = [];
        let prev = 0;

        for (const p of pages) {
            if (prev > 0 && p - prev > 1) {
                items.push(<span key={`gap-${p}`} className="px-2 text-neutral-400">...</span>);
            }
            items.push(
                <button
                    key={p}
                    onClick={() => onPageChange(p)}
                    className={`min-w-[32px] h-8 rounded-md text-sm font-medium transition-colors ${p === page
                            ? "bg-neutral-900 text-white"
                            : "bg-white border border-neutral-200 text-neutral-600 hover:bg-neutral-50"
                        }`}
                >
                    {p}
                </button>
            );
            prev = p;
        }
        return items;
    };

    return (
        <div className="flex items-center justify-center gap-2 py-4">
            <button
                onClick={handlePrev}
                disabled={page === 1}
                className="p-1 rounded-md border border-neutral-200 bg-white text-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-50"
            >
                <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-1">
                {renderPageNumbers()}
            </div>

            <button
                onClick={handleNext}
                disabled={page === totalPages}
                className="p-1 rounded-md border border-neutral-200 bg-white text-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-50"
            >
                <ChevronRight className="w-5 h-5" />
            </button>
        </div>
    );
}
