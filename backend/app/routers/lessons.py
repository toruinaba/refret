from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import List, Dict, Any, Literal
import shutil
import json
import traceback
from datetime import datetime
import math

from app.services.store import StoreService
from app.core.config import get_settings
from app.services.audio import AudioProcessor

router = APIRouter()

def get_store():
    return StoreService()

# --- Background Processing Task ---
def process_lesson_background(lesson_id: str, file_path: Path, store: StoreService, initial_metadata: Dict[str, Any] = {}):
    status_file = store.data_dir / lesson_id / "status.json"
    
    def update_status(status: str, progress: float, message: str):
        # Update File (Legacy/Frontend polling)
        with open(status_file, "w") as f:
            json.dump({
                "status": status,
                "progress": progress,
                "message": message,
                "updated_at": datetime.now().isoformat()
            }, f)
        # Update DB
        store.save_lesson_metadata(lesson_id, {"status": status})

    try:
        from app.services.audio import AudioProcessor
        processor = AudioProcessor()

        # Step 1: Separation
        update_status("processing", 0.05, "Separating Audio (Demucs)... This takes time.")
        
        # Ensure we have a WAV file for processing (handles m4a etc)
        proc_wav_path = processor.prepare_wav(file_path)
        
        try:
            vocals_path, guitar_path = processor.separate_audio(proc_wav_path, store.data_dir / lesson_id)
            
            # Generate Peaks
            update_status("processing", 0.15, "Generating Waveforms...")
            processor.generate_peaks(vocals_path, store.data_dir / lesson_id / "vocals.json")
            processor.generate_peaks(guitar_path, store.data_dir / lesson_id / "guitar.json")
        finally:
            # Cleanup temp proc wav
            if proc_wav_path.exists() and proc_wav_path != file_path:
                proc_wav_path.unlink()
        
        # Step 2: Transcription
        update_status("processing", 0.5, "Transcribing Vocals (Whisper)...")
        transcript_text, segments = processor.transcribe(vocals_path)
        
        # Step 3: Summarization
        update_status("processing", 0.8, "Summarizing (LLM)...")
        summary_data = processor.summarize(segments)
        
        # Step 4: Finalize
        update_status("processing", 0.95, "Finalizing...")
        
        # Save results to separate files (Legacy format)
        processor.save_results(store.data_dir / lesson_id, segments, transcript_text, summary_data)
        
        # Build metadata: Start with initial provided by user
        metadata = initial_metadata.copy()
        
        # Fill defaults if missing
        if "title" not in metadata or not metadata["title"]:
            metadata["title"] = f"Lesson {lesson_id}"
        if "created_at" not in metadata or not metadata["created_at"]:
            metadata["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "tags" not in metadata:
            metadata["tags"] = []
        if "memo" not in metadata:
             metadata["memo"] = ""
        
        store.save_lesson_metadata(lesson_id, metadata)
        update_status("completed", 1.0, "Ready")

    except Exception as e:
        print(f"Processing failed: {e}")
        traceback.print_exc()
        update_status("failed", 0.0, str(e))

# --- Endpoints ---

@router.post("/upload")
async def upload_lesson(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None),
    created_at: str = Form(None),
    tags: str = Form(None), # Receive as JSON string
    memo: str = Form(None),
    store: StoreService = Depends(get_store)
):
    """Upload a new lesson audio file for processing."""
    # Generate ID (Timestamp based)
    lesson_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    lesson_dir = store.data_dir / lesson_id
    lesson_dir.mkdir(exist_ok=True)
    
    # helper to parse tags
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except:
            # Fallback for simple comma list
            parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]

    initial_metadata = {
        "title": title,
        "created_at": created_at,
        "tags": parsed_tags,
        "memo": memo
    }
    # remove None keys
    initial_metadata = {k: v for k, v in initial_metadata.items() if v is not None}
    
    # Save Uploaded File (Raw)
    ext = Path(file.filename).suffix
    if not ext: ext = ".m4a" # Default for voice memo
    raw_path = lesson_dir / f"original_raw{ext}"
    
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Normalize to MP3 immediately
    final_path = lesson_dir / "original.mp3"
    try:
        processor = AudioProcessor()
        processor.convert_to_mp3(raw_path, final_path)
    except Exception as e:
        # Fallback or cleanup
        print(f"Conversion failed: {e}")
        # If conversion fails, maybe we just fail the request or try to use raw?
        # Requirement says "Convert to original.mp3 immediately". 
        # So we should probably error out if this fails.
        if raw_path.exists(): raw_path.unlink()
        # Clean folder?
        shutil.rmtree(lesson_dir) 
        raise HTTPException(status_code=500, detail=f"Audio normalization failed: {str(e)}")
        
    # Cleanup raw
    if raw_path.exists():
        raw_path.unlink()
        
    file_path = final_path
        
    # Init Status
    # Init Status
    status_file = lesson_dir / "status.json"
    with open(status_file, "w") as f:
        json.dump({"status": "queued", "progress": 0.0, "message": "In Queue"}, f)

    # Create Initial DB Record
    store.save_lesson_metadata(lesson_id, {**initial_metadata, "status": "queued"})

    # Trigger Background Task
    background_tasks.add_task(process_lesson_background, lesson_id, file_path, store, initial_metadata)
    
    return {"id": lesson_id, "message": "Upload successful, processing started."}

