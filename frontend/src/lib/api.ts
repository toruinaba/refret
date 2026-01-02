import axios from 'axios';
import type { Lesson, LessonDetail, Lick, PaginatedResponse, PracticeLog, JournalStats } from '../types';

const API_BASE_URL = '/api';

const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = {
    // Lessons
    getLessons: async (params?: { page?: number, limit?: number, tags?: string[], date_from?: string, date_to?: string }): Promise<PaginatedResponse<Lesson>> => {
        const query: any = { ...params };
        if (params?.tags) {
            query.tags = params.tags.join(",");
        }
        const res = await client.get('/lessons', { params: query });
        return res.data;
    },

    getLesson: async (id: string): Promise<LessonDetail> => {
        const res = await client.get(`/lessons/${id}`);
        return res.data;
    },

    uploadLesson: async (file: File, metadata?: { title?: string, created_at?: string, tags?: string[], memo?: string }): Promise<{ id: string }> => {
        const formData = new FormData();
        formData.append("file", file);
        if (metadata?.title) formData.append("title", metadata.title);
        if (metadata?.created_at) formData.append("created_at", metadata.created_at);
        if (metadata?.tags) formData.append("tags", JSON.stringify(metadata.tags));
        if (metadata?.memo) formData.append("memo", metadata.memo);

        const res = await client.post('/lessons/upload', formData, {
            headers: { "Content-Type": "multipart/form-data" }
        });
        return res.data;
    },

    getLessonStatus: async (id: string): Promise<{ status: string, progress: number, message: string }> => {
        const res = await client.get(`/lessons/${id}/status`);
        return res.data;
    },

    updateLesson: async (id: string, updates: Partial<Lesson>): Promise<Lesson> => {
        const res = await client.put(`/lessons/${id}`, updates);
        return res.data;
    },

    deleteLesson: async (id: string): Promise<void> => {
        await client.delete(`/lessons/${id}`);
    },

    reprocessLesson: async (id: string, taskType: 'separate' | 'transcribe' | 'summarize'): Promise<void> => {
        await client.post(`/lessons/${id}/process`, null, {
            params: { task_type: taskType }
        });
    },

    // Licks
    getLicks: async (params?: { page?: number, limit?: number, tags?: string[], lesson_id?: string, date_from?: string, date_to?: string }): Promise<PaginatedResponse<Lick>> => {
        const query: any = { ...params };
        if (params?.tags) {
            query.tags = params.tags.join(",");
        }
        const res = await client.get('/licks', { params: query });
        return res.data;
    },

    getLick: async (id: string): Promise<Lick> => {
        const res = await client.get(`/licks/${id}`);
        return res.data;
    },

    // Transcription
    transcribeAudio: async (lessonId: string, start: number, end: number) => {
        const res = await fetch(`${API_BASE_URL}/transcribe/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lesson_id: lessonId, start_time: start, end_time: end }),
        });
        if (!res.ok) throw new Error("Transcription failed");
        return res.json(); // returns { abc: string }
    },

    createLick: async (data: Omit<Lick, 'id' | 'created_at'>): Promise<Lick> => {
        const res = await client.post('/licks', data);
        return res.data;
    },

    updateLick: async (id: string, updates: Partial<Lick>): Promise<Lick> => {
        const res = await client.put(`/licks/${id}`, updates);
        return res.data;
    },

    deleteLick: async (id: string): Promise<void> => {
        await client.delete(`/licks/${id}`);
    },

    // Settings
    getSettings: async (): Promise<{
        llm_provider: string,
        llm_model: string,
        system_prompt: string,
        openai_api_key_masked: string | null,
        openai_api_key_is_set: boolean,
        // Audio
        demucs_model?: string,
        demucs_shifts?: number,
        demucs_overlap?: number,
        // Whisper
        whisper_model?: string,
        whisper_beam_size?: number,
        // Basic Pitch
        bp_onset_threshold?: number,
        bp_min_frequency?: number,
        bp_quantize_grid?: number,
    }> => {
        try {
            const res = await client.get("/settings");
            return res.data;
        } catch (e) {
            console.warn("Failed to fetch settings, using defaults");
            return {
                llm_provider: "openai",
                llm_model: "gpt-3.5-turbo",
                system_prompt: "",
                openai_api_key_masked: null,
                openai_api_key_is_set: false
            };
        }
    },

    saveSettings: async (settings: any): Promise<any> => {
        const res = await client.post("/settings", settings);
        return res.data;
    },

    // Tags
    getTags: async (): Promise<string[]> => {
        const res = await client.get('/tags');
        return res.data;
    },

    // Audio helpers
    getAudioUrl: (lessonId: string, track: 'vocals' | 'guitar') => {
        return `${API_BASE_URL}/lessons/${lessonId}/audio/${track}`;
    },

    // Journal
    getLogs: async (start?: string, end?: string): Promise<PracticeLog[]> => {
        const params: any = {};
        if (start) params.start = start;
        if (end) params.end = end;
        const res = await client.get('/journal', { params });
        return res.data;
    },

    getLog: async (id: number): Promise<PracticeLog> => {
        const res = await client.get(`/journal/${id}`);
        return res.data;
    },

    createLog: async (data: Partial<PracticeLog>): Promise<PracticeLog> => {
        const res = await client.post('/journal', data);
        return res.data;
    },

    updateLog: async (id: number, data: Partial<PracticeLog>): Promise<PracticeLog> => {
        const res = await client.put(`/journal/${id}`, data);
        return res.data;
    },

    deleteLog: async (id: number): Promise<void> => {
        await client.delete(`/journal/${id}`);
    },

    getJournalStats: async (): Promise<JournalStats> => {
        const res = await client.get('/journal/stats');
        return res.data;
    }
};
