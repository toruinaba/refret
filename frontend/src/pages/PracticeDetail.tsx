import { useState, useEffect, useRef } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import { ArrowLeft, Calendar, Edit2, Trash2, Plus, Save } from "lucide-react"
import { api } from "../lib/api"
import type { PracticeLog } from "../types"
import { MultiTrackPlayer, type MultiTrackPlayerRef } from "../components/player/MultiTrackPlayer"
import { CreateLickDialog } from "../components/licks/CreateLickDialog"
import { TagInput } from "../components/ui/TagInput"
import { cn } from "../lib/utils"

export function PracticeDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const [log, setLog] = useState<PracticeLog | null>(null)
    const [loading, setLoading] = useState(true)

    // Player State
    const playerRef = useRef<MultiTrackPlayerRef>(null)
    const [selection, setSelection] = useState<{ start: number, end: number } | null>(null)

    // Edit State
    const [isEditing, setIsEditing] = useState(false)
    const [editNotes, setEditNotes] = useState("")
    const [editTags, setEditTags] = useState<string[]>([])
    const [editSentiment, setEditSentiment] = useState("")
    const [editDate, setEditDate] = useState("")
    const [editDuration, setEditDuration] = useState(0)

    // Lick Creation
    const [isCreatingLick, setIsCreatingLick] = useState(false)

    useEffect(() => {
        if (id) loadData()
    }, [id])

    const loadData = async () => {
        try {
            setLoading(true)
            const data = await api.getLog(Number(id))
            setLog(data)

            // Init edit state
            setEditNotes(data.notes || "")
            setEditTags(data.tags || [])
            setEditSentiment(data.sentiment || "")
            setEditDate(data.date)
            setEditDuration(data.duration_minutes)
        } catch (e) {
            console.error("Failed to load log", e)
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        if (!log) return
        try {
            const updated = await api.updateLog(log.id, {
                date: editDate,
                duration_minutes: editDuration,
                notes: editNotes,
                tags: editTags,
                sentiment: editSentiment
            })
            setLog(updated)
            setIsEditing(false)
            alert("Log updated!")
        } catch (e) {
            console.error(e)
            alert("Failed to update log")
        }
    }

    const handleDelete = async () => {
        if (!log) return
        if (window.confirm("Are you sure you want to delete this log?")) {
            try {
                await api.deleteLog(log.id)
                alert("Log deleted")
                navigate("/practice")
            } catch (e) {
                console.error(e)
                alert("Failed to delete log")
            }
        }
    }

    const handleSaveLick = async (title: string, tags: string[], memo: string) => {
        if (!log || !selection) return
        try {
            await api.createLick({
                practice_log_id: log.id,
                title: title,
                tags: tags,
                memo: memo,
                start: selection.start,
                end: selection.end,
                lesson_id: undefined // Explicitly undefined as per new schema logic if needed, but backend handles optional
            })
            alert("Lick saved!")
            setIsCreatingLick(false)
        } catch (e) {
            console.error(e)
            alert("Failed to save lick")
        }
    }

    if (loading) return <div className="p-8 text-center text-neutral-400">Loading log...</div>
    if (!log) return <div className="p-8 text-center text-neutral-400">Log not found</div>

    return (
        <div className="space-y-6 pb-20">
            {/* Header */}
            <div className="flex items-center gap-4 border-b border-neutral-200 pb-4">
                <Link to="/practice" className="p-2 hover:bg-neutral-100 rounded-full transition-colors flex-shrink-0">
                    <ArrowLeft className="w-5 h-5 text-neutral-600" />
                </Link>
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 text-xs font-mono text-neutral-500 uppercase tracking-widest">
                        Practice Session
                    </div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold text-neutral-900">{log.date}</h1>
                        <span className={cn("text-sm px-2 py-0.5 rounded-full border",
                            log.sentiment === 'Good' ? "bg-green-50 text-green-700 border-green-100" :
                                log.sentiment === 'Frustrated' ? "bg-red-50 text-red-700 border-red-100" :
                                    "bg-neutral-50 text-neutral-600 border-neutral-100"
                        )}>
                            {log.sentiment || "Neutral"}
                        </span>
                    </div>
                </div>

                <div className="flex gap-2">
                    {isEditing ? (
                        <>
                            <button
                                onClick={() => setIsEditing(false)}
                                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-neutral-600 bg-white border border-neutral-200 rounded-lg hover:bg-neutral-50"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                <span className="hidden sm:inline">Cancel</span>
                            </button>
                            <button
                                onClick={handleSave}
                                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-orange-600 rounded-lg hover:bg-orange-700"
                            >
                                <Save className="w-4 h-4" />
                                <span className="hidden sm:inline">Save</span>
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={() => setIsEditing(true)}
                            className="p-2 sm:px-3 sm:py-2 flex items-center gap-2 text-sm font-medium text-neutral-600 bg-white border border-neutral-200 rounded-lg hover:bg-neutral-50"
                            title="Edit Log"
                        >
                            <Edit2 className="w-4 h-4" />
                            <span className="hidden sm:inline">Edit</span>
                        </button>
                    )}
                    <button
                        onClick={handleDelete}
                        className="p-2 sm:px-3 sm:py-2 flex items-center gap-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50"
                        title="Delete Log"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-8 items-start">
                {/* Left Column: Player */}
                <div className="lg:col-span-2 space-y-6 min-w-0">
                    {log.audio_path ? (
                        <div className="space-y-4">
                            <MultiTrackPlayer
                                ref={playerRef}
                                mode="single"
                                audioUrl={`/api/journal/${log.id}/audio`}
                                analysisData={log.analysis}
                                onSelectionChange={setSelection}
                            />

                            {/* Actions Bar */}
                            {selection && !isCreatingLick && (
                                <div className="flex justify-end animate-in fade-in slide-in-from-top-2">
                                    <button
                                        onClick={() => setIsCreatingLick(true)}
                                        className="flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors font-medium shadow-sm text-sm"
                                    >
                                        <Plus className="w-4 h-4" />
                                        Save Lick ({selection.start.toFixed(1)}s - {selection.end.toFixed(1)}s)
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="bg-neutral-50 border border-dashed border-neutral-200 rounded-xl p-8 text-center text-neutral-400">
                            No audio recording for this session.
                        </div>
                    )}

                    {/* Content Section */}
                    <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm">
                        <div className="flex items-center gap-2 mb-4">
                            <Calendar className="w-5 h-5 text-orange-600" />
                            <h3 className="font-bold text-neutral-900">Notes</h3>
                        </div>

                        {isEditing ? (
                            <textarea
                                value={editNotes}
                                onChange={e => setEditNotes(e.target.value)}
                                className="w-full h-48 border border-neutral-300 rounded-lg p-4 font-mono text-sm focus:ring-2 focus:ring-orange-500 outline-none"
                                placeholder="Reflect on your practice..."
                            />
                        ) : (
                            <div className="prose prose-sm max-w-none text-neutral-600 whitespace-pre-wrap">
                                {log.notes || <span className="text-neutral-400 italic">No notes added.</span>}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Metadata */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm space-y-6">
                        <h3 className="font-bold text-neutral-900 border-b border-neutral-100 pb-2">Details</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="text-xs font-bold text-neutral-400 uppercase mb-1 block">Date</label>
                                {isEditing ? (
                                    <input type="date" value={editDate} onChange={e => setEditDate(e.target.value)} className="w-full border border-neutral-300 rounded px-2 py-1.5 text-sm" />
                                ) : (
                                    <div className="font-mono text-neutral-700">{log.date}</div>
                                )}
                            </div>

                            <div>
                                <label className="text-xs font-bold text-neutral-400 uppercase mb-1 block">Duration</label>
                                {isEditing ? (
                                    <input type="number" value={editDuration} onChange={e => setEditDuration(Number(e.target.value))} className="w-full border border-neutral-300 rounded px-2 py-1.5 text-sm" />
                                ) : (
                                    <div className="font-mono text-neutral-700">{log.duration_minutes} min</div>
                                )}
                            </div>

                            <div>
                                <label className="text-xs font-bold text-neutral-400 uppercase mb-1 block">Sentiment</label>
                                {isEditing ? (
                                    <select value={editSentiment} onChange={e => setEditSentiment(e.target.value)} className="w-full border border-neutral-300 rounded px-2 py-1.5 text-sm">
                                        <option value="">Select...</option>
                                        <option value="Good">🔥 Good</option>
                                        <option value="Neutral">😐 Neutral</option>
                                        <option value="Frustrated">😫 Frustrated</option>
                                        <option value="Tired">😴 Tired</option>
                                    </select>
                                ) : (
                                    <div className="font-mono text-neutral-700">{log.sentiment || "--"}</div>
                                )}
                            </div>

                            <div>
                                <label className="text-xs font-bold text-neutral-400 uppercase mb-1 block">Tags</label>
                                {isEditing ? (
                                    <TagInput value={editTags} onChange={setEditTags} placeholder="tags..." />
                                ) : (
                                    <div className="flex flex-wrap gap-2">
                                        {log.tags && log.tags.length > 0 ? log.tags.map(t => (
                                            <span key={t} className="px-2 py-1 bg-neutral-100 text-neutral-600 rounded text-xs">#{t}</span>
                                        )) : <span className="text-neutral-400 text-sm">--</span>}
                                    </div>
                                )}
                            </div>
                        </div>


                    </div>
                </div>
            </div>

            <CreateLickDialog
                isOpen={isCreatingLick}
                onClose={() => setIsCreatingLick(false)}
                onSave={handleSaveLick}
                selection={selection}
            />
        </div>
    )
}
