import { useEffect, useState } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import { ArrowLeft, Clock, Tag, FileText, Music, Wand2, Trash2 } from "lucide-react"
import type { Lick } from "../types"
import { api } from "../lib/api"
import { MultiTrackPlayer } from "../components/player/MultiTrackPlayer"
import { TagInput } from "../components/ui/TagInput"
import { MarkdownEditor } from "../components/ui/MarkdownEditor"
import { MarkdownRenderer } from "../components/ui/MarkdownRenderer"
import { AbcRenderer } from "../components/ui/AbcRenderer"

export function LickDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const [lick, setLick] = useState<Lick | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const [isEditing, setIsEditing] = useState(false)
    const [editTitle, setEditTitle] = useState("")
    const [editTags, setEditTags] = useState<string[]>([])
    const [editMemo, setEditMemo] = useState("")
    const [editAbc, setEditAbc] = useState("")
    const [saving, setSaving] = useState(false)
    const [transcribing, setTranscribing] = useState(false)

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

    const startEditing = () => {
        if (!lick) return
        setEditTitle(lick.title)
        setEditTags(lick.tags || [])
        setEditMemo(lick.memo || "")
        setEditAbc(lick.abc_score || "")
        setIsEditing(true)
    }

    const handleDelete = async () => {
        if (!id) return;
        if (window.confirm("Are you sure you want to delete this lick?")) {
            try {
                await api.deleteLick(id);
                if (lick) {
                    navigate(`/lesson/${lick.lesson_dir}`);
                } else {
                    navigate("/licks");
                }
            } catch (e) {
                console.error(e);
                alert("Failed to delete lick");
            }
        }
    }

    const handleUpdate = async () => {
        if (!lick || !id) return
        try {
            setSaving(true)
            const updated = await api.updateLick(id, {
                title: editTitle,
                tags: editTags,
                memo: editMemo,
                abc_score: editAbc
            })
            setLick(updated)
            setIsEditing(false)
        } catch (e) {
            console.error(e)
            setError("Failed to update lick")
        } finally {
            setSaving(false)
        }
    }

    const handleTranscribe = async () => {
        if (!lick) return
        try {
            setTranscribing(true)
            const res = await api.transcribeAudio(lick.lesson_dir, lick.start, lick.end)
            if (res.abc) {
                setEditAbc(res.abc)
            }
        } catch (e) {
            console.error(e)
            alert("Transcription failed. Please ensure backend requirements are met.")
        } finally {
            setTranscribing(false)
        }
    }

    if (loading) return <div className="text-center p-8">Loading lick...</div>
    if (error || !lick) return <div className="text-center p-8 text-red-500">{error || "Lick not found"}</div>

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-4 flex-1">
                    <Link to="/licks" className="p-2 hover:bg-neutral-100 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5 text-neutral-600" />
                    </Link>
                    <div className="flex-1">
                        <div className="flex items-center gap-2 text-neutral-500 text-sm mb-1">
                            <span className="bg-orange-100 text-orange-800 px-2 py-0.5 rounded text-xs font-semibold">Lick</span>
                            <span>From Lesson: <Link to={`/lesson/${lick.lesson_dir}`} className="hover:underline text-orange-600">{lick.lesson_dir}</Link></span>
                        </div>
                        {isEditing ? (
                            <input
                                value={editTitle}
                                onChange={e => setEditTitle(e.target.value)}
                                className="text-2xl font-bold text-neutral-900 border-b border-neutral-300 focus:border-orange-500 outline-none w-full bg-transparent"
                            />
                        ) : (
                            <h1 className="text-2xl font-bold text-neutral-900">{lick.title}</h1>
                        )}
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                    {isEditing ? (
                        <>
                            <button onClick={() => setIsEditing(false)} className="px-3 py-1.5 text-sm text-neutral-600 hover:bg-neutral-100 rounded-md">
                                Cancel
                            </button>
                            <button
                                onClick={handleUpdate}
                                disabled={saving}
                                className="px-3 py-1.5 text-sm bg-orange-600 text-white hover:bg-orange-700 rounded-md disabled:opacity-50"
                            >
                                {saving ? "Saving..." : "Save Changes"}
                            </button>
                            <button
                                onClick={handleDelete}
                                className="px-3 py-1.5 text-sm bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 rounded-md flex items-center gap-1"
                                title="Delete Lick"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </>
                    ) : (
                        <button onClick={startEditing} className="px-3 py-1.5 text-sm border border-neutral-200 hover:bg-neutral-50 rounded-md text-neutral-700">
                            Edit Details
                        </button>
                    )}
                </div>
            </div>

            {/* Player (Unchanged) */}
            <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200">
                <MultiTrackPlayer
                    lessonId={lick.lesson_dir}
                    initialRegion={{ start: lick.start, end: lick.end }}
                    initialVocalsMuted={true}
                />
            </div>

            {/* Details Card */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-4">
                    {/* Score Card */}
                    <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="flex items-center gap-2 font-semibold text-neutral-900">
                                <Music className="w-4 h-4" /> Score / Tab
                            </h3>
                            {isEditing && (
                                <button
                                    onClick={handleTranscribe}
                                    disabled={transcribing}
                                    className="text-xs flex items-center gap-1 bg-purple-100 text-purple-700 px-2 py-1.5 rounded hover:bg-purple-200 disabled:opacity-50"
                                >
                                    <Wand2 className="w-3 h-3" /> {transcribing ? "Transcribing..." : "Auto Transcribe"}
                                </button>
                            )}
                        </div>

                        {isEditing ? (
                            <div className="space-y-2">
                                <textarea
                                    value={editAbc}
                                    onChange={e => setEditAbc(e.target.value)}
                                    className="w-full h-40 font-mono text-sm border border-neutral-300 rounded-lg p-3 focus:border-orange-500 outline-none"
                                    placeholder="X:1&#10;K:C&#10;CDEF..."
                                />
                                <p className="text-xs text-neutral-400 text-right">ABC Notation</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                {lick.abc_score ? (
                                    <AbcRenderer notation={lick.abc_score} />
                                ) : (
                                    <p className="italic text-neutral-400">No score available.</p>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-sm">
                        <h3 className="flex items-center gap-2 font-semibold text-neutral-900 mb-4">
                            <FileText className="w-4 h-4" /> Memo
                        </h3>
                        {isEditing ? (
                            <MarkdownEditor
                                value={editMemo}
                                onChange={setEditMemo}
                                rows={8}
                                placeholder="# Lick Notes..."
                            />
                        ) : (
                            <div className="prose prose-sm max-w-none text-neutral-600">
                                {lick.memo ? <MarkdownRenderer>{lick.memo}</MarkdownRenderer> : <p className="italic text-neutral-400">No memo available.</p>}
                            </div>
                        )}
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
                            {isEditing ? (
                                <TagInput
                                    value={editTags}
                                    onChange={setEditTags}
                                    placeholder="Add tag..."
                                />
                            ) : (
                                <div className="flex flex-wrap gap-2">
                                    {lick.tags && lick.tags.length > 0 ? lick.tags.map(tag => (
                                        <span key={tag} className="px-2 py-1 bg-neutral-100 rounded text-xs text-neutral-700">
                                            {tag}
                                        </span>
                                    )) : <span className="text-sm text-neutral-400">No tags</span>}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
