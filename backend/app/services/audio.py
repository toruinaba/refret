import os
import json
import subprocess
from pathlib import Path
import shutil
from faster_whisper import WhisperModel
import openai
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.schemas.lesson import LessonSummary

class AudioProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        
        # Configure LLM
        self._configure_llm()

    def _get_current_key(self):
        from app.services.store import StoreService
        store = StoreService()
        overrides = store.get_settings_override()
        return overrides.get("openai_api_key") or self.settings.OPENAI_API_KEY

    def _configure_llm(self):
        """Configure LLM client based on current settings."""
        if self.settings.LLM_PROVIDER == "openai":
            key = self._get_current_key()
            if key:
                openai.api_key = key

    def prepare_wav(self, input_path: Path) -> Path:
        """Convert input audio to WAV format for processing (ffmpeg)."""
        output_path = input_path.parent / "proc_temp.wav"
        print(f"Converting to WAV for processing: {input_path} -> {output_path}")
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-ac", "2", 
                "-ar", "44100", 
                "-f", "wav",
                str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg wav conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
            raise e

    def separate_audio(self, file_path: Path, lesson_dir: Path):
        """
        Separate audio into vocals and guitar using Demucs CLI.
        Allocates memory management to the external process to prevent OOM.
        returns: (vocals_path, guitar_path)
        """
        print(f"Separating audio (CLI): {file_path}")
        
        try:
            # Load overrides
            from app.services.store import StoreService
            store = StoreService()
            overrides = store.get_settings_override()

            # Load Model Name
            model_name = overrides.get("demucs_model") or self.settings.DEMUCS_MODEL
            
            # Construct Command
            # demucs -n <model> -o <out_dir> <input>
            # --mp3 means output directly as mp3 (Demucs supports this) - this saves a conversion step!
            # But wait, original code converted to WAV then separated then converted back.
            # Demucs CLI can accept any format ffmpeg supports.
            # We can pass the original file directly if we wanted, but prepare_wav handles normalization.
            # Let's use the input file_path (which is WAV from prepare_wav).
            
            # Note: Demucs default output structure is: <out_dir>/<model_name>/<song_name>/...
            # We need to handle this.
            
            # Additional flags
            shifts = overrides.get("demucs_shifts") or self.settings.DEMUCS_SHIFTS
            overlap = overrides.get("demucs_overlap") or self.settings.DEMUCS_OVERLAP
            
            cmd = [
                "demucs",
                "-n", model_name,
                "-o", str(lesson_dir),
                "--mp3", # Output as MP3 directly
                "--mp3-bitrate", "192",
                "--shifts", str(shifts),
                "--overlap", str(overlap),
                str(file_path)
            ]
            
            # Thread safety flags
            # -j 1 is critical for low memory environments to prevent parallel processing overhead
            cmd.extend(["-j", "1"]) 
            
            # Reduce segment size to lower peak memory usage (Default is ~7.8s)
            cmd.extend(["--segment", "4"])

            print(f"Executing Demucs CLI: {' '.join(cmd)}")
            
            # Prepare Environment
            env = os.environ.copy()
            # Strict single thread execution
            env["OMP_NUM_THREADS"] = "1" 
            env["MKL_NUM_THREADS"] = "1"
            
            # Run Subprocess
            # IMPORTANT: Do NOT use capture_output=True. 
            # Large output can fill the pipe buffer and cause the process to hang (deadlock).
            # We redirect to DEVNULL or inherit stdout/stderr.
            subprocess.run(cmd, check=True, env=env, stdout=None, stderr=None)
            # print("Demucs finished.") -> No stdout to print if we don't capture.
            
            # Locate Output Files
            # Demucs outputs to: lesson_dir / model_name / file_path.stem / {vocals, drums, bass, other}.mp3
            # file_path is usually "proc_temp.wav" from prepare_wav.
            song_name = file_path.stem # e.g. "proc_temp"
            
            demucs_out_dir = lesson_dir / model_name / song_name
            
            if not demucs_out_dir.exists():
                raise FileNotFoundError(f"Demucs output directory not found: {demucs_out_dir}")
                
            # Move/Rename specific stems to our expected flat structure
            # We want: vocals.mp3, guitar.mp3
            # Demucs (htdemucs) usually outputs: vocals.mp3, drums.mp3, bass.mp3, other.mp3
            # OR if using 6s models, guitar.mp3 might exist.
            # Standard htdemucs is 4 sources: vocals, drums, bass, other.
            # "other" usually contains guitar/piano in 4-stem models.
            # htdemucs_6s has guitar. 
            
            # Let's check what stems are available
            available_stems = list(demucs_out_dir.glob("*.mp3"))
            print(f"Generated stems: {[p.name for p in available_stems]}")
            
            target_vocals = lesson_dir / "vocals.mp3"
            target_guitar = lesson_dir / "guitar.mp3"
            
            # Vocals
            src_vocals = demucs_out_dir / "vocals.mp3"
            if src_vocals.exists():
                shutil.move(str(src_vocals), str(target_vocals))
            else:
                # Fallback or create silent?
                print("Warning: No vocals stem found.")
            
            # Guitar
            # If guitar stem exists (6s model), use it.
            # If not, use 'other' as guitar (common substitution for 4-stem).
            # Or mix 'other' + 'piano' etc.
            
            src_guitar = demucs_out_dir / "guitar.mp3"
            src_other = demucs_out_dir / "other.mp3"
            
            if src_guitar.exists():
                shutil.move(str(src_guitar), str(target_guitar))
            elif src_other.exists():
                print("Using 'other' stem as guitar track.")
                shutil.move(str(src_other), str(target_guitar))
            else:
                print("Warning: No guitar/other stem found.")
                
            # Cleanup Demucs folders
            try:
                shutil.rmtree(lesson_dir / model_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp demucs folder: {e}")

            return target_vocals, target_guitar

        except subprocess.CalledProcessError as e:
            print(f"Demucs CLI failed: {e.stderr}")
            raise RuntimeError(f"Demucs CLI failed: {e.stderr}")
        except Exception as e:
            print(f"Error in separation: {e}")
            raise e

    def convert_to_mp3(self, input_path: Path, output_path: Path):
        """Convert any audio file to MP3 (192k)."""
        print(f"Converting {input_path} to MP3...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-codec:a", "libmp3lame",
            "-b:a", "192k",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def transcribe(self, audio_path: Path):
        """Transcribe audio using Faster-Whisper."""
        print(f"Transcribing: {audio_path}")
        
        # Load overrides
        from app.services.store import StoreService
        store = StoreService()
        overrides = store.get_settings_override()
        
        model_size = overrides.get("whisper_model") or self.settings.WHISPER_MODEL
        beam_size = overrides.get("whisper_beam_size") or self.settings.WHISPER_BEAM_SIZE
        
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        segments, info = model.transcribe(
            str(audio_path), 
            beam_size=beam_size, 
            language="ja",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False
        )
        
        transcript_text = ""
        segments_data = []

        for segment in segments:
            transcript_text += segment.text + "\n"
            segments_data.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            
        return transcript_text, segments_data

    def summarize(self, segments_data):
        """Summarize using LangChain Structured Output."""
        print(f"Summarizing using {self.settings.LLM_PROVIDER}...")
        
        # Load overrides
        from app.services.store import StoreService
        store = StoreService()
        overrides = store.get_settings_override()
        
        system_instruction = overrides.get("system_prompt") or self.settings.SYSTEM_PROMPT
        model_name = overrides.get("llm_model") or self.settings.LLM_MODEL
        
        # Format transcript
        transcript_with_timestamps = ""
        for seg in segments_data:
            start_time = seg["start"]
            m = int(start_time // 60)
            s = int(start_time % 60)
            timestamp = f"{m:02d}:{s:02d}"
            transcript_with_timestamps += f"[{timestamp}] {seg['text']}\n"
        
        try:
            if self.settings.LLM_PROVIDER == "openai":
                key = self._get_current_key()
                if not key:
                    return {"error": "No OpenAI API Key found", "summary": "N/A"}
                
                llm = ChatOpenAI(
                    model=model_name, 
                    api_key=key,
                    temperature=0
                )
                
                structured_llm = llm.with_structured_output(LessonSummary)
                
                response = structured_llm.invoke([
                    ("system", system_instruction),
                    ("human", f"Here is the transcript:\n\n{transcript_with_timestamps[:15000]}")
                ])
                
                return response.model_dump()

            else:
                # Basic Fallback logic for Ollama (omitted detailed implementation for brevity in migration)
                # Just return raw text or mock
                return {"summary": "Ollama not fully ported in basic migration yet.", "key_points": [], "chords": []}
                
        except Exception as e:
            print(f"Summarization error: {e}")
            return {"error": str(e)}

    def save_results(self, lesson_dir: Path, segments: list, transcript_text: str, summary_json: dict):
        """Save processing results to separate files (Legacy format)."""
        # Save transcript JSON
        with open(lesson_dir / "transcript.json", "w") as f:
            json.dump(segments, f, indent=2)
        
        # Save transcript Text
        with open(lesson_dir / "transcript.txt", "w") as f:
            f.write(transcript_text)
            
        # Save summary
        with open(lesson_dir / "summary.json", "w") as f:
            json.dump(summary_json, f, indent=2)

    def analyze_audio(self, audio_path: Path) -> dict:
        """
        Analyze audio for musical properties (BPM, Key) using Librosa.
        Returns dict with analysis data.
        """
        print(f"Analyzing audio: {audio_path}")
        try:
            import librosa
            import numpy as np
            
            # Load audio (mono for analysis)
            y, sr = librosa.load(str(audio_path), sr=None)
            
            # 1. BPM Detection
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            
            # 2. Key Detection
            # Extract Chroma features
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            
            # Simple heuristic for key: 
            # Sum chroma over time -> dominant pitch class
            # This is very basic. For major/minor, we'd need template matching.
            # Let's try to detect Major/Minor using correlation with templates if possible, 
            # or just return the dominant pitch class for now.
            
            # Key templates
            # Major: [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1] (C Major relative intervals)
            # Minor: [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0] (C Minor relative intervals)
            
            chroma_sum = np.sum(chroma, axis=1)
            
            # Normalize
            chroma_sum /= np.max(chroma_sum)
            
            # Templates for 12 pitches (C, C#, D...)
            # We shift the templates to match each pitch class
            # ... Actually let's use a simpler library approach if available? 
            # music21 is in requirements, but librosa is loaded.
            # Let's write a simple template matcher.
            
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            # Standardize profiles
            major_profile /= np.max(major_profile)
            minor_profile /= np.max(minor_profile)
            
            pitches = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            best_correlation = -1
            detected_key = "Unknown"
            
            for i in range(12):
                # Roll profiles to check each tonic
                major_rolled = np.roll(major_profile, i)
                minor_rolled = np.roll(minor_profile, i)
                
                # Correlate
                corr_major = np.corrcoef(chroma_sum, major_rolled)[0, 1]
                corr_minor = np.corrcoef(chroma_sum, minor_rolled)[0, 1]
                
                if corr_major > best_correlation:
                    best_correlation = corr_major
                    detected_key = f"{pitches[i]} Major"
                    
                if corr_minor > best_correlation:
                    best_correlation = corr_minor
                    detected_key = f"{pitches[i]} Minor"

            return {
                "bpm": float(tempo),
                "key": detected_key,
                "duration": librosa.get_duration(y=y, sr=sr)
            }
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            return {"error": str(e), "bpm": 0, "key": "Unknown"}

    def generate_peaks(self, audio_path: Path, output_path: Path, points_per_second: int = 100):
        """
        Generate waveform peaks using ffmpeg stream to avoid memory overhead.
        Saves as JSON file.
        """
        print(f"Generating peaks for: {audio_path}")
        try:
            import numpy as np
            import subprocess
            
            # Command to output raw float32 LE mono audio to stdout
            cmd = [
                "ffmpeg", 
                "-loglevel", "error",
                "-i", str(audio_path),
                "-f", "f32le",
                "-ac", "1", # Downmix to mono
                "-ar", "44100", 
                "-" # Output to pipe
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            peaks = []
            
            # We want 'points_per_second' peaks.
            # Sample Rate = 44100
            # Chunk size = 44100 / points_per_second
            chunk_size = int(44100 / points_per_second)
            bytes_per_chunk = chunk_size * 4
            
            while True:
                raw = process.stdout.read(bytes_per_chunk)
                if not raw:
                    break
                
                count = len(raw) // 4
                if count == 0:
                     break
                     
                y = np.frombuffer(raw, dtype=np.float32, count=count)
                
                if len(y) > 0:
                    # Peak = max absolute value in this chunk
                    peak = float(np.max(np.abs(y)))
                    peaks.append(round(peak, 4))
            
            process.wait()
             
            # Save
            with open(output_path, "w") as f:
                json.dump({"data": peaks, "points_per_second": points_per_second}, f)
                
            print(f"Peaks generated: {len(peaks)} points (Saved to {output_path})")
            
        except Exception as e:
            print(f"Failed to generate peaks: {e}")
