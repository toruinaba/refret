import streamlit as st
import os
import json
import base64
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
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
def get_processor(config, version=1):
    return AudioProcessor(config)

# Load current config
current_config = load_config()
processor = get_processor(current_config, version=2) # Increment version to bust cache

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
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions (Global) ---
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
TAGS_FILE = data_dir / "tags.json"

def load_global_tags():
    """Load global tags list from json."""
    if TAGS_FILE.exists():
        try:
            with open(TAGS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_global_tags(new_tags):
    """Update global tags file with new tags."""
    current_tags = load_global_tags()
    updated = current_tags.union(set(new_tags))
    with open(TAGS_FILE, "w") as f:
        json.dump(sorted(list(updated)), f, indent=4)

def load_metadata(lesson_path):
    """Load metadata.json or create default if missing."""
    meta_file = lesson_path / "metadata.json"
    if meta_file.exists():
        with open(meta_file, "r") as f:
            return json.load(f)
    else:
        # Default metadata
        creation_time = datetime.fromtimestamp(lesson_path.stat().st_ctime).strftime('%Y-%m-%d')
        default_meta = {
            "tags": [],
            "memo": "",
            "created_at": creation_time
        }
        return default_meta

def save_metadata(lesson_path, meta_data):
    """Save metadata to json."""
    with open(lesson_path / "metadata.json", "w") as f:
        json.dump(meta_data, f, indent=4)
    
    # Update global tags
    if "tags" in meta_data:
        save_global_tags(meta_data["tags"])

    # Clear cache to refresh dashboard
    get_library_data.clear()

def get_all_tags():
    """Scan all lessons AND tags.json to find unique tags."""
    if not data_dir.exists():
        return []
    
    # 1. Start with global tags registry
    tags = load_global_tags()
    
    # 2. Scan existing lessons (in case of manual edits or out of sync)
    for lesson_dir in [d for d in data_dir.iterdir() if d.is_dir()]:
        meta = load_metadata(lesson_dir)
        for t in meta.get("tags", []):
            tags.add(t)
            
    return sorted(list(tags))

@st.cache_data
def get_library_data():
    """Scan all lessons and return a DataFrame."""
    rows = []
    if not data_dir.exists():
        return pd.DataFrame()
    
    for lesson_dir in [d for d in data_dir.iterdir() if d.is_dir()]:
        meta = load_metadata(lesson_dir)
        rows.append({
            "Lesson ID": lesson_dir.name, # Hidden or used for key
            "Date": meta.get("created_at", ""),
            "Title": lesson_dir.name, # Use folder name as title. Ideally meta title but fallback to folder
            "Tags": ", ".join(meta.get("tags", [])),
            "Memo": meta.get("memo", "")
        })
    
    if not rows:
        return pd.DataFrame()
        
    df = pd.DataFrame(rows)
    # Sort by Date descending
    if "Date" in df.columns:
        df = df.sort_values("Date", ascending=False)
    return df

# Sidebar Navigation
st.sidebar.title("🎸 Guitar Review")
mode = st.sidebar.radio("Navigation", ["New Lesson (Upload)", "Library (Review)", "Settings"])


st.sidebar.info("Upload your guitar lesson recordings to separate tracks and get AI summaries.")

# --- Mode 1: New Lesson ---
if mode == "New Lesson (Upload)":
    st.title("Upload New Lesson")
    st.write("Upload your guitar lesson recordings to separate tracks and get AI summaries.")
    
    uploaded_file = st.file_uploader("Upload Audio (MP3/WAV/M4A)", type=["mp3", "wav", "m4a"])
    
    # Metadata Inputs for new lesson
    with st.expander("📝 Add Metadata (Optional)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            input_title = st.text_input("Lesson Title (Folder Name)", value="My_Lesson")
        with col2:
            # Tags: Allow selecting existing or adding new
            all_existing_tags = get_all_tags()
            
            # Custom Tag Input to add to options
            new_tag_created = st.text_input("Create New Tag (Press Enter to add to list)")
            if new_tag_created and new_tag_created not in all_existing_tags:
                all_existing_tags.append(new_tag_created)
            
            input_tags = st.multiselect("Select Tags", options=all_existing_tags, default=[new_tag_created] if new_tag_created else [])

        input_memo = st.text_area("Memo (Markdown supported)", height=100)

    if st.button("Start Processing", type="primary"):
        if uploaded_file and input_title:
            try:
                with st.status("Processing Lesson...", expanded=True) as status:
                    
                    st.write("🔄 Initializing & Converting audio format...")
                    lesson_dir, temp_wav = processor.prepare_lesson_upload(uploaded_file, input_title)
                    
                    st.write("🎸 Separating Vocals and Guitar (Demucs)...")
                    vocals_path, guitar_path = processor.separate_audio(temp_wav, lesson_dir)
                    
                    # Cleanup temp wav
                    if temp_wav.exists():
                        temp_wav.unlink()
                    
                    st.write("📜 Transcribing Vocals (Whisper)...")
                    transcript_text, segments = processor.transcribe(vocals_path)
                    
                    st.write("🤖 Generating Summary (LLM)...")
                    summary_json = processor.summarize(segments)
                    
                    st.write("💾 Saving Results...")
                    processor.save_results(lesson_dir, segments, transcript_text, summary_json)
                    
                    # Save Metadata (User Inputs)
                    st.write("📝 Saving Metadata...")
                    meta = {
                        "tags": input_tags,
                        "memo": input_memo,
                        "created_at": datetime.now().strftime('%Y-%m-%d')
                    }
                    save_metadata(lesson_dir, meta)
                    
                    status.update(label="Processing Complete!", state="complete", expanded=False)
                    st.success(f"Lesson '{lesson_dir.name}' processed successfully!")
                    st.balloons()
                    st.info("Go to 'Library (Review)' to see your results.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please upload a file and provide a title.")

# --- Mode 2: Library ---
elif mode == "Library (Review)":
    st.title("Lesson Library")
    
    if not data_dir.exists():
        st.warning("No data directory found.")
    else:
        # Initialize session state for navigation
        if "selected_lesson" not in st.session_state:
            st.session_state.selected_lesson = None

        # --- STATE A: DASHBOARD (LIST VIEW) ---
        if st.session_state.selected_lesson is None:
            
            # 1. Search Bar
            search_query = st.text_input("🔍 Search Lessons", placeholder="Filter by title, tags, or memo...")
            
            # 2. Get Data
            df = get_library_data()
            
            if not df.empty:
                # Filter Logic
                if search_query:
                    # Robust search across all columns
                    try:
                        mask = df.apply(lambda x: x.astype(str).str.contains(search_query, case=False, regex=False).any(), axis=1)
                        df_display = df[mask]
                    except Exception as e:
                        st.error(f"Search error: {e}")
                        df_display = df
                else:
                    df_display = df

                # 3. Interactive Table
                st.caption(f"Showing {len(df_display)} lessons")
                
                event = st.dataframe(
                    df_display,
                    width="stretch",
                    hide_index=True,
                    selection_mode="single-row",
                    on_select="rerun",
                    column_config={
                        "Lesson ID": None, # Hide ID
                        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                        "Title": st.column_config.TextColumn("Title", width="medium"),
                        "Tags": st.column_config.TextColumn("Tags", width="medium"),
                        "Memo": None, # HIDE MEMO from table
                    },
                    key="library_dataframe" 
                )
                
                # Handle Selection
                if event.selection and event.selection["rows"]:
                    selected_index = event.selection["rows"][0]
                    selected_id = df_display.iloc[selected_index]["Lesson ID"]
                    st.session_state.selected_lesson = selected_id
                    st.rerun()
            else:
                st.info("No lessons found. Go to 'New Lesson' to upload one.")

        # --- STATE B: DETAIL VIEW (PLAYER) ---
        else:
            selected_lesson = st.session_state.selected_lesson
            lesson_path = data_dir / selected_lesson
            
            # Navigation
            if st.button("← Back to Library"):
                st.session_state.selected_lesson = None
                st.rerun()
            
            st.header(f"🎸 {selected_lesson}")
            
            # Load Audio Files
            vocals_path = lesson_path / "vocals.mp3"
            guitar_path = lesson_path / "guitar.mp3"
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

            # Load Metadata
            metadata = load_metadata(lesson_path)

            # --- Displays Memo (Markdown) ---
            if metadata.get("memo"):
                with st.expander("📝 My Memo", expanded=True):
                    st.markdown(metadata["memo"])

            # Layout: Player (Main) + Metadata Editor (Sidebar/Column)
            
            # --- Metadata Editor (Sidebar) ---
            with st.sidebar:
                st.subheader("✏️ Lesson Metadata")
                with st.form("metadata_form"):
                    # Tags
                    current_tags = metadata.get("tags", [])
                    
                    # Get all tags for autocomplete
                    all_existing_tags = get_all_tags()
                    
                    # Dynamic Tag Creation
                    new_tag_created = st.text_input("Create New Tag (Save to add)", key="new_tag_sidebar")
                    
                    # If a new tag is entered, add it to the list of options and pre-select it
                    if new_tag_created and new_tag_created not in all_existing_tags:
                        all_existing_tags.append(new_tag_created)
                        # Ensure the new tag is in the default selection if user typed it
                        if new_tag_created not in current_tags:
                            current_tags.append(new_tag_created)

                    available_tags = sorted(list(set(all_existing_tags))) # Use all_existing_tags which now includes the new one
                    
                    updated_tags = st.multiselect("Tags", options=available_tags, default=current_tags)
                    
                    # Memo (Markdown)
                    st.caption("Markdown supported")
                    updated_memo = st.text_area("Memo", value=metadata.get("memo", ""), height=150, help="Markdown syntax supported")
                    
                    if st.form_submit_button("Save Metadata"):
                        metadata["tags"] = updated_tags
                        metadata["memo"] = updated_memo
                        save_metadata(lesson_path, metadata)
                        st.success("Saved!")
                        st.rerun()

            # --- Player Component ---
            
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

                            <div id="timeDisplay" style="font-family: monospace; font-size: 14px; margin-left: 10px;">00:00 / 00:00</div>
                            
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
                            """
            
            if "error" in summary_content:
                html_content += f"""
                    <div style="padding: 10px; background: #fee; color: #c00; border-radius: 5px; margin-bottom: 10px;">
                        <strong>⚠️ Summary Generation Error:</strong><br>
                        {summary_content['error']}
                    </div>
                """
            
            html_content += f"""
                            <h4>Summary</h4>
                            <p>{summary_content.get('summary', 'No summary available.')}</p>
                            
                            <h4>Key Points</h4>
                            <ul>
            """
            
            points = summary_content.get('key_points', [])
            for i, point_data in enumerate(points):
                # Handle both new dict format and old string format
                if isinstance(point_data, dict):
                    point_text = point_data.get("point", "")
                    timestamp_str = point_data.get("timestamp", "00:00")
                else:
                    point_text = str(point_data)
                    timestamp_str = "00:00"

                # Parse timestamp to seconds
                try:
                    parts = timestamp_str.split(":")
                    if len(parts) == 2:
                        time_sec = int(parts[0]) * 60 + int(parts[1])
                    else:
                        time_sec = 0
                except:
                    time_sec = 0

                html_content += f"""
                    <li>
                        <a class="timestamp-link" onclick="seekTo({time_sec})">[{timestamp_str}]</a>
                        {point_text}
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
                const timeDisplay = document.getElementById('timeDisplay');

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

                // --- Helper: Format Time ---
                function formatTime(seconds) {{
                    const m = Math.floor(seconds / 60);
                    const s = Math.floor(seconds % 60);
                    return `${{m.toString().padStart(2, '0')}}:${{s.toString().padStart(2, '0')}}`;
                }}
                
                function updateTimeDisplay() {{
                    const current = wsV.getCurrentTime();
                    const total = wsV.getDuration();
                    if (total > 0) {{
                        timeDisplay.textContent = `${{formatTime(current)}} / ${{formatTime(total)}}`;
                    }} else {{
                         timeDisplay.textContent = "00:00 / 00:00";
                    }}
                }}

                // --- Event Listeners & Sync ---
                
                wsV.on('ready', () => {{ 
                    isReadyV = true; 
                    checkReady();
                    updateTimeDisplay();
                }});
                wsG.on('ready', () => {{ isReadyG = true; checkReady(); }});
                
                // Time Update
                wsV.on('timeupdate', () => {{
                    updateTimeDisplay();
                }});

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
                    updateTimeDisplay();
                }});
                
                // Also sync if user clicks on guitar track
                wsG.on('interaction', () => {{
                    wsV.setTime(wsG.getCurrentTime());
                    updateTimeDisplay();
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
                    console.log("Region Loop");
                    wsV.setTime(region.start);
                    wsG.setTime(region.start);
                    if (!wsV.isPlaying()) {{
                        wsV.play();
                        wsG.play();
                        playBtn.textContent = "⏸";
                    }}
                }});
                
                wsGRegions.on('region-clicked', (region, e) => {{
                    e.stopPropagation();
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
            "Step 1: Analyze the provided transcript with timestamps. "
            "Step 2: Create a concise summary of the lesson content in Japanese. "
            "Step 3: Extract key learning points. For each point, provide the content in Japanese and the closest timestamp (MM:SS) from the source text. "
            "Step 4: List any chords mentioned. "
            "Step 5: Return a valid JSON object strictly following this structure: "
            "{"
            "  \"summary\": \"...summary text...\", "
            "  \"key_points\": [ "
            "    {\"point\": \"...point text...\", \"timestamp\": \"MM:SS\"}, "
            "    ... "
            "  ], "
            "  \"chords\": [\"Am7\", \"G\", ...] "
            "}"
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
