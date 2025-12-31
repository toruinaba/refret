import { useState } from 'react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface MarkdownEditorProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    rows?: number;
}

export function MarkdownEditor({ value, onChange, placeholder, className, rows = 10 }: MarkdownEditorProps) {
    const [mode, setMode] = useState<'write' | 'preview'>('write');

    return (
        <div className={twMerge("border border-neutral-300 rounded-lg bg-white overflow-hidden", className)}>
            <div className="flex bg-neutral-50 border-b border-neutral-200">
                <button
                    type="button"
                    onClick={() => setMode('write')}
                    className={clsx(
                        "px-4 py-2 text-sm font-medium transition-colors",
                        mode === 'write' ? "bg-white text-orange-600 border-r border-neutral-200" : "text-neutral-600 hover:text-neutral-900"
                    )}
                >
                    Write
                </button>
                <button
                    type="button"
                    onClick={() => setMode('preview')}
                    className={clsx(
                        "px-4 py-2 text-sm font-medium transition-colors",
                        mode === 'preview' ? "bg-white text-orange-600 border-l border-r border-neutral-200" : "text-neutral-600 hover:text-neutral-900"
                    )}
                >
                    Preview
                </button>
                <div className="flex-1" />
                <span className="px-4 py-2 text-xs text-neutral-400 self-center">Markdown Supported</span>
            </div>

            <div className="relative">
                {mode === 'write' ? (
                    <textarea
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={placeholder}
                        rows={rows}
                        className="w-full p-4 outline-none font-mono text-sm resize-y"
                    />
                ) : (
                    <div
                        className="prose prose-sm prose-orange max-w-none p-4 min-h-[150px] overflow-y-auto"
                        style={{ height: rows ? `${rows * 1.5}em` : 'auto' }}
                    >
                        {value ? <MarkdownRenderer>{value}</MarkdownRenderer> : <p className="text-neutral-400 italic">Nothing to preview</p>}
                    </div>
                )}
            </div>
        </div>
    );
}
