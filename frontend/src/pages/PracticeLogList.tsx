import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { ArrowLeft, Search, Calendar, ChevronRight } from "lucide-react"
import { api } from "../lib/api"
import type { PracticeLog } from "../types"
import { cn } from "../lib/utils"

export function PracticeLogList() {
    const [logs, setLogs] = useState<PracticeLog[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState("")

    // Date Filters (Optional, keeping simple for now)
    // const [dateFrom, setDateFrom] = useState("")
    // const [dateTo, setDateTo] = useState("")

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            const data = await api.getLogs()
            setLogs(data)
        } catch (e) {
            console.error("Failed to fetch logs", e)
        } finally {
            setLoading(false)
        }
    }

    const filteredLogs = logs.filter(log => {
        const query = search.toLowerCase()
        return (
            log.notes?.toLowerCase().includes(query) ||
            log.tags?.some(t => t.toLowerCase().includes(query)) ||
            log.date.includes(query)
        )
    })

    return (
        <div className="space-y-6 pb-20">
            {/* Header */}
            <div className="flex flex-col gap-4 border-b border-neutral-200 pb-4">
                <div className="flex items-center gap-4">
                    <Link to="/" className="p-2 hover:bg-neutral-100 rounded-full transition-colors flex-shrink-0">
                        <ArrowLeft className="w-5 h-5 text-neutral-600" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-neutral-900">Practice Logs</h1>
                        <p className="text-neutral-500 text-sm">Review your practice history and progress.</p>
                    </div>
                </div>

                {/* Search / Filter */}
                <div className="flex items-center gap-2 bg-white px-3 py-2 border border-neutral-200 rounded-lg max-w-md w-full shadow-sm focus-within:ring-2 ring-orange-100 transition-all">
                    <Search className="w-4 h-4 text-neutral-400" />
                    <input
                        className="bg-transparent border-none outline-none text-sm w-full placeholder:text-neutral-400"
                        placeholder="Search logs by notes, tags, or date..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>
            </div>

            {/* Content */}
            {loading ? (
                <div className="text-center py-12 text-neutral-400">Loading logs...</div>
            ) : filteredLogs.length === 0 ? (
                <div className="bg-neutral-50 border border-dashed border-neutral-200 rounded-xl p-12 text-center">
                    <Calendar className="w-12 h-12 mx-auto text-neutral-300 mb-4" />
                    <h3 className="text-lg font-medium text-neutral-900">No logs found</h3>
                    <p className="text-neutral-500 mb-6">Try adjusting your search or create a new log.</p>
                    <Link to="/upload" className="inline-flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors">
                        Log Practice
                    </Link>
                </div>
            ) : (
                <div className="grid gap-4">
                    {filteredLogs.map(log => (
                        <Link
                            key={log.id}
                            to={`/practice/${log.id}`}
                            className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm hover:shadow-md transition-all group flex gap-4 items-start"
                        >
                            {/* Date Badge */}
                            <div className="flex flex-col items-center justify-center bg-orange-50 text-orange-800 rounded-lg p-3 w-16 shrink-0 border border-orange-100">
                                <span className="text-xs font-bold uppercase">{new Date(log.date).toLocaleString('default', { month: 'short' })}</span>
                                <span className="text-xl font-bold">{new Date(log.date).getDate()}</span>
                            </div>

                            <div className="flex-1 min-w-0 py-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-medium text-neutral-900 line-clamp-1">
                                        {log.duration_minutes} minutes
                                    </span>
                                    {log.sentiment && (
                                        <span className={cn("text-xs px-2 py-0.5 rounded-full border",
                                            log.sentiment === 'Good' ? "bg-green-50 text-green-700 border-green-100" :
                                                log.sentiment === 'Frustrated' ? "bg-red-50 text-red-700 border-red-100" :
                                                    "bg-neutral-50 text-neutral-600 border-neutral-100"
                                        )}>
                                            {log.sentiment}
                                        </span>
                                    )}
                                    {log.audio_path && (
                                        <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100">
                                            Audio
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-neutral-600 line-clamp-2 mb-2">
                                    {log.notes || "No notes."}
                                </p>
                                <div className="flex flex-wrap gap-1">
                                    {log.tags && log.tags.map(t => (
                                        <span key={t} className="text-[10px] bg-neutral-100 text-neutral-500 px-1.5 py-0.5 rounded">
                                            #{t}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="self-center">
                                <ChevronRight className="w-5 h-5 text-neutral-300 group-hover:text-orange-400 transition-colors" />
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    )
}
