export interface Lesson {
    id: string;
    title: string;
    duration: number;
    created_at: string;
    date?: string;
    vocals_path?: string;
    guitar_path?: string;
    tags?: string[];
    memo?: string;
    status?: 'queued' | 'processing' | 'completed' | 'error' | string;
    is_processed?: boolean;
}

export interface LessonDetail extends Lesson {
    transcript_path?: string;
    summary_path?: string;
    keypoints_path?: string;

    // Loaded content
    transcript?: string;
    summary?: string;
    key_points?: Array<string | { point: string, timestamp?: string }>;
    chords?: string[];
}

export interface Lick {
    id: string;
    lesson_id?: string;
    lesson_title?: string;
    practice_log_id?: number;
    title: string;
    start: number;
    end: number;
    tags: string[];
    memo: string;
    created_at: string;
    abc_score?: string; // ABC notation
    source_audio_url?: string;
}

export type LickCreate = Omit<Lick, 'id' | 'created_at'> & { lesson_dir?: string }

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

// Practice Journal
export interface PracticeLog {
    id: number;
    date: string; // YYYY-MM-DD
    duration_minutes: number;
    notes?: string;
    tags?: string[];
    sentiment?: string;
    audio_path?: string;
    analysis?: { bpm: number, key: string };
    created_at: string;
}

export interface JournalStats {
    heatmap: Array<{ date: string, count: number, duration: number }>;
    total_minutes: number;
    week_minutes: number;
}
