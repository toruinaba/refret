import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import CalendarHeatmap from 'react-calendar-heatmap'
import 'react-calendar-heatmap/dist/styles.css'
import { subDays } from 'date-fns'
import { api } from "../lib/api"
import type { PracticeLog, JournalStats, Lesson } from "../types"
import { Loader2, BarChart3, ChevronRight, Music, Mic } from "lucide-react"
import { cn } from "../lib/utils"

type Activity =
    | { type: 'log', data: PracticeLog, date: Date }
    | { type: 'lesson', data: Lesson, date: Date }

export function Dashboard() {
    const [stats, setStats] = useState<JournalStats | null>(null)
    const [activities, setActivities] = useState<Activity[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            setLoading(true)
            const [statsData, logsData, lessonsData] = await Promise.all([
                api.getJournalStats(),
                api.getLogs(),
                api.getLessons({ limit: 20 }) // Fetch recent lessons
            ])
            setStats(statsData)

            // Merge and Sort
            const merged: Activity[] = [
                ...logsData.map(l => ({ type: 'log' as const, data: l, date: new Date(l.date) })),
                ...lessonsData.items.map(l => ({ type: 'lesson' as const, data: l, date: new Date(l.date || l.created_at || new Date()) }))
            ].sort((a, b) => b.date.getTime() - a.date.getTime())

            setActivities(merged)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    if (loading && !stats) return <div className="flex justify-center p-20"><Loader2 className="animate-spin" /></div>

    // Transform stats for heatmap
    const heatmapValues = stats?.heatmap.map(h => ({
        date: h.date,
        count: h.duration > 0 ? Math.min(4, Math.ceil(h.duration / 30)) : 0,
        data: h
    })) || []

    return (
        <div className="space-y-8 pb-20">
            {/* Header / Stats */}
            <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-neutral-900">Activity Dashboard</h1>
                        <p className="text-neutral-500 text-sm mt-1">Consistency is key.</p>
                    </div>
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

            {/* Recent Activity */}
            <div className="grid md:grid-cols-3 gap-8">
                <div className="md:col-span-2 space-y-4">
                    <h3 className="font-bold text-lg text-neutral-800 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-orange-500" /> Recent Activity
                    </h3>

                    {activities.length === 0 && <p className="text-neutral-400 italic">No activity yet.</p>}

                    {activities.map((item) => {
                        if (item.type === 'log') {
                            const log = item.data;
                            return (
                                <Link
                                    key={`log-${log.id}`}
                                    to={`/practice/${log.id}`}
                                    className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm hover:shadow-md transition-all group flex gap-4 items-center"
                                >
                                    <div className="flex flex-col items-center justify-center bg-orange-50 text-orange-800 rounded-lg p-2 w-14 shrink-0 border border-orange-100">
                                        <span className="text-[10px] font-bold uppercase">{item.date.toLocaleString('default', { month: 'short' })}</span>
                                        <span className="text-lg font-bold">{item.date.getDate()}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-bold bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded">PRACTICE</span>
                                            <span className="text-sm font-medium text-neutral-900">{log.duration_minutes} min</span>
                                            {log.sentiment && (
                                                <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full border",
                                                    log.sentiment === 'Good' ? "bg-green-50 text-green-700 border-green-100" :
                                                        "bg-neutral-50 text-neutral-600 border-neutral-100"
                                                )}>{log.sentiment}</span>
                                            )}
                                        </div>
                                        <p className="text-sm text-neutral-500 line-clamp-1">{log.notes || "No notes."}</p>
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-neutral-300 group-hover:text-orange-400 transition-colors" />
                                </Link>
                            )
                        } else {
                            const lesson = item.data;
                            return (
                                <Link
                                    key={`lesson-${lesson.id}`}
                                    to={`/lesson/${lesson.id}`}
                                    className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm hover:shadow-md transition-all group flex gap-4 items-center"
                                >
                                    <div className="flex flex-col items-center justify-center bg-indigo-50 text-indigo-800 rounded-lg p-2 w-14 shrink-0 border border-indigo-100">
                                        <span className="text-[10px] font-bold uppercase">{item.date.toLocaleString('default', { month: 'short' })}</span>
                                        <span className="text-lg font-bold">{item.date.getDate()}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-bold bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded">LESSON</span>
                                            <span className="text-sm font-medium text-neutral-900 truncate">{lesson.title}</span>
                                        </div>
                                        <div className="flex gap-1 text-xs text-neutral-400">
                                            {lesson.vocals_path && <span className="flex items-center gap-0.5"><Mic className="w-3 h-3" /> Vocals</span>}
                                            {lesson.guitar_path && <span className="flex items-center gap-0.5"><Music className="w-3 h-3" /> Guitar</span>}
                                        </div>
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-neutral-300 group-hover:text-indigo-400 transition-colors" />
                                </Link>
                            )
                        }
                    })}
                </div>

                {/* Right Column: Stats (or maybe Tips/Goals in future) */}
                <div className="space-y-6">
                    <div className="bg-neutral-900 rounded-2xl p-6 text-white overflow-hidden relative">
                        <div className="relative z-10">
                            <h2 className="text-lg font-bold mb-4">You're doing great!</h2>
                            <p className="text-neutral-400 text-sm mb-4">
                                Keep logging your practice sessions and analyzing your lessons to see improvement.
                            </p>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-white/10 p-3 rounded-lg backdrop-blur-sm">
                                    <p className="text-neutral-400 text-xs uppercase font-bold mb-1">Activity</p>
                                    <p className="text-xl font-bold">{activities.length}</p>
                                </div>
                                <div className="bg-white/10 p-3 rounded-lg backdrop-blur-sm">
                                    <p className="text-neutral-400 text-xs uppercase font-bold mb-1">Streak</p>
                                    <p className="text-xl font-bold text-orange-500">3 <span className="text-xs text-neutral-500">days</span></p>
                                </div>
                            </div>
                        </div>
                        <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-orange-600/20 rounded-full blur-3xl"></div>
                    </div>
                </div>
            </div>
        </div>
    )
}
