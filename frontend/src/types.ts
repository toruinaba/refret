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
    tags: string[];
    start: number;
    end: number;
    memo: string;
    created_at: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
}
