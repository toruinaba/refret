import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import type { Lesson } from "../../types"
import { api } from "../../lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/card"
import { Calendar, Tag, Loader2 } from "lucide-react"
import { FilterBar } from "../../components/ui/FilterBar"
import { PaginationControls } from "../../components/ui/PaginationControls"

export function LessonGrid() {
    const [lessons, setLessons] = useState<Lesson[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Pagination & Filter State
    const [page, setPage] = useState(1)
    const [limit] = useState(12)
    const [total, setTotal] = useState(0)
    const [filters, setFilters] = useState({ tags: [] as string[], dateFrom: "", dateTo: "" })

    useEffect(() => {
        const fetchLessons = async () => {
            setLoading(true)
            try {
                const res = await api.getLessons({
                    page,
                    limit,
                    tags: filters.tags,
                    date_from: filters.dateFrom || undefined,
                    date_to: filters.dateTo || undefined
                })
                setLessons(res.items)
                setTotal(res.total)
            } catch (err) {
                console.error(err)
                setError("Failed to fetch lessons. Is the backend running?")
            } finally {
                setLoading(false)
            }
        }
        fetchLessons()
    }, [page, filters]) // Re-fetch when page or filters change

    const handleFilterChange = (newFilters: typeof filters) => {
        setFilters(newFilters)
        setPage(1) // Reset to first page on filter change
    }

    if (error) return (
        <div className="text-center p-8 text-red-500 bg-red-50 rounded-lg">
            <p>{error}</p>
            <p className="text-sm mt-2">Ensure `start_backend.sh` is running.</p>
        </div>
    )

    return (
        <div className="space-y-6">
            <FilterBar filters={filters} onFilterChange={handleFilterChange} />

            {loading ? (
                <div className="text-center p-12 text-neutral-500 animate-pulse">Loading lessons...</div>
            ) : lessons.length === 0 ? (
                <div className="text-center p-12 text-neutral-500 bg-neutral-50 rounded-xl border border-neutral-100">
                    <p className="font-semibold text-lg mb-2">No lessons found</p>
                    <p className="text-sm">Try adjusting your filters or upload a new lesson.</p>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {lessons.map((lesson) => {
                            const isProcessing = lesson.status && lesson.status !== 'completed';

                            const CardContentWrapper = ({ children }: { children: React.ReactNode }) => (
                                <Card className={`h-full transition-all relative overflow-hidden ${isProcessing ? 'bg-neutral-50/50 border-orange-100' : 'cursor-pointer hover:border-orange-200'}`}>
                                    {isProcessing && (
                                        <div className="absolute inset-x-0 bottom-0 h-1 bg-neutral-100">
                                            <div className="h-full bg-orange-400 animate-progress origin-left w-full"></div>
                                        </div>
                                    )}
                                    {children}
                                </Card>
                            )

                            return (
                                isProcessing ? (
                                    <div key={lesson.id} className="cursor-wait group relative">
                                        <CardContentWrapper>
                                            <CardHeader>
                                                <div className="flex justify-between items-start gap-2">
                                                    <CardTitle className="truncate text-neutral-500" title={lesson.title}>
                                                        {lesson.title}
                                                    </CardTitle>
                                                    <span className="shrink-0 inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700 animate-pulse">
                                                        <Loader2 className="w-3 h-3 animate-spin" />
                                                        Processing
                                                    </span>
                                                </div>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex flex-col gap-2 text-sm text-neutral-400">
                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="w-4 h-4 opacity-50" />
                                                        <span>{lesson.created_at || "Just now"}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Tag className="w-4 h-4 opacity-50" />
                                                        <span>Processing tags...</span>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </CardContentWrapper>
                                    </div>
                                ) : (
                                    <Link key={lesson.id} to={`/lesson/${lesson.id}`}>
                                        <Card className="h-full cursor-pointer hover:border-orange-200 transition-colors">
                                            <CardHeader>
                                                <CardTitle className="truncate" title={lesson.title}>
                                                    {lesson.title}
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex flex-col gap-2 text-sm text-neutral-500">
                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="w-4 h-4" />
                                                        <span>{lesson.created_at || "Unknown Date"}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <Tag className="w-4 h-4" />
                                                        {lesson.tags && lesson.tags.length > 0 ? (
                                                            <div className="flex gap-1 flex-wrap">
                                                                {lesson.tags.slice(0, 3).map(tag => (
                                                                    <span key={tag} className="bg-neutral-100 px-2 py-0.5 rounded-full text-xs">
                                                                        {tag}
                                                                    </span>
                                                                ))}
                                                                {lesson.tags.length > 3 && <span>+{lesson.tags.length - 3}</span>}
                                                            </div>
                                                        ) : (
                                                            <span>No tags</span>
                                                        )}
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    </Link>
                                )
                            )
                        })}
                    </div>

                    <PaginationControls page={page} limit={limit} total={total} onPageChange={setPage} />
                </>
            )}
        </div>
    )
}
