# Refret Web (Guitar Lesson Review App)

Refret is a modern web application designed for guitarists to review, transcribe, and study their lessons effectively. It leverages AI to separate audio tracks, transcribe vocals, summarize content, and extract musical notes.

## Key Features

*   **Smart Audio Separation**: Separates lesson audio into **Vocals** and **Guitar** tracks using [Demucs](https://github.com/facebookresearch/demucs).
*   **AI Transcription & Summarization**:
    *   Transcribes speech using [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper).
    *   Summarizes lesson content and extracts key points using LLM (OpenAI/Ollama).
*   **Multi-Track Player**:
    *   Synchronized playback of Original, Vocals, and Guitar tracks.
    *   Waveform visualization with region looping and speed control.
*   **Lick Library**: Organically build a library of "Licks" by selecting regions in your lessons and saving them with tags.
*   **Configurable AI Settings**: Adjust model parameters (Demucs models, Whisper beam size, LLM prompts) directly from the UI.
*   **Reprocessing**: Re-run Separation, Transcription, or Summarization steps individually with new settings.

## Architecture

*   **Backend**: Python (FastAPI)
    *   Core AI Services: Demucs, Faster-Whisper, Basic Pitch.
    *   Data Persistence: Local Filesystem (`data/`).
*   **Frontend**: React (Vite + TypeScript)
    *   UI: Tailwind CSS v4, Lucide React.
    *   State: React Hooks, Axios.
*   **Infrastructure**: Docker Compose (Nginx, Python API).

## Getting Started

### Prerequisites

*   **Docker** and **Docker Compose** installed.
*   (Optional) OpenAI API Key for summarization features.

### Quick Start

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd refret
    ```

2.  **Start the Application**:
    ```bash
    docker-compose up -d --build
    ```
    *   This will build the frontend and backend containers.
    *   Backend runs on port `8000`.
    *   Frontend runs on port `5173` (localhost:5173) or `80` depending on mapping.
    *   *Note: Current `docker-compose.yml` maps host 5173 -> container 80.*

3.  **Access the App**:
    Open [http://localhost:5173](http://localhost:5173) in your browser.

4.  **Configure Settings**:
    Go to the **Settings** page ("Cog" icon) to:
    *   Set your OpenAI API Key (if using OpenAI).
    *   Configure Demucs model (e.g., `htdemucs`, `mdx_extra`).
    *   Adjust Whisper beam size or LLM prompts.

## Usage Guide

### uploading Lessons
1.  Click the **Upload** button on the main library view.
2.  Select an audio file (MP3/WAV/M4A).
3.  The system will automatically process the file (separate -> transcribe -> summarize).

### Studying a Lesson
1.  Click on a lesson card.
2.  **Player**: Use the separate track controls to mute vocals or boost guitar.
3.  **Looping**: Drag on the waveform to create a loop.
4.  **Save Lick**: While a region is selected, click **Save Lick** (left sidebar) to save that phrase.
5.  **Edit/Reprocess**:
    *   Click **Edit Metadata** to change tags or memo.
    *   In Edit mode, use the **AI Tools** section to re-run specific AI tasks (e.g., if you changed the separation model).

### Lick Library
*   View all your saved licks across different lessons.
*   Filter by tags to practice specific techniques.

## Development

If you want to run the stack locally without Docker (e.g., for faster dev):

**Backend**:
```bash
cd backend
pip install -r requirements.txt
./start_backend.sh
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## Data Storage

All lesson data (audio, JSON metadata) is stored in the `data/` directory at the project root. This directory is volume-mounted in Docker, so your data persists across restarts.
