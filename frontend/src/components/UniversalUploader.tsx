import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import {
    CloudUpload,
    FileAudio,
    CheckCircle2,
    AlertCircle
} from 'lucide-react';
import { api } from '../lib/api';

interface UniversalUploaderProps {
    onSuccess?: () => void;
    defaultTab?: number;
}

export const UniversalUploader: React.FC<UniversalUploaderProps> = ({ onSuccess, defaultTab = 0 }) => {
    const [tabValue, setTabValue] = useState(defaultTab); // 0 = Lesson, 1 = Practice
    const [file, setFile] = useState<File | null>(null);

    // Common Fields
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [tags, setTags] = useState('');
    const [notes, setNotes] = useState(''); // Mapped to 'memo' (Lesson) or 'notes' (Practice)

    // Lesson Specific
    const [title, setTitle] = useState('');

    // Practice Specific (Added)
    const [duration, setDuration] = useState(30);
    const [sentiment, setSentiment] = useState('');

    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            setFile(acceptedFiles[0]);
            setError(null);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'audio/*': ['.mp3', '.wav', '.m4a', '.aac', '.mp4']
        },
        maxFiles: 1
    });

    const handleUpload = async () => {
        // Validation
        if (tabValue === 0 && !file) {
            setError("Please select a file for the lesson.");
            return;
        }
        // Practice Log allows text only, so file is optional.

        setUploading(true);
        setProgress(0);
        setError(null);
        setMessage(null);

        try {
            if (tabValue === 1 && !file) {
                // Text-only Practice Log
                const data = {
                    date: date,
                    duration_minutes: duration,
                    notes: notes,
                    tags: tags.split(',').map(t => t.trim()).filter(Boolean),
                    sentiment: sentiment || undefined
                };
                await api.createLog(data);
                setMessage("Practice log saved!");
            } else {
                // File Upload (Lesson or Practice with Audio)
                const formData = new FormData();
                formData.append('file', file!); // We checked file exists for tab 0, and if we are here for tab 1 it exists

                const endpoint = tabValue === 0
                    ? `/api/lessons/upload`
                    : `/api/journal/upload`;

                if (tabValue === 0) {
                    // Lesson
                    if (title.trim()) formData.append('title', title);
                    formData.append('created_at', date);
                    if (tags.trim()) formData.append('tags', tags);
                    if (notes.trim()) formData.append('memo', notes);
                } else {
                    // Practice with Audio
                    formData.append('date', date);
                    if (tags.trim()) formData.append('tags', tags);
                    if (notes.trim()) formData.append('notes', notes);
                    formData.append('duration_minutes', duration.toString());
                    if (sentiment) formData.append('sentiment', sentiment);
                }

                await axios.post(endpoint, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    onUploadProgress: (progressEvent) => {
                        const total = progressEvent.total || (file ? file.size : 0);
                        const percent = Math.round((progressEvent.loaded * 100) / total);
                        setProgress(percent);
                    }
                });
                setMessage("Upload successful! Processing in background.");
            }

            // Reset Form
            setFile(null);
            setTitle('');
            setNotes('');
            setTags('');
            setSentiment('');
            // setDuration(30); // Keep duration for convenience?

            if (onSuccess) onSuccess();

        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Upload failed. Please try again.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden max-w-2xl mx-auto mt-8">
            <div className="p-6">
                <h2 className="text-2xl font-bold text-center text-neutral-900 mb-6">
                    {tabValue === 0 ? "Upload Lesson" : "Log Practice"}
                </h2>

                {/* Tabs */}
                <div className="flex border-b border-neutral-200 mb-6">
                    <button
                        className={`flex-1 pb-3 text-sm font-medium transition-colors border-b-2 ${tabValue === 0
                            ? 'border-orange-600 text-orange-600'
                            : 'border-transparent text-neutral-500 hover:text-neutral-700'
                            }`}
                        onClick={() => { setTabValue(0); setError(null); setMessage(null); }}
                    >
                        New Lesson
                    </button>
                    <button
                        className={`flex-1 pb-3 text-sm font-medium transition-colors border-b-2 ${tabValue === 1
                            ? 'border-orange-600 text-orange-600'
                            : 'border-transparent text-neutral-500 hover:text-neutral-700'
                            }`}
                        onClick={() => { setTabValue(1); setError(null); setMessage(null); }}
                    >
                        Practice Log
                    </button>
                </div>

                {/* Dropzone (Optional for Practice) */}
                <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors mb-6 relative group ${isDragActive
                        ? 'border-orange-500 bg-orange-50'
                        : 'border-neutral-300 hover:border-orange-400 hover:bg-neutral-50'
                        }`}
                >
                    {tabValue === 1 && !file && (
                        <div className="absolute top-2 right-2 text-xs text-neutral-400 bg-white px-2 py-1 rounded border border-neutral-200">
                            Optional
                        </div>
                    )}

                    <input {...getInputProps()} />
                    <CloudUpload className="w-12 h-12 text-neutral-400 mx-auto mb-3" />
                    {file ? (
                        <div className="relative">
                            <p className="text-orange-600 font-semibold flex items-center justify-center gap-2">
                                <FileAudio className="w-5 h-5" />
                                {file.name}
                            </p>
                            <p className="text-xs text-neutral-500 mt-1">
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                            <button
                                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                                className="absolute -top-1 -right-4 p-1 rounded-full hover:bg-red-50 text-red-400"
                            >
                                <span className="sr-only">Remove</span>
                                ×
                            </button>
                        </div>
                    ) : (
                        <div>
                            <p className="text-neutral-600 font-medium">
                                {tabValue === 0 ? "Drag & drop audio file here" : "Add recording (Optional)"}
                            </p>
                            <p className="text-xs text-neutral-400 mt-2">
                                Supports MP3, WAV, M4A
                            </p>
                        </div>
                    )}
                </div>

                {/* Form Fields */}
                <div className="space-y-4">

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">
                                Date
                            </label>
                            <input
                                type="date"
                                className="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                disabled={uploading}
                            />
                        </div>

                        {/* Lesson Title OR Practice Duration */}
                        {tabValue === 0 ? (
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">
                                    Title (Optional)
                                </label>
                                <input
                                    type="text"
                                    className="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    disabled={uploading}
                                    placeholder="e.g. Jazz Blues"
                                />
                            </div>
                        ) : (
                            <div>
                                <label className="block text-sm font-medium text-neutral-700 mb-1">
                                    Duration (Minutes)
                                </label>
                                <input
                                    type="number"
                                    className="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    value={duration}
                                    onChange={(e) => setDuration(Number(e.target.value))}
                                    disabled={uploading}
                                />
                            </div>
                        )}
                    </div>

                    {tabValue === 1 && (
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 mb-1">
                                Sentiment
                            </label>
                            <select
                                value={sentiment}
                                onChange={(e) => setSentiment(e.target.value)}
                                className="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                            >
                                <option value="">Select how it went...</option>
                                <option value="Good">🔥 Good</option>
                                <option value="Neutral">😐 Neutral</option>
                                <option value="Frustrated">😫 Frustrated</option>
                                <option value="Tired">😴 Tired</option>
                            </select>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Tags (comma separated)
                        </label>
                        <input
                            type="text"
                            className="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            disabled={uploading}
                            placeholder="e.g. blues, fast, lick"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                            {tabValue === 0 ? "Memo" : "Notes"}
                        </label>
                        <textarea
                            className="w-full px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                            rows={3}
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            disabled={uploading}
                            placeholder={tabValue === 0 ? "Lesson details..." : "Practice session notes..."}
                        />
                    </div>

                    {/* Status Messages */}
                    {error && (
                        <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                            <p className="text-sm">{error}</p>
                        </div>
                    )}

                    {message && (
                        <div className="p-4 bg-green-50 text-green-700 rounded-lg flex items-start gap-3">
                            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                            <p className="text-sm">{message}</p>
                        </div>
                    )}

                    {/* Progress Bar */}
                    {uploading && (
                        <div className="space-y-2">
                            <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-orange-600 transition-all duration-300"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                            <p className="text-xs text-center text-neutral-500">
                                Uploading... {progress}%
                            </p>
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-all ${!file || uploading
                            ? 'bg-neutral-300 cursor-not-allowed'
                            : 'bg-orange-600 hover:bg-orange-700 shadow-md hover:shadow-lg'
                            }`}
                        onClick={handleUpload}
                        disabled={!file || uploading}
                    >
                        {uploading ? 'Processing...' : 'Upload Audio'}
                    </button>
                </div>
            </div>
        </div>
    );
};
