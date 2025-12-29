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
    def __init__(self, config=None):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Default Config from Env / Defaults
        self.config = {
            "llm_provider": os.getenv("LLM_PROVIDER", "openai").lower(),
            "llm_model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "system_prompt": (
                "You are a helpful assistant summarizing a guitar lesson. "
                "Extract key points, chords mentioned, and techniques practiced. "
                "Return a JSON object with keys: 'summary', 'key_points' (list), 'chords' (list). "
                "IMPORTANT: Please write the summary and key points in Japanese."
            )
        }
        
        # Override with passed config
        if config:
            self.config.update(config)

        self._configure_llm()

    def update_config(self, new_config):
        """Update configuration at runtime."""
        if new_config:
            self.config.update(new_config)
            self._configure_llm()

    def _configure_llm(self):
        """Configure LLM client based on current config."""
        self.llm_provider = self.config.get("llm_provider", "openai")
        self.llm_model = self.config.get("llm_model", "gpt-3.5-turbo")
        self.api_key = self.config.get("openai_api_key")
        
        if self.llm_provider == "openai":
            if self.api_key:
                openai.api_key = self.api_key
        # Ollama doesn't need explicit key setting usually, effectively handled in summarize

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
            temp_vocals_path = lesson_dir / "vocals_temp.wav"
            temp_guitar_path = lesson_dir / "guitar_temp.wav"
            final_vocals_path = lesson_dir / "vocals.mp3"
            final_guitar_path = lesson_dir / "guitar.mp3"
            
            # Save using soundfile (WAV first)
            sf.write(str(temp_vocals_path), vocals_out, model.samplerate)
            sf.write(str(temp_guitar_path), backing_out, model.samplerate)
            
            # Convert to MP3
            def convert_to_mp3(input_path, output_path):
                print(f"Converting {input_path} to MP3...")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(input_path),
                    "-codec:a", "libmp3lame",
                    "-b:a", "192k",
                    str(output_path)
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                # Remove temp wav
                input_path.unlink()

            try:
                convert_to_mp3(temp_vocals_path, final_vocals_path)
                convert_to_mp3(temp_guitar_path, final_guitar_path)
            except subprocess.CalledProcessError as e:
                print(f"MP3 Conversion failed: {e}")
                # Fallback: keep WAVs if MP3 fails (renaming for consistency if needed, needs logic)
                # For now, let's assume ffmpeg is present as verified before.
                raise e
            
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

            system_prompt = self.config.get("system_prompt", "You are a helpful assistant summarizing a guitar lesson. Extract key points, chords mentioned, and techniques practiced. Return a JSON object with keys: 'summary', 'key_points' (list), 'chords' (list).")

            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
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

        original_mp3_path = lesson_dir / "original.mp3"

        # Save uploaded file
        # Convert to MP3 using ffmpeg (File-based approach for maximum robustness & space saving)
        print(f"Converting upload ({uploaded_file.name}) to MP3...")
        
        # Determine extension or default to .tmp
        ext = Path(uploaded_file.name).suffix
        if not ext:
            ext = ".tmp"
            
        temp_input_path = lesson_dir / f"temp_input{ext}"
        
        try:
            # 1. Write uploaded bytes to temp file
            with open(temp_input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            print(f"Saved temp input to {temp_input_path} ({temp_input_path.stat().st_size} bytes)")
            
            # 2. Run FFmpeg conversion to MP3
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(temp_input_path),
                "-codec:a", "libmp3lame", 
                "-b:a", "192k",
                str(original_mp3_path)
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True
            )
            
            print(f"Converted to {original_mp3_path} ({original_mp3_path.stat().st_size} bytes)")
            
            # Cleanup temp input
            if temp_input_path.exists():
                temp_input_path.unlink()
            
            # 3. Create a temporary WAV for processing (Demucs/Soundfile best compatibility)
            # We don't want to keep this, just use it for separation
            temp_proc_wav = lesson_dir / "proc_temp.wav"
            cmd_wav = [
                "ffmpeg", "-y",
                "-i", str(original_mp3_path),
                "-ac", "2", 
                "-ar", "44100", 
                "-f", "wav",
                str(temp_proc_wav)
            ]
            subprocess.run(cmd_wav, check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg conversion failed: {e}")
            if e.stderr:
                print(f"STDERR: {e.stderr.decode()}")
            raise e
        except Exception as e:
             print(f"Generic error in conversion: {e}")
             import traceback
             traceback.print_exc()
             raise e

        # 1. Separate (Using the temp WAV for stability)
        vocals_path, guitar_path = self.separate_audio(temp_proc_wav, lesson_dir)
        
        # Cleanup temp processing wav
        if temp_proc_wav.exists():
            temp_proc_wav.unlink()

        # 2. Transcribe Vocals (Whisper can read MP3 directly usually, code assumes path)
        # Note: separate_audio returns MP3 paths now.
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
