import axios from 'axios';
import type { Lesson, LessonDetail } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = {
    // Lessons
    getLessons: async (): Promise<Lesson[]> => {
        const res = await client.get('/lessons');
        return res.data;
    },

    getLesson: async (id: string): Promise<LessonDetail> => {
        const res = await client.get(`/lessons/${id}`);
        return res.data;
    },

    updateLesson: async (id: string, updates: Partial<Lesson>): Promise<Lesson> => {
        const res = await client.put(`/lessons/${id}`, updates);
        return res.data;
    },

    // Audio helpers
    getAudioUrl: (lessonId: string, track: 'vocals' | 'guitar') => {
        return `${API_BASE_URL}/lessons/${lessonId}/audio/${track}`;
    }
};
