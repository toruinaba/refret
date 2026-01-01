export interface Lesson {
    id: string;
    title: string;
    created_at: string;
    tags: string[];
    memo: string;
}

export interface LessonDetail extends Lesson {
    transcript?: string;
    summary?: string;
    key_points?: Array<string | { point: string, timestamp: string }>;
    chords?: string[];
}

export interface Lick {
    id: string;
    lesson_dir: string;
    title: string;
    start: number;
    end: number;
    tags?: string[];
    created_at?: string;
    memo?: string;
    abc_score?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
}
