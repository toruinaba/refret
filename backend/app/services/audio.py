import os
import subprocess
from pathlib import Path
import soundfile as sf
import torch
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model
from faster_whisper import WhisperModel
import openai
from langchain_openai import ChatOpenAI

from backend.app.core.config import get_settings
from backend.app.schemas.lesson import LessonSummary

class AudioProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        
        # Configure LLM
        self._configure_llm()

    def _configure_llm(self):
        """Configure LLM client based on current settings."""
        if self.settings.LLM_PROVIDER == "openai":
            if self.settings.OPENAI_API_KEY:
                openai.api_key = self.settings.OPENAI_API_KEY

    def separate_audio(self, file_path: Path, lesson_dir: Path):
        """
        Separate audio into vocals and guitar using Demucs (Manual Inference).
        returns: (vocals_path, guitar_path)
        """
        print(f"Separating audio (In-Process Manual): {file_path}")
        
        try:
            # Load Model
            model = get_model("htdemucs")
            model.cpu()
            model.eval()

            # Load Audio using soundfile to bypass torchaudio backend issues
            wav_np, sr = sf.read(str(file_path))
            
            # Convert to torch tensor
            wav = torch.from_numpy(wav_np).float()
            
            # Handle shape
            if wav.dim() == 1:
                wav = wav.unsqueeze(0)
            else:
                wav = wav.t()
            
            if wav.shape[-1] == 0:
                raise ValueError("Loaded audio is empty.")
            
            # Resample if needed
            if sr != model.samplerate:
                resampler = torchaudio.transforms.Resample(sr, model.samplerate)
                wav = resampler(wav)
            
            # Prepare input: [1, channels, time]
            wav_input = wav.unsqueeze(0)
            
            # Normalize
            ref_mean = wav_input.mean()
            ref_std = wav_input.std() + 1e-8
            wav_norm = (wav_input - ref_mean) / ref_std
            
            # Inference
            print("Running inference...")
            sources = apply_model(model, wav_norm, shifts=1, split=True, overlap=0.25, progress=True)[0]
            
            # Denormalize
            sources = sources * ref_std + ref_mean
            
            # Identify stems
            sources_list = model.sources
            vocals_idx = sources_list.index("vocals")
            vocals_wav = sources[vocals_idx] # [channels, time]
            
            # Calculate No Vocals (Backing)
            no_vocals_wav = torch.zeros_like(vocals_wav)
            for i, src_name in enumerate(sources_list):
                 if src_name != "vocals":
                     no_vocals_wav += sources[i]
            
            # Ensure proper shape for writing [time, channels]
            vocals_out = vocals_wav.cpu().numpy().T
            backing_out = no_vocals_wav.cpu().numpy().T

            # Prepare paths
            temp_vocals_path = lesson_dir / "vocals_temp.wav"
            temp_guitar_path = lesson_dir / "guitar_temp.wav"
            final_vocals_path = lesson_dir / "vocals.mp3"
            final_guitar_path = lesson_dir / "guitar.mp3"
            
            # Save WAV
            sf.write(str(temp_vocals_path), vocals_out, model.samplerate)
            sf.write(str(temp_guitar_path), backing_out, model.samplerate)
            
            # Convert to MP3
            self._convert_to_mp3(temp_vocals_path, final_vocals_path)
            self._convert_to_mp3(temp_guitar_path, final_guitar_path)
            
            return final_vocals_path, final_guitar_path

        except Exception as e:
            print(f"Error in separation: {e}")
            raise e

    def _convert_to_mp3(self, input_path: Path, output_path: Path):
        print(f"Converting {input_path} to MP3...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-codec:a", "libmp3lame",
            "-b:a", "192k",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        if input_path.exists():
            input_path.unlink()

    def transcribe(self, audio_path: Path):
        """Transcribe audio using Faster-Whisper."""
        print(f"Transcribing: {audio_path}")
        model_size = "small"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        segments, info = model.transcribe(
            str(audio_path), 
            beam_size=5, 
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
        
        # Format transcript
        transcript_with_timestamps = ""
        for seg in segments_data:
            start_time = seg["start"]
            m = int(start_time // 60)
            s = int(start_time % 60)
            timestamp = f"{m:02d}:{s:02d}"
            transcript_with_timestamps += f"[{timestamp}] {seg['text']}\n"
        
        system_instruction = self.settings.SYSTEM_PROMPT
        
        try:
            if self.settings.LLM_PROVIDER == "openai":
                if not self.settings.OPENAI_API_KEY:
                    return {"error": "No OpenAI API Key found", "summary": "N/A"}
                
                llm = ChatOpenAI(
                    model=self.settings.LLM_MODEL, 
                    api_key=self.settings.OPENAI_API_KEY,
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
