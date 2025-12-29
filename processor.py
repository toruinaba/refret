import sys
import os
import shutil
import json
import subprocess
from pathlib import Path
import soundfile as sf
import torch
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model
from faster_whisper import WhisperModel
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AudioProcessor:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Configure LLM
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.llm_model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.api_key = os.getenv("OPENAI_API_KEY")

        if self.llm_provider == "openai":
            if self.api_key:
                openai.api_key = self.api_key
        elif self.llm_provider == "ollama":
            # Ollama compatibility uses the same OpenAI client structure
            # but points to local server.
            pass

    def separate_audio(self, file_path, lesson_dir):
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
            print(f"Loading audio from: {file_path}")
            if not os.path.exists(file_path):
                 print("ERROR: File does not exist!")
            else:
                 print(f"File size: {os.path.getsize(file_path)} bytes")

            wav_np, sr = sf.read(str(file_path))
            print(f"Loaded audio stats - Shape: {wav_np.shape}, SR: {sr}, Type: {wav_np.dtype}")
            
            # Convert to torch tensor
            wav = torch.from_numpy(wav_np).float()
            
            # Handle shape: soundfile is [time, channels], demucs wants [channels, time]
            if wav.dim() == 1:
                # Mono: [time] -> [1, time]
                wav = wav.unsqueeze(0)
            else:
                # Stereo/Multi: [time, channels] -> [channels, time]
                wav = wav.t()
            
            print(f"Tensor shape (channels, time): {wav.shape}")
            if wav.shape[-1] == 0:
                raise ValueError("Loaded audio is empty (0 frames).")
            
            # Resample if needed
            if sr != model.samplerate:
                print(f"Resampling from {sr} to {model.samplerate}")
                resampler = torchaudio.transforms.Resample(sr, model.samplerate)
                wav = resampler(wav)
            
            # Prepare input for model
            # Demucs expects: [batch, channels, time]
            wav_input = wav.unsqueeze(0) # [1, channels, time]
            
            # Apply Model
            print("Running inference...")
            
            # Normalize for inference (common practice for demucs pretrained)
            # We must capture mean/std to DENORMALIZE output later
            ref_mean = wav_input.mean()
            ref_std = wav_input.std() + 1e-8
            
            wav_norm = (wav_input - ref_mean) / ref_std
            
            sources = apply_model(model, wav_norm, shifts=1, split=True, overlap=0.25, progress=True)[0]
            # sources shape: [sources, channels, time]
            
            # Denormalize sources to match original audio scale
            sources = sources * ref_std + ref_mean
            
            # Identify stems
            # htdemucs sources: ["drums", "bass", "other", "vocals"]
            sources_list = model.sources
            vocals_idx = sources_list.index("vocals")
            vocals_wav = sources[vocals_idx] # [channels, time]
            
            # Calculate No Vocals (Backing)
            # Instead of mix - vocals, we sum the other sources for cleaner separation
            no_vocals_wav = torch.zeros_like(vocals_wav)
            for i, src_name in enumerate(sources_list):
                 if src_name != "vocals":
                     no_vocals_wav += sources[i]
            
            # Ensure proper shape for writing [time, channels]
            vocals_out = vocals_wav.cpu().numpy().T
            backing_out = no_vocals_wav.cpu().numpy().T

            # Prepare paths
            final_vocals_path = lesson_dir / "vocals.wav"
            final_guitar_path = lesson_dir / "guitar.wav"
            
            # Save using soundfile
            sf.write(str(final_vocals_path), vocals_out, model.samplerate)
            sf.write(str(final_guitar_path), backing_out, model.samplerate)
            
            return final_vocals_path, final_guitar_path

        except Exception as e:
            print(f"Error in separation: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def transcribe(self, audio_path):
        """
        Transcribe audio using Faster-Whisper.
        """
        print(f"Transcribing: {audio_path}")
        # Use 'small' model for better accuracy than 'base', especially for non-English.
        model_size = "small"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # Explicitly set language to Japanese
        segments, info = model.transcribe(str(audio_path), beam_size=5, language="ja")
        
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

    def summarize(self, transcript_text):
        """
        Summarize the lesson using OpenAI or Ollama.
        """
        print(f"Summarizing transcript using {self.llm_provider} ({self.llm_model})...")
        
        client = None
        
        try:
            if self.llm_provider == "ollama":
                # Connect to local Ollama instance
                client = openai.OpenAI(
                    base_url="http://localhost:11434/v1",
                    api_key="ollama" # Required but ignored
                )
            else:
                # Default to OpenAI
                if not self.api_key:
                    return {"error": "No OpenAI API Key found", "summary": "N/A"}
                client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant summarizing a guitar lesson. Extract key points, chords mentioned, and techniques practiced. Return a JSON object with keys: 'summary', 'key_points' (list), 'chords' (list)."},
                    {"role": "user", "content": f"Here is the transcript of the guitar lesson:\n\n{transcript_text[:12000]}"} 
                ],
                response_format={"type": "json_object"} if self.llm_provider == "openai" else None
            )
            
            content = response.choices[0].message.content
            
            # Additional cleanup for Ollama if it returns markdown code blocks
            if self.llm_provider == "ollama":
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
        except Exception as e:
            print(f"LLM error: {e}")
            return {"error": str(e)}

    def process_lesson(self, uploaded_file, lesson_title):
        """
        Orchestrate the full pipeline.
        """
        # Create directory for this lesson
        # Sanitize title
        safe_title = "".join([c for c in lesson_title if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")
        lesson_dir = self.data_dir / safe_title
        lesson_dir.mkdir(parents=True, exist_ok=True)

        original_path = lesson_dir / "original.wav"

        # Save uploaded file
        # Convert to WAV using ffmpeg (File-based approach for maximum robustness)
        print(f"Converting upload ({uploaded_file.name}) to WAV...")
        
        # Determine extension or default to .tmp (ffmpeg is good at sniffing headers anyway)
        ext = Path(uploaded_file.name).suffix
        if not ext:
            ext = ".tmp"
            
        temp_input_path = lesson_dir / f"temp_input{ext}"
        
        try:
            # 1. Write uploaded bytes to temp file
            with open(temp_input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            print(f"Saved temp input to {temp_input_path} ({temp_input_path.stat().st_size} bytes)")
            
            # 2. Run FFmpeg conversion
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(temp_input_path),
                "-ac", "2", 
                "-ar", "44100", 
                "-f", "wav",
                str(original_path)
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True
            )
            
            print(f"Converted to {original_path} ({original_path.stat().st_size} bytes)")
            
            # Cleanup temp file
            if temp_input_path.exists():
                temp_input_path.unlink()
            
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg conversion failed: {e}")
            if e.stderr:
                print(f"STDERR: {e.stderr.decode()}")
            # Attempt to use the temp file as original if conversion failed (maybe it was already wav?)
            if temp_input_path.exists():
                 # Copy instead of move to keep logic simple
                 with open(temp_input_path, "rb") as src, open(original_path, "wb") as dst:
                     dst.write(src.read())

        except Exception as e:
             print(f"Generic error in conversion: {e}")
             import traceback
             traceback.print_exc()
             # Last ditch: write bytes directly
             uploaded_file.seek(0)
             with open(original_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        # 1. Separate
        vocals_path, guitar_path = self.separate_audio(original_path, lesson_dir)

        # 2. Transcribe Vocals
        transcript_text, segments = self.transcribe(vocals_path)
        
        # Save transcript
        with open(lesson_dir / "transcript.json", "w") as f:
            json.dump(segments, f, indent=2)
        
        with open(lesson_dir / "transcript.txt", "w") as f:
            f.write(transcript_text)

        # 3. Summarize
        summary_json = self.summarize(transcript_text)
        
        # Save summary
        with open(lesson_dir / "summary.json", "w") as f:
            json.dump(summary_json, f, indent=2)
            
        return lesson_dir
