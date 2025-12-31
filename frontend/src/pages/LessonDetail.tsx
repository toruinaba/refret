import { useState, useEffect, useRef } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Plus, X, FileText, Tag, Calendar, PlayCircle, ChevronDown, ChevronRight, Music } from "lucide-react"
import { MultiTrackPlayer, type MultiTrackPlayerRef } from "../components/player/MultiTrackPlayer"
import { api } from "../lib/api"
import type { LessonDetail as LessonDetailType } from "../types"
import { TagInput } from "../components/ui/TagInput"
import { MarkdownEditor } from "../components/ui/MarkdownEditor"
import { MarkdownRenderer } from '../components/ui/MarkdownRenderer'

export function LessonDetail() {
    const { id } = useParams<{ id: string }>()
    const [lesson, setLesson] = useState<LessonDetailType | null>(null)
    const [selection, setSelection] = useState<{ start: number, end: number } | null>(null)
    const [isCreating, setIsCreating] = useState(false)

    // Refs
    const playerRef = useRef<MultiTrackPlayerRef>(null)

    // UI State
    const [showTranscript, setShowTranscript] = useState(false)

    // Metadata Edit State
    const [isEditing, setIsEditing] = useState(false)
    const [editTags, setEditTags] = useState<string[]>([])
    const [editMemo, setEditMemo] = useState("")


    // Form State (for new Lick)
    const [createTitle, setCreateTitle] = useState("")
    const [createTags, setCreateTags] = useState("")
    const [createMemo, setCreateMemo] = useState("")
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
        if (!id) return;
        api.getLesson(id).then((data) => {
            setLesson(data as LessonDetailType)
            setEditTags(data.tags || [])
            setEditMemo(data.memo || "")

        }).catch(console.error)
    }, [id])

    const handleSaveMetadata = async () => {
        if (!id) return
        try {
            await api.updateLesson(id, { tags: editTags, memo: editMemo })
            setLesson(prev => prev ? ({ ...prev, tags: editTags, memo: editMemo }) : null)

            setIsEditing(false)
            alert("Metadata saved successfully!")
        } catch (e) {
            console.error(e)
            alert("Failed to save metadata")
        }
    }

    const handleSeek = (ts: string) => {
        // Remove brackets if any, e.g. [01:23] -> 01:23
        const cleanTs = ts.replace(/[\[\]]/g, "");
        const parts = cleanTs.split(":").map(Number);
        if (parts.length === 2) {
            const time = parts[0] * 60 + parts[1];
            console.log(`Seeking to: ${ts} -> ${time}s`);
            playerRef.current?.seekTo(time);
        } else {
            console.warn("Invalid timestamp format:", ts);
        }
    }

    const handleSaveLick = async () => {
        if (!id || !selection) return;
        try {
            setSubmitting(true)
            await api.createLick({
                lesson_dir: id,
                title: createTitle || "New Lick",
                tags: createTags.split(",").map(t => t.trim()).filter(Boolean),
                memo: createMemo,
                start: selection.start,
                end: selection.end
            })
            alert("Lick saved!")
            setIsCreating(false)
            setCreateTitle("")
            setCreateTags("")
            setCreateMemo("")
        } catch (e) {
            console.error(e)
            alert("Failed to save lick")
        } finally {
            setSubmitting(false)
        }
    }

    if (!id) return <div>Invalid Lesson ID</div>

    return (
        <div className="space-y-6 relative pb-20">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link to="/" className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5 text-neutral-600" />
                    </Link>
                    <div className="flex flex-col">
                        <span className="text-xs text-neutral-500 font-mono">{id}</span>
                        <h1 className="text-2xl font-bold">{lesson?.title || id}</h1>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {selection && !isCreating && (
                        <button
                            onClick={() => setIsCreating(true)}
                            className="flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors animate-in fade-in"
                        >
                            <Plus className="w-4 h-4" /> Save Lick ({selection.start.toFixed(1)}s - {selection.end.toFixed(1)}s)
                        </button>
                    )}

                    {isEditing ? (
                        <>
                            <button onClick={() => setIsEditing(false)} className="px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-100 rounded-md">
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveMetadata}
                                className="px-3 py-2 text-sm bg-neutral-900 text-white hover:bg-neutral-800 rounded-md shadow-sm"
                            >
                                Save Changes
                            </button>
                        </>
                    ) : (
                        <button onClick={() => setIsEditing(true)} className="px-3 py-2 text-sm border border-neutral-200 hover:bg-neutral-50 rounded-md text-neutral-700">
                            Edit Details
                        </button>
                    )}
                </div>
            </div>

            <div className="max-w-4xl mx-auto space-y-8">
                <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200 shadow-sm sticky top-4 z-20">
                    <MultiTrackPlayer ref={playerRef} lessonId={id} onSelectionChange={setSelection} />
                </div>

                {/* AI Analysis Section (Summary & Key Points) */}
                {lesson && (lesson.summary || (lesson.key_points && lesson.key_points.length > 0)) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-bottom-4 duration-500">
                        {/* Summary Card */}
                        <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm space-y-4">
                            <h3 className="flex items-center gap-2 font-semibold text-neutral-900 border-b border-neutral-100 pb-2">
                                <FileText className="w-4 h-4 text-orange-600" /> Summary
                            </h3>
                            <p className="text-sm text-neutral-600 leading-relaxed whitespace-pre-wrap">
                                {lesson.summary || "No summary available."}
                            </p>

                            {/* Chords if any */}
                            {lesson.chords && lesson.chords.length > 0 && (
                                <div className="pt-4 border-t border-neutral-100">
                                    <h4 className="text-xs font-semibold text-neutral-500 uppercase mb-2">Chords Mentioned</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {lesson.chords.map(chord => (
                                            <span key={chord} className="px-2 py-1 bg-yellow-50 text-yellow-700 border border-yellow-100 rounded text-xs font-mono font-bold">
                                                {chord}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Key Points Card */}
                        <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm space-y-4">
                            <h3 className="flex items-center gap-2 font-semibold text-neutral-900 border-b border-neutral-100 pb-2">
                                <Music className="w-4 h-4 text-orange-600" /> Key Points
                            </h3>
                            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                                {lesson.key_points?.map((kp, i) => {
                                    const isStr = typeof kp === 'string';
                                    const timestamp = isStr ? null : (kp as any).timestamp;
                                    const point = isStr ? kp : (kp as any).point;

                                    return (
                                        <div key={i} className="flex gap-3 items-start group hover:bg-neutral-50 p-2 rounded-lg transition-colors">
                                            {timestamp && (
                                                <button
                                                    onClick={() => handleSeek(timestamp)}
                                                    className="flex items-center gap-1.5 text-xs font-mono bg-orange-100 text-orange-700 px-2 py-1.5 rounded hover:bg-orange-200 transition-colors shrink-0 mt-0.5"
                                                >
                                                    <PlayCircle className="w-3 h-3" />
                                                    {timestamp}
                                                </button>
                                            )}
                                            <p className="text-sm text-neutral-700">{point}</p>
                                        </div>
                                    )
                                })}
                                {(!lesson.key_points || lesson.key_points.length === 0) && (
                                    <p className="text-neutral-400 text-sm italic">No key points extracted.</p>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Transcript Accordion */}
                {lesson && (
                    <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
                        <button
                            onClick={() => setShowTranscript(!showTranscript)}
                            className="w-full flex items-center justify-between p-4 bg-neutral-50 hover:bg-white transition-colors border-b border-neutral-100"
                        >
                            <span className="font-semibold text-sm text-neutral-700 flex items-center gap-2">
                                <FileText className="w-4 h-4" /> Full Transcript
                            </span>
                            {showTranscript ? <ChevronDown className="w-4 h-4 text-neutral-400" /> : <ChevronRight className="w-4 h-4 text-neutral-400" />}
                        </button>
                        {showTranscript && (
                            <div className="p-6 max-h-[500px] overflow-y-auto bg-white">
                                <p className="text-xs text-neutral-600 whitespace-pre-wrap leading-relaxed font-mono">
                                    {lesson.transcript || "No transcript available."}
                                </p>
                            </div>
                        )}
                    </div>
                )}


                {/* Lesson Metadata (View/Edit) */}
                {lesson && (
                    <div className="pt-8 border-t border-neutral-200 animate-in slide-in-from-bottom-8 duration-700">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <FileText className="w-5 h-5 text-orange-600" />
                                Metadata & Notes
                            </h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="md:col-span-2 space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-neutral-500 uppercase mb-2 block">Memo</label>
                                    {isEditing ? (
                                        <MarkdownEditor
                                            value={editMemo}
                                            onChange={val => { setEditMemo(val); }}
                                            rows={8}
                                            placeholder="# Notes..."
                                        />
                                    ) : (
                                        <div className="prose prose-sm max-w-none text-neutral-600">
                                            {lesson.memo ? <MarkdownRenderer>{lesson.memo}</MarkdownRenderer> : <p className="italic text-neutral-400">No memo available.</p>}
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-neutral-500 uppercase flex items-center gap-2 mb-2">
                                        <Tag className="w-3 h-3" /> Tags
                                    </label>
                                    {isEditing ? (
                                        <TagInput
                                            value={editTags}
                                            onChange={tags => { setEditTags(tags); }}
                                            placeholder="Add tag..."
                                        />
                                    ) : (
                                        <div className="flex flex-wrap gap-2">
                                            {lesson.tags && lesson.tags.length > 0 ? lesson.tags.map(tag => (
                                                <span key={tag} className="px-2 py-1 bg-neutral-100 rounded text-xs text-neutral-700">
                                                    {tag}
                                                </span>
                                            )) : <span className="text-sm text-neutral-400">No tags</span>}
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-neutral-500 uppercase flex items-center gap-2 mb-2">
                                        <Calendar className="w-3 h-3" /> Created
                                    </label>
                                    <p className="text-sm font-mono text-neutral-900 bg-neutral-50 px-3 py-2 rounded-lg border border-neutral-200">
                                        {lesson.created_at || "Unknown"}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
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
                                    value={createTitle} onChange={e => setCreateTitle(e.target.value)}
                                    className="w-full border border-neutral-300 rounded-md px-3 py-2"
                                    placeholder="Awesome Lick"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Tags (comma separated)</label>
                                <input
                                    value={createTags} onChange={e => setCreateTags(e.target.value)}
                                    className="w-full border border-neutral-300 rounded-md px-3 py-2"
                                    placeholder="blues, slow, bend"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">Memo</label>
                                <textarea
                                    value={createMemo} onChange={e => setCreateMemo(e.target.value)}
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
