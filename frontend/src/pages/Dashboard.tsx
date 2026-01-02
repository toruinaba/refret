import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import CalendarHeatmap from 'react-calendar-heatmap'
import 'react-calendar-heatmap/dist/styles.css'
import { format, subDays } from 'date-fns'
import { api } from "../lib/api"
import type { PracticeLog, JournalStats } from "../types"
import { TagInput } from "../components/ui/TagInput"
import { UniversalUploader } from "../components/UniversalUploader"
import { Loader2, Plus, Edit2, Trash2, BarChart3 } from "lucide-react"
import { cn } from "../lib/utils"

export function Dashboard() {
    const [stats, setStats] = useState<JournalStats | null>(null)
    const [recentLogs, setRecentLogs] = useState<PracticeLog[]>([])
    const [loading, setLoading] = useState(true)

    // Editing State
    const [isEditing, setIsEditing] = useState(false)
    const [editId, setEditId] = useState<number | null>(null)
    const [editDate, setEditDate] = useState(format(new Date(), 'yyyy-MM-dd'))
    const [editDuration, setEditDuration] = useState(30)
    const [editNotes, setEditNotes] = useState("")
    const [editTags, setEditTags] = useState<string[]>([])
    const [editSentiment, setEditSentiment] = useState("")

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            setLoading(true)
            const [statsData, logsData] = await Promise.all([
                api.getJournalStats(),
                api.getLogs() // Fetch all recent logs (backend defaults to sort DESC)
            ])
            setStats(statsData)
            setRecentLogs(logsData)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    const handleDayClick = (value: { date: string, count: number } | null) => {
        if (!value) return

        // Find log for this date to edit, or setup new
        const existingLog = recentLogs.find(l => l.date === value.date)
        if (existingLog) {
            openEdit(existingLog)
        } else {
            // New entry for clicked date
            openNew(value.date)
        }
    }

    const openNew = (dateStr?: string) => {
        setEditId(null)
        setEditDate(dateStr || format(new Date(), 'yyyy-MM-dd'))
        setEditDuration(30)
        setEditNotes("")
        setEditTags([])
        setEditSentiment("")
        setIsEditing(true)
    }

    const openEdit = (log: PracticeLog) => {
        setEditId(log.id)
        setEditDate(log.date)
        setEditDuration(log.duration_minutes)
        setEditNotes(log.notes || "")
        setEditTags(log.tags || [])
        setEditSentiment(log.sentiment || "")
        setIsEditing(true)
    }

    const handleSave = async () => {
        try {
            const data = {
                date: editDate,
                duration_minutes: editDuration,
                notes: editNotes,
                tags: editTags,
                sentiment: editSentiment
            }
            if (editId) {
                await api.updateLog(editId, data)
            } else {
                await api.createLog(data)
            }
            setIsEditing(false)
            loadData() // Refresh
        } catch (e) {
            alert("Failed to save log")
            console.error(e)
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm("Delete this log?")) return
        try {
            await api.deleteLog(id)
            loadData()
        } catch (e) {
            console.error(e)
        }
    }

    if (loading && !stats) return <div className="flex justify-center p-20"><Loader2 className="animate-spin" /></div>

    // Transform stats for heatmap
    // CalendarHeatmap expects { date: 'yyyy-mm-dd', count: number }
    // Our stats.heatmap is { date, count, duration }
    const heatmapValues = stats?.heatmap.map(h => ({
        date: h.date,
        count: h.duration > 0 ? Math.min(4, Math.ceil(h.duration / 30)) : 0, // Scale 0-4
        data: h
    })) || []

    return (
        <div className="space-y-8 pb-20">
            {/* Header / Stats */}
            <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-neutral-900">Practice Dashboard</h1>
                        <p className="text-neutral-500 text-sm mt-1">Consistency is key.</p>
                    </div>
                    <button onClick={() => openNew()} className="bg-neutral-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-neutral-800 flex items-center gap-2">
                        <Plus className="w-4 h-4" /> Log Practice
                    </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-neutral-50 p-4 rounded-lg">
                        <span className="text-xs font-bold text-neutral-400 uppercase">Total Hours</span>
                        <p className="text-2xl font-mono mt-1">{(stats?.total_minutes || 0) / 60 | 0}<span className="text-sm text-neutral-400">h</span></p>
                    </div>
                    <div className="bg-neutral-50 p-4 rounded-lg">
                        <span className="text-xs font-bold text-neutral-400 uppercase">This Week</span>
                        <p className="text-2xl font-mono mt-1">{(stats?.week_minutes || 0) / 60 | 0}<span className="text-sm text-neutral-400">h</span></p>
                    </div>
                    {/* Add streak or other stats here */}
                </div>

                <div className="w-full overflow-x-auto bg-white p-4 rounded-lg border border-neutral-200">
                    <div className="min-w-[600px]">
                        <CalendarHeatmap
                            startDate={subDays(new Date(), 365)}
                            endDate={new Date()}
                            values={heatmapValues}
                            classForValue={(value) => {
                                if (!value || value.count === 0) return 'color-empty';
                                return `color-scale-${value.count}`;
                            }}
                            onClick={(value) => handleDayClick(value as any)}
                            tooltipDataAttrs={(value: any) => {
                                if (!value || !value.date) return { 'data-tip': 'No data' } as any
                                const minutes = value.data ? value.data.duration : 0
                                return {
                                    'data-tip': `${value.date}: ${minutes} mins`,
                                } as any
                            }}
                            showWeekdayLabels
                        />
                    </div>
                </div>
                <style>{`
                    .react-calendar-heatmap .color-empty { fill: #e5e5e5; }
                    .react-calendar-heatmap .color-scale-1 { fill: #ffedd5; }
                    .react-calendar-heatmap .color-scale-2 { fill: #fdba74; }
                    .react-calendar-heatmap .color-scale-3 { fill: #f97316; }
                    .react-calendar-heatmap .color-scale-4 { fill: #c2410c; }
                    .react-calendar-heatmap text { font-size: 10px; fill: #9ca3af; }
                `}</style>
            </div>

            {/* Recent Logs & Log Editor */}
            <div className="grid md:grid-cols-2 gap-8">
                {/* Recent Logs List */}
                <div className="space-y-4">
                    <h3 className="font-bold text-lg text-neutral-800">Recent Entries</h3>
                    {recentLogs.length === 0 && <p className="text-neutral-400 italic">No logs yet.</p>}
                    {recentLogs.map(log => (
                        <Link
                            key={log.id}
                            to={`/practice/${log.id}`}
                            className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm hover:shadow-md transition-all group flex gap-4 items-center"
                        >
                            {/* Date Badge */}
                            <div className="flex flex-col items-center justify-center bg-orange-50 text-orange-800 rounded-lg p-2 w-14 shrink-0 border border-orange-100">
                                <span className="text-[10px] font-bold uppercase">{new Date(log.date).toLocaleString('default', { month: 'short' })}</span>
                                <span className="text-lg font-bold">{new Date(log.date).getDate()}</span>
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-medium text-neutral-900">
                                        {log.duration_minutes} min
                                    </span>
                                    {log.sentiment && (
                                        <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full border",
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
                                <p className="text-sm text-neutral-500 line-clamp-1">
                                    {log.notes || "No notes."}
                                </p>

                                <div className="flex flex-wrap gap-1 mt-2">
                                    {log.tags?.map(t => <span key={t} className="text-[10px] bg-neutral-50 px-1.5 py-0.5 rounded text-neutral-400">#{t}</span>)}
                                </div>
                            </div>

                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={(e) => { e.preventDefault(); openEdit(log); }}
                                    className="p-1 hover:bg-neutral-100 rounded text-neutral-500"
                                >
                                    <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={(e) => { e.preventDefault(); handleDelete(log.id); }}
                                    className="p-1 hover:bg-red-50 rounded text-red-500"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </Link>
                    ))}
                </div>

                {/* Editor Panel */}
                <div className="">
                    {isEditing ? (
                        editId ? (
                            // Edit Mode (Legacy Form for now)
                            <div className="bg-white p-6 rounded-xl border border-orange-200 shadow-sm sticky top-24 animate-in slide-in-from-right-4">
                                <h3 className="font-bold text-lg mb-4 flex items-center justify-between">
                                    <span>Edit Log</span>
                                    <button onClick={() => setIsEditing(false)} className="text-neutral-400 hover:text-neutral-600 text-sm">Cancel</button>
                                </h3>

                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-semibold text-neutral-500 uppercase mb-1">Date</label>
                                            <input type="date" value={editDate} onChange={e => setEditDate(e.target.value)} className="w-full border border-neutral-300 rounded-md px-3 py-2" />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-semibold text-neutral-500 uppercase mb-1">Minutes</label>
                                            <input type="number" value={editDuration} onChange={e => setEditDuration(Number(e.target.value))} className="w-full border border-neutral-300 rounded-md px-3 py-2" />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-neutral-500 uppercase mb-1">Notes</label>
                                        <textarea
                                            value={editNotes}
                                            onChange={e => setEditNotes(e.target.value)}
                                            className="w-full border border-neutral-300 rounded-md px-3 py-2 h-32"
                                            placeholder="What did you practice today? What was hard?"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-neutral-500 uppercase mb-1">Tags</label>
                                        <TagInput value={editTags} onChange={setEditTags} placeholder="scales, songs..." />
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-neutral-500 uppercase mb-1">Sentiment</label>
                                        <select value={editSentiment} onChange={e => setEditSentiment(e.target.value)} className="w-full border border-neutral-300 rounded-md px-3 py-2">
                                            <option value="">Select...</option>
                                            <option value="Good">🔥 Good</option>
                                            <option value="Neutral">😐 Neutral</option>
                                            <option value="Frustrated">😫 Frustrated</option>
                                            <option value="Tired">😴 Tired</option>
                                        </select>
                                    </div>

                                    <button onClick={handleSave} className="w-full bg-orange-600 text-white py-2 rounded-lg font-medium hover:bg-orange-700">Save Changes</button>
                                </div>
                            </div>
                        ) : (
                            // New Log Mode (Unified Uploader)
                            <div className="sticky top-24 animate-in slide-in-from-right-4">
                                <div className="flex justify-end mb-2">
                                    <button onClick={() => setIsEditing(false)} className="text-neutral-400 hover:text-neutral-600 text-sm">Cancel</button>
                                </div>
                                <UniversalUploader
                                    defaultTab={1}
                                    onSuccess={() => {
                                        setIsEditing(false);
                                        loadData();
                                    }}
                                />
                            </div>
                        )
                    ) : (
                        <div className="bg-neutral-50 border border-dashed border-neutral-300 rounded-xl p-8 flex flex-col items-center justify-center text-neutral-400 text-center">
                            <Plus className="w-8 h-8 mb-2 opacity-50" />
                            <p>Select a date on the calendar or click "Log Practice" to add an entry.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Stats Overview */}
            <div className="bg-neutral-900 rounded-2xl p-6 text-white overflow-hidden relative">
                <div className="relative z-10">
                    <h2 className="text-lg font-bold mb-6 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-orange-500" />
                        Activity
                    </h2>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                            <p className="text-neutral-400 text-xs uppercase font-bold mb-1">Total Time</p>
                            <p className="text-2xl font-bold">{Math.round(stats?.total_minutes || 0 / 60)}h <span className="text-sm text-neutral-500">{(stats?.total_minutes || 0) % 60}m</span></p>
                        </div>
                        <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                            <p className="text-neutral-400 text-xs uppercase font-bold mb-1">This Week</p>
                            <p className="text-2xl font-bold">{Math.round(stats?.week_minutes || 0 / 60)}h <span className="text-sm text-neutral-500">{(stats?.week_minutes || 0) % 60}m</span></p>
                        </div>
                        <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                            <p className="text-neutral-400 text-xs uppercase font-bold mb-1">Logs</p>
                            <p className="text-2xl font-bold">{recentLogs.length}</p>
                        </div>
                        <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                            <p className="text-neutral-400 text-xs uppercase font-bold mb-1">Streak</p>
                            <p className="text-2xl font-bold text-orange-500">3 <span className="text-sm text-neutral-500">days</span></p>
                        </div>
                    </div>
                </div>

                {/* Decorative background */}
                <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-orange-600/20 rounded-full blur-3xl"></div>
            </div>
        </div>
    )
}
