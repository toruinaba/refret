import axios from 'axios';
import type { Lesson, LessonDetail, Lick } from '../types';

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

    // Licks
    getLicks: async (): Promise<Lick[]> => {
        const res = await client.get('/licks');
        return res.data;
    },

    getLick: async (id: string): Promise<Lick> => {
        const res = await client.get(`/licks/${id}`);
        return res.data;
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

    // Audio helpers
    getAudioUrl: (lessonId: string, track: 'vocals' | 'guitar') => {
        return `${API_BASE_URL}/lessons/${lessonId}/audio/${track}`;
    }
};
