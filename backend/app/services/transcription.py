import os
import logging
import tempfile
import numpy as np
import soundfile as sf
import librosa
import music21
from music21 import abcFormat
from basic_pitch.inference import predict

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    def get_lesson_dir(self, lesson_id: str) -> str:
        settings = get_settings()
        return os.path.join(settings.DATA_DIR, lesson_id)

    def transcribe_segment(self, lesson_id: str, start: float, end: float) -> str:
        """
        Transcribe a segment of the guitar track to ABC notation.
        """
        from app.services.store import StoreService
        store = StoreService()
        overrides = store.get_settings_override()
        settings = get_settings()

        onset_thresh = overrides.get("bp_onset_threshold") or settings.BP_ONSET_THRESHOLD
        min_freq = overrides.get("bp_min_frequency") or settings.BP_MIN_FREQUENCY
        q_grid = overrides.get("bp_quantize_grid") or settings.BP_QUANTIZE_GRID

        try:
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
                # Silence
                return "z4 |]"

            # Inference (Basic Pitch)
            # Create temp wav for basic-pitch
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_wav:
                sf.write(tmp_wav.name, y, sr)
                # Run prediction
                _, midi_data, _ = predict(tmp_wav.name, onset_threshold=onset_thresh, minimum_frequency=min_freq)

            # Quantization (Music21)
            # basic-pitch returns pretty-midi object. Convert to midi file for music21?
            # midi_data is a pretty_midi object.
            
            with tempfile.NamedTemporaryFile(suffix=".mid", delete=True) as tmp_midi:
                midi_data.write(tmp_midi.name)
                s = music21.converter.parse(tmp_midi.name)
                # Quantize to nearest 16th note (approx)
                quantized = s.quantize([q_grid], processOffsets=True, processDurations=True)
                
                # music21 ABC export
                return self._stream_to_abc_manual(quantized)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Return error as comment in ABC so user sees it
            return f"z4 |] % Error: {str(e)}"

    def _stream_to_abc_manual(self, stream) -> str:
        """Manually convert music21 stream to ABC string (Monophonic)."""
        import math
        
        lines = [
            "X:1",
            "T:AI Transcription",
            "M:4/4",
            "L:1/16",
            "K:C"
        ]
        
        # Flatten and get notes/rests
        flat = stream.flat.notesAndRests
        
        abc_notes = []
        for el in flat:
            # Duration (base 1/16th)
            # quarterLength 1.0 = 4 units (16th notes)
            units = el.duration.quarterLength * 4
            dur_str = ""
            if units != 1.0:
                 if abs(round(units) - units) < 0.01:
                     dur_str = str(int(round(units)))
                 else:
                     dur_str = str(int(units)) 
            
            # Element Text
            token = ""
            if el.isRest:
                token = "z"
            elif 'Chord' in el.classes:
                # Handle Chord: [note1 note2]
                chord_notes = []
                for p in el.pitches:
                    chord_notes.append(self._pitch_to_abc(p))
                token = f"[{''.join(chord_notes)}]"
            elif 'Note' in el.classes:
                # Handle Note
                token = self._pitch_to_abc(el.pitch)
            else:
                continue

            abc_notes.append(f"{token}{dur_str}")
        
        lines.append(" ".join(abc_notes) + " |]")
        return "\n".join(lines)

    def _pitch_to_abc(self, pitch_obj) -> str:
        """Helper to convert music21 Pitch to ABC string."""
        step = pitch_obj.step
        accidental = pitch_obj.accidental.modifier if pitch_obj.accidental else ""
        octave = pitch_obj.octave
        
        if octave >= 4:
            note_char = step.lower()
            suffix = "'" * (octave - 4)
        else:
            note_char = step.upper()
            suffix = "," * (3 - octave)
        
        acc_map = {'#': '^', '-': '_', 'n': '='}
        abc_acc = acc_map.get(accidental, "")
        if accidental == '-': abc_acc = '_' 
        elif accidental == 'b': abc_acc = '_'
        
        return f"{abc_acc}{note_char}{suffix}"
