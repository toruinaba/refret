import { useState, useEffect } from "react"
import CalendarHeatmap from 'react-calendar-heatmap'
import 'react-calendar-heatmap/dist/styles.css'
import { format, subDays } from 'date-fns'
import { api } from "../lib/api"
import type { PracticeLog, JournalStats } from "../types"
import { TagInput } from "../components/ui/TagInput"
import { Loader2, Plus, Edit2, Trash2 } from "lucide-react"

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
                        <div key={log.id} className="bg-white p-4 rounded-lg border border-neutral-200 shadow-sm hover:shadow-md transition-shadow group">
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-mono font-bold text-neutral-700">{log.date}</span>
                                        <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">{log.duration_minutes}m</span>
                                        {log.sentiment && <span className="text-xs bg-neutral-100 text-neutral-600 px-2 py-0.5 rounded-full">{log.sentiment}</span>}
                                    </div>
                                    <p className="text-sm text-neutral-600 whitespace-pre-wrap">{log.notes}</p>
                                    <div className="flex flex-wrap gap-1 mt-2">
                                        {log.tags?.map(t => <span key={t} className="text-[10px] bg-neutral-50 px-1.5 py-0.5 rounded text-neutral-400">#{t}</span>)}
                                    </div>
                                </div>
                                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button onClick={() => openEdit(log)} className="p-1 hover:bg-neutral-100 rounded text-neutral-500"><Edit2 className="w-4 h-4" /></button>
                                    <button onClick={() => handleDelete(log.id)} className="p-1 hover:bg-red-50 rounded text-red-500"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Editor Panel (Always visible if editing, or maybe sticky?) */}
                <div className="">
                    {isEditing ? (
                        <div className="bg-white p-6 rounded-xl border border-orange-200 shadow-sm sticky top-24 animate-in slide-in-from-right-4">
                            <h3 className="font-bold text-lg mb-4 flex items-center justify-between">
                                <span>{editId ? "Edit Log" : "New Log"}</span>
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

                                <button onClick={handleSave} className="w-full bg-orange-600 text-white py-2 rounded-lg font-medium hover:bg-orange-700">Save Log</button>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-neutral-50 border border-dashed border-neutral-300 rounded-xl p-8 flex flex-col items-center justify-center text-neutral-400 text-center">
                            <Plus className="w-8 h-8 mb-2 opacity-50" />
                            <p>Select a date on the calendar or click "Log Practice" to add an entry.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
