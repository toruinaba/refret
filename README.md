# Refret Web (Guitar Lesson Review App)

Refret is a comprehensive practice companion web application for guitarists. It unifies lesson review, practice logging, and phrase (Lick) management into a single, AI-powered platform.

## Key Features

### 🎸 Smart Lesson Review
*   **AI Separation**: Automatically separates audio into **Vocals** and **Guitar** tracks (Demucs).
*   **Rich Player**: Multi-track player with synchronized playback, speed control, A-B looping, and track muting/soloing.
*   **AI Transcription**: Full speech-to-text transcription using Faster-Whisper.
*   **Smart Summary**: AI-generated summaries, key points, and chord progression extraction (LLM-powered).

### 📝 Practice Journal
*   **Activity Heatmap**: Visualize your practice consistency on a GitHub-style dashboard.
*   **Rich Practice Logs**: Record sessions with audio, write Markdown notes (with ABC notation support), and tag entries.
*   **Unified History**: Tracking for both structured "Lessons" and free-form "Practice" sessions in one view.

### 🎼 Lick Library
*   **Phrase Managment**: Select any region from a Lesson or Practice Log and save it as a "Lick".
*   **ABC Notation Support**: Write or generate scores for your licks using standard ABC notation.
*   **Auto Transcription**: (Experimental) Convert audio to score automatically.
*   **Tagging**: Organize licks by technique, artist, or style for focused practice.

### ⚙️ Modern Architecture
*   **Responsive UI**: Built with React, Vite, and Tailwind CSS v4.
*   **Fast Backend**: Python FastAPI with async processing for heavy AI tasks.
*   **Flexible Storage**: SQLite database for metadata + filesystem for large media assets.

---

## Architecture

*   **Frontend**: React 19, Vite, TypeScript, Tailwind CSS v4
*   **Backend**: Python 3.10+, FastAPI, SQLite
*   **AI Stack**: Demucs (Separation), Faster-Whisper (Transcription), LangChain (Summarization)
*   **Infrastructure**: Docker Compose

## Quick Start (Docker)

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd refret
    ```

2.  **Start with Docker Compose**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Access the App**:
    *   Frontend: [http://localhost:5173](http://localhost:5173)
    *   Backend API: `http://localhost:8000`

4.  **Initial Setup**:
    *   Go to **Settings** (Cog icon) in the sidebar.
    *   Set your **OpenAI API Key** (required for Summary features).
    *   Configure Demucs/Whisper model settings if needed.

## Manual Development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run server
./start_backend.sh
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Data Management

*   **Database**: stored in `data/practice.db` (SQLite).
*   **Files**: Audio, transcripts, and summaries are stored in `data/lessons/{id}`.
*   **Persistence**: The `data/` directory is mounted to the host, ensuring data survives container restarts.
