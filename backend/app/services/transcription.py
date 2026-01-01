import os
import logging
from app.core.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

class TranscriptionService:
    def get_lesson_dir(self, lesson_id: str) -> str:
        return os.path.join(PROJECT_ROOT, "data", "lessons", lesson_id)

    def transcribe_segment(self, lesson_id: str, start: float, end: float) -> str:
        """
        Transcribe a segment of the guitar track to ABC notation.
        
        NOTE: Due to Python 3.13 incompatibility with basic-pitch/tensorflow/librosa,
        this service currently runs in MOCK MODE unless libraries are manually installed.
        """
        try:
            # Try importing real libraries
            import librosa
            import numpy as np
            import soundfile as sf
            from basic_pitch.inference import predict
            import music21
            
            # --- REAL IMPLEMENTATION ---
            lesson_dir = self.get_lesson_dir(lesson_id)
            audio_path = os.path.join(lesson_dir, "guitar.mp3")

            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Guitar track not found for lesson {lesson_id}")

            duration = end - start
            if duration <= 0:
                return "z"

            logger.info(f"Loading audio segment: {audio_path} [{start}:{end}]")
            y, sr = librosa.load(audio_path, sr=22050, offset=start, duration=duration)
            
            # Noise Gate
            rms = librosa.feature.rms(y=y)
            if np.max(rms) < 0.02:
                return "z4 |]"

            # Inference
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_wav:
                sf.write(tmp_wav.name, y, sr)
                _, midi_data, _ = predict(tmp_wav.name, onset_threshold=0.6, minimum_frequency=80.0)

            # Quantization
            with tempfile.NamedTemporaryFile(suffix=".mid", delete=True) as tmp_midi:
                midi_data.write(tmp_midi.name)
                s = music21.converter.parse(tmp_midi.name)
                quantized = s.quantize([4], processOffsets=True, processDurations=True)
                
                with tempfile.NamedTemporaryFile(suffix=".abc", delete=True) as tmp_abc:
                    quantized.write('abc', fp=tmp_abc.name)
                    with open(tmp_abc.name, 'r') as f:
                        return f.read()

        except ImportError as e:
            logger.warning(f"AI Dependencies missing ({e}). Using MOCK transcription.")
            # Mock Response for Python 3.13 users
            return self._get_mock_abc(start, end)
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "z4 |] % Error: " + str(e)

    def _get_mock_abc(self, start: float, end: float) -> str:
        """Returns a dummy ABC score for testing/fallback."""
        # Simple C Major scale lick
        return """X:1
T:AI Transcription (Mock)
M:4/4
L:1/8
K:C
cdef g2 e2 | c2 G2 E2 C2 |]"""
