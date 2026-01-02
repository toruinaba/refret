import { useState, useEffect, useRef } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import { ArrowLeft, Plus, FileText, Tag, Calendar, PlayCircle, ChevronDown, ChevronRight, Music, Trash2, RefreshCw, Layers, Mic, Edit2, Save } from "lucide-react"
import { CreateLickDialog } from "../components/licks/CreateLickDialog"
import { MultiTrackPlayer, type MultiTrackPlayerRef } from "../components/player/MultiTrackPlayer"
import { api } from "../lib/api"
import type { LessonDetail as LessonDetailType } from "../types"
import { TagInput } from "../components/ui/TagInput"
import { MarkdownEditor } from "../components/ui/MarkdownEditor"
import { MarkdownRenderer } from '../components/ui/MarkdownRenderer'


export function LessonDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
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

    // Processing State
    const [processingTask, setProcessingTask] = useState<string | null>(null)
    const [processingProgress, setProcessingProgress] = useState(0)
    const [processingMessage, setProcessingMessage] = useState("")

    useEffect(() => {
        if (!processingTask || !id) return

        const interval = setInterval(async () => {
            try {
                const status = await api.getLessonStatus(id)
                setProcessingProgress(status.progress)
                setProcessingMessage(status.message)

                if (status.status === 'completed') {
                    // Reload data
                    const newData = await api.getLesson(id)
                    setLesson(newData as LessonDetailType)
                    setProcessingTask(null)
                    clearInterval(interval)
                } else if (status.status === 'failed') {
                    setProcessingTask(null)
                    alert("Processing Failed: " + status.message)
                    clearInterval(interval)
                }
            } catch (e) {
                console.error(e)
            }
        }, 1000)

        return () => clearInterval(interval)
    }, [processingTask, id])

    const handleReprocess = async (task: 'separate' | 'transcribe' | 'summarize') => {
        if (!id) return
        if (!window.confirm(`Are you sure you want to re-run ${task}? This will overwrite existing data for this step.`)) return

        try {
            setProcessingTask(task)
            setProcessingProgress(0)
            setProcessingMessage("Starting...")
            await api.reprocessLesson(id, task)
        } catch (e) {
            console.error(e)
            alert("Failed to start processing")
            setProcessingTask(null)
        }
    }

    useEffect(() => {
        if (!id) return;
        api.getLesson(id).then((data) => {
            const detail = data as LessonDetailType
            setLesson(detail)
            setEditTags(detail.tags || [])
            setEditMemo(detail.memo || "")

            // If status is not completed, start polling
            if (detail.status && detail.status !== 'completed') {
                setProcessingTask('initial') // Triggers the existing polling effect
            }
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

    const handleDelete = async () => {
        if (!id) return;
        if (window.confirm("Are you sure you want to delete this lesson? This action cannot be undone.")) {
            try {
                await api.deleteLesson(id);
                alert("Lesson deleted.");
                navigate("/");
            } catch (e) {
                console.error(e);
                alert("Failed to delete lesson.");
            }
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

    const handleSaveLick = async (title: string, tags: string[], memo: string) => {
        if (!id || !selection) return;
        try {
            await api.createLick({
                lesson_id: id,
                title: title,
                tags: tags,
                memo: memo,
                start: selection.start,
                end: selection.end
            })
            alert("Lick saved!")
            setIsCreating(false)
        } catch (e) {
            console.error(e)
            alert("Failed to save lick")
        }
    }

    if (!id) return <div>Invalid Lesson ID</div>

    return (
        <div className="space-y-6 pb-20">
            {processingTask && (
                <div className="fixed inset-0 bg-white/95 backdrop-blur-sm z-50 flex flex-col items-center justify-center p-8 space-y-6 animate-in fade-in duration-300">
                    <div className="relative">
                        <div className="w-16 h-16 border-4 border-neutral-100 border-t-orange-500 rounded-full animate-spin"></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-bold text-orange-600">{Math.round(processingProgress * 100)}%</span>
                        </div>
                    </div>
                    <div className="text-center space-y-2">
                        <h2 className="text-xl font-bold text-neutral-900">
                            {processingTask === 'initial' && "Processing Lesson..."}
                            {processingTask === 'separate' && "Separating Audio Tracks..."}
                            {processingTask === 'transcribe' && "Transcribing Audio..."}
                            {processingTask === 'summarize' && "Generating Summary..."}
                        </h2>
                        <p className="text-neutral-500 max-w-md">
                            Please wait while we process your request. Do not close this page.
                        </p>
                        <p className="text-sm font-mono bg-neutral-50 px-3 py-1 rounded inline-block text-neutral-600">
                            {processingMessage || "Initializing..."}
                        </p>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex items-center justify-between gap-4 border-b border-neutral-200 pb-4">
                <div className="flex items-center gap-4 min-w-0">
                    <Link to="/lessons" className="p-2 hover:bg-neutral-100 rounded-full transition-colors flex-shrink-0">
                        <ArrowLeft className="w-5 h-5 text-neutral-600" />
                    </Link>
                    <div className="flex flex-col min-w-0">
                        <span className="text-xs text-neutral-500 font-mono truncate">{id}</span>
                        <h1 className="text-xl sm:text-2xl font-bold truncate pr-4">{lesson?.title || id}</h1>
                    </div>
                </div>

                <div className="flex items-center gap-2">
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
                                onClick={handleSaveMetadata}
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
                            title="Edit Lesson"
                        >
                            <Edit2 className="w-4 h-4" />
                            <span className="hidden sm:inline">Edit</span>
                        </button>
                    )}
                    <button
                        onClick={handleDelete}
                        className="p-2 sm:px-3 sm:py-2 flex items-center gap-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50"
                        title="Delete Lesson"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-8 items-start">
                {/* Left Column: Player (Sticky) */}
                <div className="lg:col-span-1 space-y-4 lg:sticky lg:top-24 z-10 min-w-0">
                    <div className="bg-white p-1 rounded-xl border border-neutral-200 shadow-sm min-w-0">
                        <MultiTrackPlayer ref={playerRef} lessonId={id} onSelectionChange={setSelection} />
                    </div>

                    {/* Player Actions */}
                    <div className="flex flex-col gap-2">
                        {selection && !isCreating && (
                            <button
                                onClick={() => setIsCreating(true)}
                                className="w-full flex items-center justify-center gap-2 bg-orange-600 text-white px-4 py-3 rounded-lg hover:bg-orange-700 transition-colors font-medium shadow-sm animate-in fade-in slide-in-from-top-2"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Save Lick ({selection.start.toFixed(1)}s - {selection.end.toFixed(1)}s)</span>
                            </button>
                        )}

                        {selection && !isCreating && (
                            <button
                                onClick={() => setIsCreating(true)}
                                className="w-full flex items-center justify-center gap-2 bg-orange-600 text-white px-4 py-3 rounded-lg hover:bg-orange-700 transition-colors font-medium shadow-sm animate-in fade-in slide-in-from-top-2"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Save Lick ({selection.start.toFixed(1)}s - {selection.end.toFixed(1)}s)</span>
                            </button>
                        )}

                        {/* Redo Audio Separation Button (Player Context) */}
                        {isEditing && (
                            <button
                                onClick={() => handleReprocess('separate')}
                                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200"
                            >
                                <Layers className="w-3.5 h-3.5" />
                                Redo Audio Separation
                            </button>
                        )}
                    </div>
                </div>

                {/* Right Column: Content */}
                <div className="lg:col-span-2 space-y-8">
                    {/* AI Analysis Section */}
                    {lesson && (lesson.summary || (lesson.key_points && lesson.key_points.length > 0)) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-bottom-4 duration-500">
                            {/* Summary Card */}
                            <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm space-y-4 relative">
                                <div className="flex items-center justify-between border-b border-neutral-100 pb-2">
                                    <h3 className="flex items-center gap-2 font-semibold text-neutral-900">
                                        <FileText className="w-4 h-4 text-orange-600" /> Summary
                                    </h3>
                                    {isEditing && (
                                        <button
                                            onClick={() => handleReprocess('summarize')}
                                            className="text-xs flex items-center gap-1 text-green-600 bg-green-50 px-2 py-1 rounded hover:bg-green-100 transition-colors"
                                            title="Redo Summary"
                                        >
                                            <RefreshCw className="w-3 h-3" /> Redo
                                        </button>
                                    )}
                                </div>
                                <p className="text-sm text-neutral-600 leading-relaxed whitespace-pre-wrap">
                                    {lesson.summary || "No summary available."}
                                </p>

                                {/* Chords */}
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
                                <div className="flex items-center gap-3">
                                    {isEditing && (
                                        <div
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleReprocess('transcribe');
                                            }}
                                            className="text-xs flex items-center gap-1 text-red-600 bg-red-50 px-2 py-1 rounded hover:bg-red-100 transition-colors cursor-pointer"
                                            title="Redo Transcription"
                                        >
                                            <Mic className="w-3 h-3" /> Redo
                                        </div>
                                    )}
                                    {showTranscript ? <ChevronDown className="w-4 h-4 text-neutral-400" /> : <ChevronRight className="w-4 h-4 text-neutral-400" />}
                                </div>
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
                        <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm animate-in slide-in-from-bottom-8 duration-700">
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
            </div>

            {/* Creation Modal */}
            <CreateLickDialog
                isOpen={isCreating}
                onClose={() => setIsCreating(false)}
                onSave={handleSaveLick}
                selection={selection}
            />
        </div>
    )
}
