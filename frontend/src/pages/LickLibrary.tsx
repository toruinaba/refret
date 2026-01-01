import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import type { Lick } from "../types"
import { api } from "../lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card"
import { Tag, Music, ArrowLeft } from "lucide-react"
import { FilterBar } from "../components/ui/FilterBar"
import { PaginationControls } from "../components/ui/PaginationControls"

export function LickLibrary() {
    const [licks, setLicks] = useState<Lick[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Pagination & Filter State
    const [page, setPage] = useState(1)
    const [limit] = useState(12)
    const [total, setTotal] = useState(0)
    const [filters, setFilters] = useState({ tags: [] as string[], dateFrom: "", dateTo: "" })

    useEffect(() => {
        const fetchLicks = async () => {
            setLoading(true)
            try {
                const res = await api.getLicks({
                    page,
                    limit,
                    tags: filters.tags,
                    date_from: filters.dateFrom || undefined,
                    date_to: filters.dateTo || undefined
                })
                setLicks(res.items)
                setTotal(res.total)
            } catch (err) {
                console.error(err)
                setError("Failed to fetch licks.")
            } finally {
                setLoading(false)
            }
        }
        fetchLicks()
    }, [page, filters])

    const handleFilterChange = (newFilters: typeof filters) => {
        setFilters(newFilters)
        setPage(1)
    }

    if (error) return <div className="text-center p-8 text-red-500">{error}</div>

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Link to="/" className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-neutral-600" />
                </Link>
                <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
                    Lick Library 🎸
                </h1>
            </div>

            <FilterBar filters={filters} onFilterChange={handleFilterChange} />

            {loading ? (
                <div className="text-center p-12 text-neutral-500 animate-pulse">Loading licks...</div>
            ) : licks.length === 0 ? (
                <div className="text-center p-12 bg-neutral-50 rounded-lg border border-dashed border-neutral-300 text-neutral-500">
                    <Music className="w-12 h-12 mx-auto mb-4 text-neutral-300" />
                    <p>No licks found.</p>
                    <p className="text-sm">Try adjusting filters or create licks from the Lesson Player.</p>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {licks.map((lick) => (
                            <Link key={lick.id} to={`/lick/${lick.id}`}>
                                <Card className="h-full cursor-pointer hover:border-orange-200 transition-colors">
                                    <CardHeader>
                                        <CardTitle className="truncate" title={lick.title}>
                                            {lick.title}
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex flex-col gap-2 text-sm text-neutral-500">
                                            <div className="flex items-center gap-2">
                                                <Music className="w-4 h-4" />
                                                <span>{lick.lesson_id}</span>
                                            </div>
                                            <div className="text-xs font-mono bg-neutral-100 px-2 py-1 rounded w-fit">
                                                {lick.start.toFixed(2)}s - {lick.end.toFixed(2)}s
                                            </div>
                                            <div className="flex items-center gap-2 flex-wrap mt-1">
                                                <Tag className="w-4 h-4" />
                                                {lick.tags && lick.tags.length > 0 ? (
                                                    <div className="flex gap-1 flex-wrap">
                                                        {lick.tags.slice(0, 5).map(tag => (
                                                            <span key={tag} className="bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full text-xs">
                                                                {tag}
                                                            </span>
                                                        ))}
                                                        {lick.tags.length > 5 && <span>+{lick.tags.length - 5}</span>}
                                                    </div>
                                                ) : (
                                                    <span>No tags</span>
                                                )}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </Link>
                        ))}
                    </div>

                    <PaginationControls page={page} limit={limit} total={total} onPageChange={setPage} />
                </>
            )}
        </div>
    )
}
