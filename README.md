# Refret Web (Guitar Lesson Review App)

Refret is a modern web application for guitarists to review and study their lessons. It separates audio tracks (vocals vs guitar), provides transcription and summarization using AI, and features a powerful multi-track audio player for practicing.

## Architecture

The project has been migrated from a monolithic Streamlit app to a modern web stack:

*   **Backend**: Python (FastAPI)
    *   Handles audio processing (Demucs), transcription (Faster-Whisper), and summarization (LLM).
    *   Manages data persistence (Filesystem-based).
    *   Serves REST API for frontend.
*   **Frontend**: React (Vite + TypeScript)
    *   **UI Framework**: Tailwind CSS v4
    *   **Audio Player**: Wavesurfer.js (Multi-track sync, Regions, Speed control)
    *   **State Management**: React Hooks + Axios

## Key Features

1.  **Audio Separation**: Automatically separates uploaded lessons into Vocals and Guitar tracks using Hybrid Transformer Demucs.
2.  **Lesson Library**: Organize lessons with tags and memos. Search and filter your practice history.
3.  **Lick Library**: Save specific phrases (loops) from lessons as "Licks". Build your own library of riffs to practice.
4.  **Multi-Track Player**:
    *   **Sync Playback**: Listen to vocals and guitar tracks simultaneously or individually.
    *   **Mute/Solo**: Isolate the guitar track to hear nuances.
    *   **Looping**: Drag to create loop regions for repetitive practice.
    *   **Speed Control**: Slow down tricky parts without changing pitch.
5.  **AI Integration**: Summarizes lesson content and extracts key points using OpenAI or Ollama.

## Installation & Setup

### Prerequisites
*   Node.js (v18+)
*   Python (3.13+)
*   FFmpeg (Installed and in system PATH)

### 1. Backend Setup

```bash
# Navigate to project root
pip install -r backend/requirements.txt

# Start the Backend Server
./start_backend.sh
# OR
uvicorn backend.app.main:app --reload --port 8000
```
Backend runs at `http://localhost:8000`. API Docs at `/docs`.

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Development Server
npm run dev
```
Frontend runs at `http://localhost:5173`.

## Usage

1.  **Upload (Legacy)**: Currently, new audio uploads are processed via the legacy Streamlit app scripts or manual placement in `data/` (Upload UI migration is planned).
2.  **Library**: Open the Web App to view processed lessons.
3.  **Practice**: Click a lesson to open the Player.
    *   **Save Lick**: Select a region on the waveform and click "Save Lick" to add it to your Lick Library.
4.  **Licks**: Review saved phrases in the "Lick Library" tab.

## Data Storage

Data is stored in the `data/` directory:
*   `data/lessons/{id}/`: Audio files and metadata.json for lessons.
*   `data/licks.json`: Database of saved licks.
