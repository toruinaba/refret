import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Clock, Tag, FileText } from "lucide-react"
import type { Lick } from "../types"
import { api } from "../lib/api"
import { MultiTrackPlayer } from "../components/player/MultiTrackPlayer"

export function LickDetail() {
    const { id } = useParams<{ id: string }>()
    const [lick, setLick] = useState<Lick | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!id) return;
        const fetchLick = async () => {
            try {
                const data = await api.getLick(id)
                setLick(data)
            } catch (err) {
                console.error(err)
                setError("Failed to fetch lick details.")
            } finally {
                setLoading(false)
            }
        }
        fetchLick()
    }, [id])

    if (loading) return <div className="text-center p-8">Loading lick...</div>
    if (error || !lick) return <div className="text-center p-8 text-red-500">{error || "Lick not found"}</div>

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link to="/licks" className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-neutral-600" />
                </Link>
                <div>
                    <div className="flex items-center gap-2 text-neutral-500 text-sm mb-1">
                        <span className="bg-orange-100 text-orange-800 px-2 py-0.5 rounded text-xs font-semibold">Lick</span>
                        <span>From Lesson: <Link to={`/lesson/${lick.lesson_dir}`} className="hover:underline text-orange-600">{lick.lesson_dir}</Link></span>
                    </div>
                    <h1 className="text-2xl font-bold text-neutral-900">{lick.title}</h1>
                </div>
            </div>

            {/* Player */}
            <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200">
                <MultiTrackPlayer
                    lessonId={lick.lesson_dir}
                    initialRegion={{ start: lick.start, end: lick.end }}
                />
            </div>

            {/* Details Card */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-4">
                    <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-sm">
                        <h3 className="flex items-center gap-2 font-semibold text-neutral-900 mb-4">
                            <FileText className="w-4 h-4" /> Memo
                        </h3>
                        <div className="prose prose-sm max-w-none text-neutral-600 whitespace-pre-wrap">
                            {lick.memo || "No memo available."}
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-sm space-y-4">
                        <div>
                            <h4 className="text-xs font-semibold text-neutral-500 uppercase flex items-center gap-2 mb-2">
                                <Clock className="w-3 h-3" /> Timestamp
                            </h4>
                            <p className="text-sm font-mono text-neutral-900">
                                {lick.start.toFixed(2)}s - {lick.end.toFixed(2)}s
                            </p>
                        </div>
                        <div>
                            <h4 className="text-xs font-semibold text-neutral-500 uppercase flex items-center gap-2 mb-2">
                                <Tag className="w-3 h-3" /> Tags
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {lick.tags && lick.tags.length > 0 ? lick.tags.map(tag => (
                                    <span key={tag} className="px-2 py-1 bg-neutral-100 rounded text-xs text-neutral-700">
                                        {tag}
                                    </span>
                                )) : <span className="text-sm text-neutral-400">No tags</span>}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
