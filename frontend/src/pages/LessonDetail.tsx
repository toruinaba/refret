import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Plus, X } from "lucide-react"
import { MultiTrackPlayer } from "../components/player/MultiTrackPlayer"
import { api } from "../lib/api"

export function LessonDetail() {
    const { id } = useParams<{ id: string }>()
    const [selection, setSelection] = useState<{ start: number, end: number } | null>(null)
    const [isCreating, setIsCreating] = useState(false)

    // Form State
    const [title, setTitle] = useState("")
    const [tags, setTags] = useState("")
    const [memo, setMemo] = useState("")
    const [submitting, setSubmitting] = useState(false)

    const handleSaveLick = async () => {
        if (!id || !selection) return;
        try {
            setSubmitting(true)
            await api.createLick({
                lesson_dir: id,
                title: title || "New Lick",
                tags: tags.split(",").map(t => t.trim()).filter(Boolean),
                memo,
                start: selection.start,
                end: selection.end
            })
            alert("Lick saved!")
            setIsCreating(false)
            setTitle("")
            setTags("")
            setMemo("")
        } catch (e) {
            console.error(e)
            alert("Failed to save lick")
        } finally {
            setSubmitting(false)
        }
    }

    if (!id) return <div>Invalid Lesson ID</div>

    return (
        <div className="space-y-6 relative">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link to="/" className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5 text-neutral-600" />
                    </Link>
                    <h1 className="text-2xl font-bold">{id}</h1>
                </div>

                {selection && !isCreating && (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors animate-in fade-in"
                    >
                        <Plus className="w-4 h-4" /> Save Lick ({selection.start.toFixed(1)}s - {selection.end.toFixed(1)}s)
                    </button>
                )}
            </div>

            <div className="max-w-4xl mx-auto">
                <MultiTrackPlayer lessonId={id} onSelectionChange={setSelection} />
            </div>

            {/* Creation Modal/Overlay */}
            {isCreating && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 animate-in zoom-in-95">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-bold">Save New Lick</h2>
                            <button onClick={() => setIsCreating(false)}><X className="w-5 h-5 text-neutral-400 hover:text-neutral-600" /></button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Title</label>
                                <input
                                    value={title} onChange={e => setTitle(e.target.value)}
                                    className="w-full border border-neutral-300 rounded-md px-3 py-2"
                                    placeholder="Awesome Lick"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Tags (comma separated)</label>
                                <input
                                    value={tags} onChange={e => setTags(e.target.value)}
                                    className="w-full border border-neutral-300 rounded-md px-3 py-2"
                                    placeholder="blues, slow, bend"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Memo</label>
                                <textarea
                                    value={memo} onChange={e => setMemo(e.target.value)}
                                    className="w-full border border-neutral-300 rounded-md px-3 py-2 h-24"
                                    placeholder="Notes about fingering, difficulty etc."
                                />
                            </div>

                            <div className="text-xs text-neutral-500 bg-neutral-100 p-2 rounded">
                                Range: {selection?.start.toFixed(2)}s - {selection?.end.toFixed(2)}s
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-4">
                            <button onClick={() => setIsCreating(false)} className="px-4 py-2 text-neutral-600 hover:bg-neutral-100 rounded-lg">Cancel</button>
                            <button
                                onClick={handleSaveLick} disabled={submitting}
                                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
                            >
                                {submitting ? "Saving..." : "Save Lick"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
