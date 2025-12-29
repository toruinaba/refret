import streamlit as st
import os
import json
import base64
import streamlit.components.v1 as components
from pathlib import Path
from processor import AudioProcessor

# Page Config
st.set_page_config(page_title="Guitar Lesson Review", page_icon="🎸", layout="wide")

# Config File
CONFIG_FILE = Path("config.json")

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_audio_base64(file_path):
    """Read audio file and return base64 string."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except Exception as e:
        print(f"Error reading audio: {e}")
        return None

# Initialize Processor
# Using cache_resource to keep the model loaded, but added ttl to ensure updates propagate during dev
# We need to hash the config so that if config changes, processor re-inits
@st.cache_resource(ttl="1h", hash_funcs={dict: lambda d: json.dumps(d, sort_keys=True)}) 
def get_processor(config):
    return AudioProcessor(config)

# Load current config
current_config = load_config()
processor = get_processor(current_config)

# Custom CSS for aesthetics
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stAudio {
        margin-bottom: 20px;
    }
    .summary-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🎸 Guitar Review")
mode = st.sidebar.radio("Navigation", ["New Lesson (Upload)", "Library (Review)", "Settings"])

st.sidebar.info("Upload your guitar lesson recordings to separate tracks and get AI summaries.")

# --- Mode 1: New Lesson ---
if mode == "New Lesson (Upload)":
    st.title("Upload New Lesson")
    
    with st.container():
        st.write("Upload your lesson recording (WAV/MP3) to begin processing.")
        
        uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a"])
        lesson_title = st.text_input("Lesson Title", placeholder="e.g., Blues Improv Week 1")
        
        if st.button("Start Processing", type="primary"):
            if uploaded_file and lesson_title:
                try:
                    with st.spinner("Processing... This may take a while (Separating Audio -> Transcribing -> Summarizing)"):
                        # Process
                        output_dir = processor.process_lesson(uploaded_file, lesson_title)
                    
                    st.success(f"Processing Complete! Saved to {output_dir}")
                    st.balloons()
                    st.info("Go to 'Library (Review)' to see your results.")
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            else:
                st.warning("Please upload a file and provide a title.")

# --- Mode 2: Library ---
elif mode == "Library (Review)":
    st.title("Lesson Library")
    
    data_dir = Path("data")
    if not data_dir.exists():
        st.warning("No data directory found.")
    else:
        # List subdirectories
        lessons = [d.name for d in data_dir.iterdir() if d.is_dir()]
        lessons.sort()
        
        if not lessons:
            st.info("No lessons found. Go to 'New Lesson' to add one.")
        else:
            selected_lesson = st.selectbox("Select a Lesson", lessons)
            
            if selected_lesson:
                lesson_path = data_dir / selected_lesson
                
                # Load Audio Files
                vocals_path = lesson_path / "vocals.mp3"
                guitar_path = lesson_path / "guitar.mp3"
                # Check for mp3 original, fallback to wav if old lesson
                original_path = lesson_path / "original.mp3"
                if not original_path.exists():
                     original_path = lesson_path / "original.wav"
                
                vocals_b64 = get_audio_base64(vocals_path) if vocals_path.exists() else None
                guitar_b64 = get_audio_base64(guitar_path) if guitar_path.exists() else None

                # Load Summary
                summary_file = lesson_path / "summary.json"
                summary_content = {}
                if summary_file.exists():
                    with open(summary_file, "r") as f:
                        try:
                            summary_content = json.load(f)
                        except json.JSONDecodeError:
                            st.error("Error reading summary file.")

                # Download Buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if vocals_path.exists():
                        with open(vocals_path, "rb") as f:
                            st.download_button("Download Vocals (MP3)", f, file_name="vocals.mp3")
                with col2:
                    if guitar_path.exists():
                        with open(guitar_path, "rb") as f:
                            st.download_button("Download Guitar (MP3)", f, file_name="guitar.mp3")
                with col3:
                    if original_path.exists():
                        with open(original_path, "rb") as f:
                            st.download_button("Download Original (MP3)", f, file_name="original.mp3")

                # Generate Custom HTML for Wavesurfer Player & Interactive Summary
                html_content = f"""
                <html>
                <head>
                <script src="https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.min.js"></script>
                <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
                <style>
                    body {{ font-family: sans-serif; color: #333; margin: 0; padding: 0; }}
                    .container {{ display: flex; gap: 20px; flex-direction: column; }}
                    
                    /* Desktop layout */
                    @media (min-width: 768px) {{
                        .container {{ flex-direction: row; }}
                    }}

                    .player_col {{ flex: 2; padding: 20px; background: #f9f9f9; border-radius: 10px; }}
                    .summary_col {{ flex: 1; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 10px; height: 600px; overflow-y: auto; }}
                    
                    h3 {{ margin-top: 0; }}
                    
                    /* Controls */
                    .controls-area {{ 
                        background: #333; 
                        padding: 15px; 
                        border-radius: 8px; 
                        color: white;
                        display: flex;
                        align-items: center;
                        gap: 20px;
                        margin-bottom: 20px;
                        flex-wrap: wrap;
                    }}
                    
                    .play-btn {{
                        background: #ff4b4b;
                        color: white;
                        border: none;
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        font-size: 24px;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: background 0.2s;
                    }}
                    .play-btn:hover {{ background: #ff3333; }}

                    .slider-group {{ display: flex; flex-direction: column; gap: 5px; min-width: 150px; }}
                    .slider-group label {{ font-size: 12px; color: #ccc; }}
                    input[type=range] {{ width: 100%; cursor: pointer; }}

                    .waveform-box {{
                        margin-bottom: 20px;
                        background: white;
                        padding: 10px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        position: relative;
                    }}
                    .waveform-label {{
                        position: absolute;
                        top: 5px;
                        left: 10px;
                        font-size: 11px;
                        font-weight: bold;
                        z-index: 10;
                        padding: 2px 6px;
                        border-radius: 4px;
                        background: rgba(255,255,255,0.8);
                        pointer-events: none;
                    }}

                    /* Interactive Summary Styles */
                    .timestamp-link {{
                        color: #ff4b4b;
                        text-decoration: none;
                        font-weight: bold;
                        cursor: pointer;
                        padding: 2px 4px;
                        border-radius: 4px;
                        transition: background 0.2s;
                    }}
                    .timestamp-link:hover {{ background: #ffeeee; text-decoration: underline; }}
                    
                    ul {{ padding-left: 20px; }}
                    li {{ margin-bottom: 12px; line-height: 1.5; }}
                </style>
                </head>
                <body>
                
                <div class="container">
                    <!-- Left: Players -->
                    <div class="player_col">
                        <h3>🎧 Study Player</h3>
                        
                        <div class="controls-area">
                            <button id="playBtn" class="play-btn">▶</button>
                            
                            <div class="slider-group">
                                <label>Speed: <span id="speedVal">1.0</span>x</label>
                                <input type="range" id="speedSlider" min="0.25" max="1.5" step="0.05" value="1.0">
                            </div>

                            <div class="slider-group">
                                <label>Zoom</label>
                                <input type="range" id="zoomSlider" min="10" max="200" step="10" value="20">
                            </div>

                            <div class="slider-group" style="min-width: 120px;">
                                <label>Tracks</label>
                                <div style="display: flex; gap: 10px; align-items: center; height: 20px;">
                                    <label style="color: white; font-size: 11px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                                        <input type="checkbox" id="muteV" checked> Vocals
                                    </label>
                                    <label style="color: white; font-size: 11px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                                        <input type="checkbox" id="muteG" checked> Guitar
                                    </label>
                                </div>
                            </div>
                            
                            <div style="font-size: 0.9em; margin-left: auto; color: #aaa;">
                                <small>💡 Drag guitar track to loop</small>
                            </div>
                        </div>

                        <!-- Vocals -->
                        <div class="waveform-box">
                            <div class="waveform-label">🗣️ Vocals</div>
                            <div id="waveform-v"></div>
                        </div>
                        
                        <!-- Guitar -->
                        <div class="waveform-box">
                            <div class="waveform-label">🎸 Guitar</div>
                            <div id="waveform-g"></div>
                        </div>
                    </div>
                    
                    <!-- Right: Summary -->
                    <div class="summary_col">
                        <h3>📝 Interactive Notes</h3>
                        <div id="summary-content">
                            <h4>Summary</h4>
                            <p>{summary_content.get('summary', 'No summary available.')}</p>
                            
                            <h4>Key Points</h4>
                            <ul>
                """
                
                points = summary_content.get('key_points', [])
                for i, point in enumerate(points):
                    # Mock timestamp logic again for demo if real timestamps aren't parsed
                    time_sec = (i + 1) * 15 
                    time_fmt = f"{int(time_sec//60):02d}:{int(time_sec%60):02d}"
                    
                    html_content += f"""
                        <li>
                            <a class="timestamp-link" onclick="seekTo({time_sec})">[{time_fmt}]</a>
                            {point}
                        </li>
                    """

                html_content += f"""
                            </ul>
                            <h4>Chords</h4>
                            <code>{", ".join(summary_content.get('chords', []))}</code>
                        </div>
                    </div>
                </div>

                <script>
                    // Base64 Audio Data
                    const vocalsData = "data:audio/mp3;base64,{vocals_b64}";
                    const guitarData = "data:audio/mp3;base64,{guitar_b64}";

                    // Components
                    const playBtn = document.getElementById('playBtn');
                    const speedSlider = document.getElementById('speedSlider');
                    const speedVal = document.getElementById('speedVal');
                    const zoomSlider = document.getElementById('zoomSlider');
                    const muteV = document.getElementById('muteV');
                    const muteG = document.getElementById('muteG');

                    // Initialize Wavesurfer Instances
                    let wsV, wsG;
                    let isReadyV = false;
                    let isReadyG = false;

                    // 1. Vocals (Master)
                    wsV = WaveSurfer.create({{
                        container: '#waveform-v',
                        waveColor: '#A855F7',
                        progressColor: '#7E22CE',
                        cursorColor: '#7E22CE',
                        barWidth: 2,
                        barGap: 1,
                        barRadius: 2,
                        height: 100,
                        normalize: true,
                        minPxPerSec: 20,
                    }});

                    // 2. Guitar (Follower + Regions)
                    wsG = WaveSurfer.create({{
                        container: '#waveform-g',
                        waveColor: '#F97316',
                        progressColor: '#C2410C',
                        cursorColor: '#C2410C',
                        barWidth: 2,
                        barGap: 1,
                        barRadius: 2,
                        height: 100,
                        normalize: true,
                        minPxPerSec: 20,
                        plugins: [
                            WaveSurfer.Regions.create()
                        ]
                    }});

                    // Load Audio
                    wsV.load(vocalsData);
                    wsG.load(guitarData);

                    // --- Event Listeners & Sync ---
                    
                    wsV.on('ready', () => {{ isReadyV = true; checkReady(); }});
                    wsG.on('ready', () => {{ isReadyG = true; checkReady(); }});

                    function checkReady() {{
                        if (isReadyV && isReadyG) {{
                            console.log("Both tracks ready");
                        }}
                    }}

                    // Play/Pause Toggle
                    playBtn.onclick = () => {{
                        if (wsV.isPlaying()) {{
                            wsV.pause();
                            wsG.pause();
                            playBtn.textContent = "▶";
                        }} else {{
                            wsV.play();
                            wsG.play();
                            playBtn.textContent = "⏸";
                        }}
                    }};

                    // Sync: Seek
                    wsV.on('seeking', (currentTime) => {{
                        wsG.setTime(currentTime);
                    }});
                    
                    // Also sync if user clicks on guitar track
                    wsG.on('interaction', () => {{
                        wsV.setTime(wsG.getCurrentTime());
                    }});
                    
                    // Sync: Finish
                    wsV.on('finish', () => {{
                        wsG.stop();
                        playBtn.textContent = "▶";
                    }});

                    // Speed Control
                    speedSlider.oninput = function() {{
                        const speed = parseFloat(this.value);
                        speedVal.textContent = speed.toFixed(1);
                        wsV.setPlaybackRate(speed);
                        wsG.setPlaybackRate(speed);
                    }};

                    // Zoom Control
                    zoomSlider.oninput = function() {{
                        const pxPerSec = parseInt(this.value);
                        wsV.zoom(pxPerSec);
                        wsG.zoom(pxPerSec);
                    }};
                    
                    // Mute Control
                    // Checkbox checked = sound ON. Unchecked = Muted.
                    muteV.onchange = function() {{
                        wsV.setMuted(!this.checked);
                    }};
                    
                    muteG.onchange = function() {{
                        wsG.setMuted(!this.checked);
                    }};

                    // --- Looping (Regions) ---

                    const wsGRegions = wsG.plugins[0];
                    
                    wsGRegions.enableDragSelection({{
                        color: 'rgba(255, 0, 0, 0.1)',
                    }});

                    // On Region Loop
                    wsGRegions.on('region-out', (region) => {{
                        // When playing exits region, jump back to start
                        console.log("Region Loop");
                        wsV.setTime(region.start);
                        wsG.setTime(region.start);
                        // Ensure playing continues
                        if (!wsV.isPlaying()) {{
                            wsV.play();
                            wsG.play();
                            playBtn.textContent = "⏸";
                        }}
                    }});
                    
                    wsGRegions.on('region-clicked', (region, e) => {{
                        e.stopPropagation(); // prevent seek
                        wsV.setTime(region.start);
                        wsG.setTime(region.start);
                        wsV.play();
                        wsG.play();
                        playBtn.textContent = "⏸";
                    }});

                    // --- External API ---
                    window.seekTo = function(seconds) {{
                        wsV.setTime(seconds);
                        wsG.setTime(seconds);
                        wsV.play();
                        wsG.play();
                        playBtn.textContent = "⏸";
                        
                        // Clear active regions if any to avoid getting stuck in a loop from elsewhere
                        wsGRegions.clearRegions();
                    }};

                </script>
                </body>
                </html>
                """

                # Render
                components.html(html_content, height=800, scrolling=True)
                
                st.divider()
                
                # Transcript
                st.subheader("📜 Full Transcript")
                transcript_file = lesson_path / "transcript.txt"
                if transcript_file.exists():
                    with st.expander("Show Transcript", expanded=False):
                        with open(transcript_file, "r") as f:
                            st.text(f.read())
                else:
                    st.caption("No transcript file found.")

# --- Mode 3: Settings ---
elif mode == "Settings":
    st.title("Settings")
    
    with st.container():
        st.write("Configure your LLM settings here.")
        
        # Load current values from config or env defaults
        default_provider = current_config.get("llm_provider") or os.getenv("LLM_PROVIDER", "openai")
        default_api_key = current_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        default_model = current_config.get("llm_model") or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        # Default Japanese System Prompt
        default_prompt_text = (
            "You are a helpful assistant summarizing a guitar lesson. "
            "Extract key points, chords mentioned, and techniques practiced. "
            "Return a JSON object with keys: 'summary', 'key_points' (list), 'chords' (list). "
            "IMPORTANT: Please write the summary and key points in Japanese."
        )
        default_prompt = current_config.get("system_prompt", default_prompt_text)
        
        with st.form("settings_form"):
            new_provider = st.selectbox("LLM Provider", ["openai", "ollama"], index=0 if default_provider == "openai" else 1)
            new_api_key = st.text_input("OpenAI API Key (Ignored for Ollama)", value=default_api_key, type="password")
            new_model = st.text_input("LLM Model Name", value=default_model, help="e.g., gpt-4o-mini, llama3")
            new_prompt = st.text_area("System Prompt", value=default_prompt, height=150)
            
            submitted = st.form_submit_button("Save Settings")
            
            if submitted:
                new_config = {
                    "llm_provider": new_provider,
                    "openai_api_key": new_api_key,
                    "llm_model": new_model,
                    "system_prompt": new_prompt
                }
                
                save_config(new_config)
                
                # Update at runtime
                processor.update_config(new_config)
                
                st.success("Settings saved successfully!")
                st.rerun()
