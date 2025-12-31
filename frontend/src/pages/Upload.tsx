import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Upload as UploadIcon, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import { api } from "../lib/api"
import { TagInput } from "../components/ui/TagInput"
import { MarkdownEditor } from "../components/ui/MarkdownEditor"

export function Upload() {
    const navigate = useNavigate()
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const [processingId, setProcessingId] = useState<string | null>(null)
    const [status, setStatus] = useState<{ status: string, progress: number, message: string } | null>(null)
    const [error, setError] = useState<string | null>(null)

    // Metadata State
    const [metadata, setMetadata] = useState<{
        title: string,
        created_at: string,
        tags: string[],
        memo: string
    }>({
        title: "",
        created_at: new Date().toISOString().split('T')[0],
        tags: [],
        memo: ""
    })

    // Polling Effect
    useEffect(() => {
        let interval: number;
        if (processingId && status?.status !== 'completed' && status?.status !== 'failed') {
            interval = setInterval(async () => {
                try {
                    const s = await api.getLessonStatus(processingId)
                    setStatus(s)
                    if (s.status === 'completed') {
                        // Redirect after short delay
                        setTimeout(() => navigate(`/lesson/${processingId}`), 1000)
                    }
                    if (s.status === 'failed') {
                        setError(s.message || "Processing failed")
                    }
                } catch (e) {
                    console.error(e)
                }
            }, 1000)
        }
        return () => clearInterval(interval)
    }, [processingId, status, navigate])

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0])
            // Set default title if empty
            if (!metadata.title) {
                const name = e.target.files[0].name.replace(/\.[^/.]+$/, "")
                setMetadata(prev => ({ ...prev, title: name }))
            }
            setError(null)
        }
    }

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true)
        setError(null)
        try {
            const res = await api.uploadLesson(file, metadata)
            setProcessingId(res.id)
            setStatus({ status: 'queued', progress: 0, message: 'Queued...' })
        } catch (e) {
            console.error(e)
            setError("Upload failed. Please check backend logs.")
            setUploading(false)
        }
    }

    return (
        <div className="max-w-5xl mx-auto space-y-8 pb-20">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold text-neutral-900">Upload New Lesson</h1>
                <p className="text-neutral-500">Upload an audio file and separate tracks.</p>
            </div>

            {!processingId ? (
                <div className="grid md:grid-cols-2 gap-8 items-start">
                    {/* Metadata Column */}
                    <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm space-y-5 order-2 md:order-1">
                        <h2 className="text-lg font-semibold flex items-center gap-2 border-b border-neutral-100 pb-3">
                            <span className="bg-orange-100 text-orange-600 w-6 h-6 rounded-full flex items-center justify-center text-xs">1</span>
                            Lesson Details
                        </h2>

                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Title</label>
                            <input
                                type="text"
                                value={metadata.title}
                                onChange={e => setMetadata({ ...metadata, title: e.target.value })}
                                placeholder="e.g. Blues Jam in A"
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Date</label>
                            <input
                                type="date"
                                value={metadata.created_at}
                                onChange={e => setMetadata({ ...metadata, created_at: e.target.value })}
                                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Tags</label>
                            <TagInput
                                value={metadata.tags}
                                onChange={tags => setMetadata({ ...metadata, tags })}
                                placeholder="Type and press Enter..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">Memo</label>
                            <MarkdownEditor
                                value={metadata.memo}
                                onChange={memo => setMetadata({ ...metadata, memo })}
                                rows={8}
                                placeholder="# Notes..."
                            />
                        </div>
                    </div>

                    {/* File Upload Column */}
                    <div className="bg-white p-8 rounded-xl border border-dashed border-neutral-300 hover:border-orange-500 transition-colors text-center space-y-6 flex flex-col justify-center h-full min-h-[400px] order-1 md:order-2">
                        <div className="w-16 h-16 bg-orange-50 text-orange-600 rounded-full flex items-center justify-center mx-auto">
                            <UploadIcon className="w-8 h-8" />
                        </div>
                        <div>
                            <input
                                type="file"
                                onChange={handleFileChange}
                                accept="audio/*"
                                className="hidden"
                                id="file-upload"
                            />
                            <label
                                htmlFor="file-upload"
                                className="cursor-pointer inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 md:text-lg shadow-sm"
                            >
                                Select Audio File
                            </label>
                            <p className="mt-2 text-sm text-neutral-400">
                                {file ? file.name : "No file selected"}
                            </p>
                        </div>

                        {file && (
                            <div className="pt-4 border-t border-dashed border-neutral-200 w-full">
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    className="w-full py-3 bg-neutral-900 text-white rounded-lg font-semibold hover:bg-neutral-800 disabled:opacity-50 shadow-sm"
                                >
                                    {uploading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Start Processing"}
                                </button>
                                <p className="text-xs text-neutral-400 mt-2">
                                    Files will be separated into vocals and guitar tracks.
                                </p>
                            </div>
                        )}

                        {error && <div className="text-red-500 text-sm bg-red-50 p-2 rounded">{error}</div>}
                    </div>
                </div>
            ) : (
                <div className="bg-white p-8 rounded-xl border border-neutral-200 space-y-6 shadow-sm">
                    <div className="text-center">
                        {status?.status === 'completed' ? (
                            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                        ) : status?.status === 'failed' ? (
                            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-2" />
                        ) : (
                            <Loader2 className="w-12 h-12 text-orange-500 animate-spin mx-auto mb-2" />
                        )}
                        <h2 className="text-xl font-bold text-neutral-900">
                            {status?.status === 'completed' ? "Processing Complete!" :
                                status?.status === 'failed' ? "Processing Failed" : "Processing Lesson..."}
                        </h2>
                        <p className="text-neutral-500 text-sm">{status?.message}</p>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-neutral-100 rounded-full h-4 overflow-hidden">
                        <div
                            className={`h-full transition-all duration-500 ${status?.status === 'failed' ? 'bg-red-500' : 'bg-orange-600'}`}
                            style={{ width: `${(status?.progress || 0) * 100}%` }}
                        ></div>
                    </div>
                </div>
            )}
        </div>
    )
}
