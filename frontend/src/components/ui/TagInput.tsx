import { useState, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { X, Tag } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface TagInputProps {
    value: string[];
    onChange: (tags: string[]) => void;
    suggestions?: string[];
    placeholder?: string;
    className?: string;
}

const EMPTY_LIST: string[] = [];

export function TagInput({ value, onChange, suggestions = EMPTY_LIST, placeholder = "Add tag...", className }: TagInputProps) {
    const [inputValue, setInputValue] = useState("");
    const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);

    useEffect(() => {
        if (inputValue.trim()) {
            setFilteredSuggestions(
                suggestions.filter(s =>
                    s.toLowerCase().includes(inputValue.toLowerCase()) &&
                    !value.includes(s)
                ).slice(0, 5)
            );
        } else {
            setFilteredSuggestions([]);
        }
    }, [inputValue, suggestions, value]);

    const addTag = (tag: string) => {
        const trimmed = tag.trim();
        if (trimmed && !value.includes(trimmed)) {
            onChange([...value, trimmed]);
        }
        setInputValue("");
    };

    const removeTag = (tagToRemove: string) => {
        onChange(value.filter(tag => tag !== tagToRemove));
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addTag(inputValue);
        } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
            removeTag(value[value.length - 1]);
        }
    };

    return (
        <div className={twMerge("w-full", className)}>
            <div className="flex flex-wrap gap-2 items-center p-2 bg-white border border-neutral-300 rounded-lg focus-within:ring-2 focus-within:ring-orange-500 focus-within:border-orange-500">
                {value.map(tag => (
                    <span key={tag} className="flex items-center gap-1 bg-orange-100 text-orange-800 text-sm px-2 py-0.5 rounded-full">
                        <Tag className="w-3 h-3" />
                        {tag}
                        <button onClick={() => removeTag(tag)} className="hover:text-orange-950">
                            <X className="w-3 h-3" />
                        </button>
                    </span>
                ))}

                <div className="relative flex-1 min-w-[120px]">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={value.length === 0 ? placeholder : ""}
                        className="w-full outline-none bg-transparent text-sm py-1"
                        list="tag-suggestions" // Fallback
                    />

                    {/* Custom Suggestions Dropdown */}
                    {filteredSuggestions.length > 0 && (
                        <div className="absolute top-full left-0 w-full mt-1 bg-white border border-neutral-200 rounded-md shadow-lg z-10 max-h-40 overflow-y-auto">
                            {filteredSuggestions.map(s => (
                                <button
                                    key={s}
                                    type="button"
                                    onClick={() => addTag(s)}
                                    className="block w-full text-left px-3 py-2 text-sm hover:bg-neutral-50"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
