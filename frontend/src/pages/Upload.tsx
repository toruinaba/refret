import React from 'react';
import { UniversalUploader } from '../components/UniversalUploader';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export const Upload: React.FC = () => {
    const navigate = useNavigate();

    return (
        <div className="max-w-3xl mx-auto">
            <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 text-neutral-600 hover:text-orange-600 transition-colors mb-6 font-medium"
            >
                <ArrowLeft className="w-5 h-5" />
                Back to Dashboard
            </button>

            <UniversalUploader onSuccess={() => {
                // Optional: navigate to specific page or just let user stay
                // navigate('/'); 
            }} />
        </div>
    );
};
