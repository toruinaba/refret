import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface CreateLickDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (title: string, tags: string[], memo: string) => void;
    selection?: { start: number, end: number } | null;
}

export const CreateLickDialog: React.FC<CreateLickDialogProps> = ({ isOpen, onClose, onSave, selection }) => {
    const [title, setTitle] = useState("");
    const [tags, setTags] = useState("");
    const [memo, setMemo] = useState("");

    // Reset when opening
    useEffect(() => {
        if (isOpen) {
            setTitle("");
            setTags("");
            setMemo("");
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleSave = () => {
        if (!title.trim()) return;
        const tagList = tags.split(",").map(t => t.trim()).filter(Boolean);
        onSave(title, tagList, memo);
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 animate-in zoom-in-95" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold">Save New Lick</h2>
                    <button onClick={onClose}><X className="w-5 h-5 text-neutral-400 hover:text-neutral-600" /></button>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">Title</label>
                        <input
                            value={title} onChange={e => setTitle(e.target.value)}
                            className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-orange-500 outline-none"
                            placeholder="Awesome Lick"
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">Tags (comma separated)</label>
                        <input
                            value={tags} onChange={e => setTags(e.target.value)}
                            className="w-full border border-neutral-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-orange-500 outline-none"
                            placeholder="blues, slow, bend"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">Memo</label>
                        <textarea
                            value={memo} onChange={e => setMemo(e.target.value)}
                            className="w-full border border-neutral-300 rounded-md px-3 py-2 h-24 focus:ring-2 focus:ring-orange-500 outline-none"
                            placeholder="Notes about fingering, difficulty etc."
                        />
                    </div>

                    {selection && (
                        <div className="text-xs text-neutral-500 bg-neutral-100 p-2 rounded">
                            Range: {selection.start.toFixed(2)}s - {selection.end.toFixed(2)}s
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-3 pt-4">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-neutral-600 hover:bg-neutral-100 rounded-lg font-medium transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={!title.trim()}
                        className="px-4 py-2 bg-orange-600 text-white rounded-lg font-medium hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Save Lick
                    </button>
                </div>
            </div>
        </div>
    );
};
