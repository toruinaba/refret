export interface Lesson {
    id: string;
    title: string;
    duration: number;
    created_at: string;
    tags?: string[];
    memo?: string;
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
    title: string;
    start: number;
    end: number;
    tags: string[];
    memo: string;
    created_at: string;
    abc_score?: string; // ABC notation
}

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
    created_at: string;
}

export interface JournalStats {
    heatmap: Array<{ date: string, count: number, duration: number }>;
    total_minutes: number;
    week_minutes: number;
}