@router.get("/{lesson_id}/status")
async def get_lesson_status(lesson_id: str, store: StoreService = Depends(get_store)):
    """Check processing status of a lesson."""
    # Check DB first
    meta = store.get_lesson_metadata(lesson_id)
    if meta and "status" in meta:
         # Combine with file-based progress if available (DB doesn't store progress float)
         status_file = store.data_dir / lesson_id / "status.json"
         progress = 0.0
         message = meta["status"]
         if status_file.exists():
             try:
                 with open(status_file, "r") as f:
                     sf = json.load(f)
                     progress = sf.get("progress", 0.0)
                     message = sf.get("message", message)
             except:
                 pass
         return {"status": meta["status"], "progress": progress, "message": message}

    # Fallback to file only
    status_file = store.data_dir / lesson_id / "status.json"
    
    if not status_file.exists():
        if (store.data_dir / lesson_id).exists():
             return {"status": "unknown", "progress": 0.0, "message": "No status info"}
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    with open(status_file, "r") as f:
        try:
            return json.load(f)
        except:
             return {"status": "unknown", "progress": 0.0, "message": "Read error"}

@router.get("/", response_model=Dict[str, Any])
async def list_lessons(
    page: int = 1,
    limit: int = 50,
    tags: str = None,
    date_from: str = None,
    date_to: str = None,
    store: StoreService = Depends(get_store)
):
    """List lessons with filtering and pagination."""
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
    items, total = store.list_lessons(
        page=page, 
        limit=limit, 
        tags=tag_list, 
        date_from=date_from, 
        date_to=date_to
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1
    }

@router.get("/{lesson_id}", response_model=Dict[str, Any])
async def get_lesson(lesson_id: str, store: StoreService = Depends(get_store)):
    """Get metadata for a specific lesson."""
    meta = store.get_lesson_metadata(lesson_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Return basic info plus IDs to help frontend construct audio URLs
    return {
        "id": lesson_id,
        "title": lesson_id,
        **meta
    }

@router.put("/{lesson_id}")
async def update_lesson(lesson_id: str, updates: Dict[str, Any], store: StoreService = Depends(get_store)):
    """Update lesson metadata (memo, tags)."""
    current = store.get_lesson_metadata(lesson_id)
    if not current and not (store.data_dir / lesson_id).exists():
         raise HTTPException(status_code=404, detail="Lesson not found")
         
    # Merge updates
    current.update(updates)
    store.save_lesson_metadata(lesson_id, current)
    return current

@router.get("/{lesson_id}/audio/{track_type}")
async def get_audio_stream(lesson_id: str, track_type: str, store: StoreService = Depends(get_store)):
    """
    Stream audio file.
    track_type: 'vocals' or 'guitar'
    """
    if track_type not in ["vocals", "guitar"]:
        raise HTTPException(status_code=400, detail="Invalid track type")
        
    file_name = f"{track_type}.mp3"
    file_path = store.data_dir / lesson_id / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"{lesson_id}_{track_type}.mp3"
    )

@router.get("/{lesson_id}/audio/{track_type}/peaks")
async def get_audio_peaks(lesson_id: str, track_type: str, store: StoreService = Depends(get_store)):
    """
    Get pre-computed peaks data for audio track.
    """
    if track_type not in ["vocals", "guitar"]:
        raise HTTPException(status_code=400, detail="Invalid track type")
        
    peaks_path = store.data_dir / lesson_id / f"{track_type}.json"
    
    # Lazy generation if missing
    if not peaks_path.exists():
        audio_path = store.data_dir / lesson_id / f"{track_type}.mp3"
        if audio_path.exists():
            from app.services.audio import AudioProcessor
            processor = AudioProcessor()
            processor.generate_peaks(audio_path, peaks_path)
        else:
             # If audio doesn't exist, we can't generate
             raise HTTPException(status_code=404, detail="Audio file not found")
            
    if not peaks_path.exists():
         raise HTTPException(status_code=404, detail="Peaks not found")

    with open(peaks_path, "r") as f:
        try:
            data = json.load(f)
            return data
        except:
             raise HTTPException(status_code=500, detail="Invalid peaks file")

