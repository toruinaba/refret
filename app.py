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

                # Generate Custom HTML for Player & Interactive Summary
                
                html_content = f"""
                <html>
                <head>
                <style>
                    body {{ font-family: sans-serif; color: #333; }}
                    .container {{ display: flex; gap: 20px; }}
                    .player_col {{ flex: 1; padding: 20px; background: #f9f9f9; border-radius: 10px; }}
                    .summary_col {{ flex: 1; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 10px; height: 500px; overflow-y: auto; }}
                    
                    h3 {{ margin-top: 0; }}
                    
                    .audio-control {{ margin-bottom: 20px; }}
                    audio {{ width: 100%; margin-bottom: 10px; }}
                    
                    .speed-controls {{ margin-bottom: 20px; }}
                    .btn {{ 
                        padding: 5px 10px; 
                        margin-right: 5px; 
                        cursor: pointer; 
                        background: #eee; 
                        border: 1px solid #ccc; 
                        border-radius: 4px; 
                    }}
                    .btn:hover {{ background: #ddd; }}
                    .btn.active {{ background: #ff4b4b; color: white; border-color: #ff4b4b; }}
                    
                    .timestamp-link {{
                        color: #ff4b4b;
                        text-decoration: none;
                        font-weight: bold;
                        cursor: pointer;
                    }}
                    .timestamp-link:hover {{ text-decoration: underline; }}
                    
                    ul {{ padding-left: 20px; }}
                    li {{ margin-bottom: 8px; }}
                </style>
                </head>
                <body>
                
                <div class="container">
                    <!-- Left: Players -->
                    <div class="player_col">
                        <h3>🎧 Study Player</h3>
                        
                        <div class="speed-controls">
                            <span style="margin-right: 10px; font-weight: bold;">Speed:</span>
                            <button class="btn" onclick="setSpeed(0.5, this)">0.5x</button>
                            <button class="btn" onclick="setSpeed(0.75, this)">0.75x</button>
                            <button class="btn active" onclick="setSpeed(1.0, this)">1.0x</button>
                        </div>
                        
                        <div class="audio-control">
                            <label><strong>🗣️ Vocals</strong></label>
                            <audio id="player-v" controls>
                                <source src="data:audio/mp3;base64,{vocals_b64}" type="audio/mp3">
                            </audio>
                        </div>
                        
                        <div class="audio-control">
                            <label><strong>🎸 Guitar / Backing</strong></label>
                            <audio id="player-g" controls>
                                <source src="data:audio/mp3;base64,{guitar_b64}" type="audio/mp3">
                            </audio>
                        </div>
                        
                        <p><small><em>Audio players attempt to sync automatically. Use controls above.</em></small></p>
                    </div>
                    
                    <!-- Right: Summary -->
                    <div class="summary_col">
                        <h3>📝 Interactive Notes</h3>
                        <div id="summary-content">
                            <!-- Injected Summary Content -->
                            <h4>Summary</h4>
                            <p>{summary_content.get('summary', 'No summary available.')}</p>
                            
                            <h4>Key Points</h4>
                            <ul>
                """
                
                points = summary_content.get('key_points', [])
                for i, point in enumerate(points):
                    # Mock timestamp logic: distribute points across first 2 mins for demo
                    # In a real app, LLM would extract "[00:30] Chord change"
                    time_sec = (i + 1) * 15 
                    time_fmt = f"{int(time_sec//60):02d}:{int(time_sec%60):02d}"
                    
                    html_content += f"""
                        <li>
                            <a class="timestamp-link" onclick="seekTo({time_sec})">[{time_fmt}]</a>
                            {point}
                        </li>
                    """

                html_content += """
                            </ul>
                            <h4>Chords</h4>
                            <code>""" + ", ".join(summary_content.get('chords', [])) + """</code>
                        </div>
                    </div>
                </div>

                <script>
                    const vPlayer = document.getElementById('player-v');
                    const gPlayer = document.getElementById('player-g');
                    
                    // --- SYNC LOGIC ---
                    // Simple leader-follower sync. If user plays V, G follows.
                    
                    let isSyncing = false;
                    
                    function syncEvent(leader, follower) {
                        leader.onplay = () => { follower.play(); };
                        leader.onpause = () => { follower.pause(); };
                        leader.onseeking = () => { follower.currentTime = leader.currentTime; };
                        leader.onseeked = () => { follower.currentTime = leader.currentTime; };
                    }
                    
                    // Bi-directional sync is tricky without loops. Let's make Vocal leader for now.
                    if (vPlayer && gPlayer) {
                        syncEvent(vPlayer, gPlayer);
                    }
                    
                    // --- SPEED CONTROL ---
                    function setSpeed(rate, btn) {
                        if (vPlayer) vPlayer.playbackRate = rate;
                        if (gPlayer) gPlayer.playbackRate = rate;
                        
                        // Update UI
                        document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                    }
                    
                    // --- SEEK TO ---
                    function seekTo(seconds) {
                        if (vPlayer) {
                            vPlayer.currentTime = seconds;
                            vPlayer.play();
                        }
                        if (gPlayer) {
                            gPlayer.currentTime = seconds;
                        }
                    }
                </script>
                </body>
                </html>
                """
                
                # Render the HTML Component
                components.html(html_content, height=600, scrolling=True)
                
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
