import { useState, useEffect } from "react";
import { Filter, Calendar, X } from "lucide-react";
import { api } from "../../lib/api";
import { TagInput } from "./TagInput";
import { clsx } from "clsx";

interface FilterState {
    tags: string[];
    dateFrom: string;
    dateTo: string;
}

interface FilterBarProps {
    filters: FilterState;
    onFilterChange: (filters: FilterState) => void;
    className?: string;
}

export function FilterBar({ filters, onFilterChange, className }: FilterBarProps) {
    const [allTags, setAllTags] = useState<string[]>([]);

    useEffect(() => {
        api.getTags().then(tags => setAllTags(tags)).catch(console.error);
    }, []);

    const handleChange = (key: keyof FilterState, value: any) => {
        onFilterChange({ ...filters, [key]: value });
    };

    const hasFilters = filters.tags.length > 0 || filters.dateFrom || filters.dateTo;

    return (
        <div className={clsx("bg-white p-4 rounded-xl border border-neutral-200 shadow-sm space-y-4", className)}>
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-neutral-700 flex items-center gap-2">
                    <Filter className="w-4 h-4 text-orange-600" />
                    Filters
                </h3>
                {hasFilters && (
                    <button
                        onClick={() => onFilterChange({ tags: [], dateFrom: "", dateTo: "" })}
                        className="text-xs text-neutral-500 hover:text-neutral-900 flex items-center gap-1"
                    >
                        <X className="w-3 h-3" /> Clear All
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Tag Filter */}
                <div className="space-y-1">
                    <label className="text-xs font-semibold text-neutral-500 uppercase">Tags</label>
                    <TagInput
                        value={filters.tags}
                        onChange={(tags) => handleChange("tags", tags)}
                        suggestions={allTags}
                        placeholder="Filter by tags..."
                    />
                </div>

                {/* Date Filter */}
                <div className="space-y-1">
                    <label className="text-xs font-semibold text-neutral-500 uppercase flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Date Range
                    </label>
                    <div className="flex gap-2 items-center">
                        <input
                            type="date"
                            value={filters.dateFrom}
                            onChange={e => handleChange("dateFrom", e.target.value)}
                            className="bg-neutral-50 border border-neutral-300 rounded-md px-2 py-1.5 text-sm w-full outline-none focus:ring-2 focus:ring-orange-500 font-mono"
                        />
                        <span className="text-neutral-400">-</span>
                        <input
                            type="date"
                            value={filters.dateTo}
                            onChange={e => handleChange("dateTo", e.target.value)}
                            className="bg-neutral-50 border border-neutral-300 rounded-md px-2 py-1.5 text-sm w-full outline-none focus:ring-2 focus:ring-orange-500 font-mono"
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