@router.get("/{lesson_id}/transcript")
async def get_transcript(lesson_id: str, store: StoreService = Depends(get_store)):
    """Get transcript text if available."""
    # Assuming transcript is saved in metadata or a separate file?
    # Original app saved to metadata['transcript'] in some versions or transcript.txt
    # Let's check session_state in app.py logic. 
    # For now, let's look for transcript.txt or metadata.
    
    # Check metadata first
    meta = store.get_lesson_metadata(lesson_id)
    if "transcript" in meta: # If we start saving it there
        return {"transcript": meta["transcript"]}
        
    # Fallback/Migration: Check if transcript.txt exists (if we change storage strategy)
    # The current streamlit app stores it in `st.session_state` but seemingly doesn't persist it plainly 
    # except potentially in `metadata.json` if we modified processor.
    
    # Re-reading processor.py logic: processor returns it, but app.py decides where to save.
    # In `app.py`, save logic is not explicitly dumping transcript to file other than maybe `summary`.
    # Let's assume for now we just return what's in metadata or empty.
    
    return {"transcript": meta.get("transcript", "")}

@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: str, store: StoreService = Depends(get_store)):
    """Delete a lesson."""
    store.delete_lesson(lesson_id)
    return {"status": "deleted", "id": lesson_id}

def reprocess_lesson_step(lesson_id: str, task_type: str, store: StoreService):
    status_file = store.data_dir / lesson_id / "status.json"
    lesson_dir = store.data_dir / lesson_id
    
    def update_status(status: str, progress: float, message: str):
        with open(status_file, "w") as f:
            json.dump({
                "status": status,
                "progress": progress,
                "message": message,
                "updated_at": datetime.now().isoformat()
            }, f)
        # Update DB
        store.save_lesson_metadata(lesson_id, {"status": status})

    try:
        from app.services.audio import AudioProcessor
        processor = AudioProcessor()
        
        original_file = list(lesson_dir.glob("original.*"))
        if not original_file:
            raise FileNotFoundError("Original audio file not found")
        original_path = original_file[0]

        if task_type == "separate":
            update_status("processing", 0.1, "Re-separating Audio...")
            proc_wav = processor.prepare_wav(original_path)
            try:
                processor.separate_audio(proc_wav, lesson_dir)
            finally:
                if proc_wav.exists() and proc_wav != original_path:
                    proc_wav.unlink()
            update_status("completed", 1.0, "Separation Complete")

        elif task_type == "transcribe":
            update_status("processing", 0.1, "Re-transcribing...")
            vocals_path = lesson_dir / "vocals.mp3"
            if not vocals_path.exists():
                raise FileNotFoundError("Vocals track not found. Run separation first.")
            
            transcript_text, segments = processor.transcribe(vocals_path)
            
            # Save Transcript result specifically
            with open(lesson_dir / "transcript.json", "w") as f:
                json.dump(segments, f, indent=2)
            with open(lesson_dir / "transcript.txt", "w") as f:
                f.write(transcript_text)
                
            # Update metadata
            meta = store.get_lesson_metadata(lesson_id)
            if meta:
                meta["transcript"] = transcript_text
                store.save_lesson_metadata(lesson_id, meta)
            
            update_status("completed", 1.0, "Transcription Complete")

        elif task_type == "summarize":
            update_status("processing", 0.1, "Re-summarizing...")
            transcript_json = lesson_dir / "transcript.json"
            if not transcript_json.exists():
                raise FileNotFoundError("Transcript not found. Run transcription first.")
                
            with open(transcript_json, "r") as f:
                segments = json.load(f)
                
            summary_data = processor.summarize(segments)
            
            # Save Summary
            with open(lesson_dir / "summary.json", "w") as f:
                json.dump(summary_data, f, indent=2)
                
            # Update Metadata
            meta = store.get_lesson_metadata(lesson_id)
            if meta:
                meta.update(summary_data)
                store.save_lesson_metadata(lesson_id, meta)
            
            update_status("completed", 1.0, "Summarization Complete")
            
        else:
            raise ValueError(f"Unknown task: {task_type}")

    except Exception as e:
        print(f"Reprocessing failed: {e}")
        traceback.print_exc()
        update_status("failed", 0.0, f"Error: {str(e)}")


@router.post("/{lesson_id}/process")
async def process_lesson(
    lesson_id: str, 
    task_type: Literal["separate", "transcribe", "summarize"], 
    background_tasks: BackgroundTasks,
    store: StoreService = Depends(get_store)
):
    """Trigger a specific processing step for a lesson."""
    if not (store.data_dir / lesson_id).exists():
        raise HTTPException(status_code=404, detail="Lesson not found")

    background_tasks.add_task(reprocess_lesson_step, lesson_id, task_type, store)
    return {"message": f"Started task: {task_type}"}
