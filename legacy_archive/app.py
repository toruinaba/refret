import streamlit as st
import os
import json
import base64
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from pathlib import Path
from processor import AudioProcessor
import licks_manager

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

def play_lick(lick):
    """Callback to play a lick in Lick Player mode."""
    st.session_state.selected_lesson = lick['lesson_dir']
    st.session_state.current_lick = lick
    st.session_state["nav_mode"] = "Lick Library 🎸"

# Sidebar Navigation
st.sidebar.title("🎸 Guitar Review")
mode = st.sidebar.radio("Navigation", ["New Lesson (Upload)", "Library (Review)", "Lick Library 🎸", "Settings"], key="nav_mode")


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
            
            # Title First (User Request)
            st.title(f"🎸 {selected_lesson}")

            # Minimal Navigation
            if st.button("← Back to Library"):
                st.session_state.selected_lesson = None
                st.rerun()
            
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



            # --- Player Component ---
            




            # Auto-Loop Logic: Check session state for requested loop
            auto_loop_start = st.session_state.get("auto_loop_start", None)
            auto_loop_end = st.session_state.get("auto_loop_end", None)
            
            # Clear them so we don't loop on every refresh
            if "auto_loop_start" in st.session_state:
                del st.session_state["auto_loop_start"]
            if "auto_loop_end" in st.session_state:
                del st.session_state["auto_loop_end"]

            # Get tags for JS autocomplete
            all_tags_json = json.dumps(get_all_tags())

            # --- 1. Player Component HTML ---
            player_html = f"""
                <html>
                <head>
                <script src="https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.min.js"></script>
                <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
                <style>
                    body {{ font-family: sans-serif; color: #333; margin: 0; padding: 10px; background: #f9f9f9; overflow: hidden; }}
                    /* Controls */
                    .controls-area {{ 
                        background: #333; 
                        padding: 10px; 
                        border-radius: 8px; 
                        color: white;
                        display: flex;
                        align-items: center;
                        gap: 15px;
                        margin-bottom: 10px;
                        flex-wrap: wrap;
                    }}
                    .play-btn {{
                        background: #ff4b4b; color: white; border: none; width: 40px; height: 40px;
                        border-radius: 50%; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center;
                    }}
                    .play-btn:hover {{ background: #ff3333; }}
                    .slider-group {{ display: flex; flex-direction: column; gap: 2px; min-width: 120px; }}
                    .slider-group label {{ font-size: 11px; color: #ccc; }}
                    input[type=range] {{ width: 100%; cursor: pointer; }}
                    
                    .waveform-box {{
                        margin-bottom: 10px; background: white; padding: 5px; border-radius: 6px; position: relative;
                        height: 80px;
                    }}
                    .waveform-label {{
                        position: absolute; top: 2px; left: 5px; font-size: 10px; font-weight: bold;
                        padding: 1px 4px; border-radius: 3px; background: rgba(255,255,255,0.8); pointer-events: none; z-index: 10;
                    }}
                    #regionInfo {{
                        color: #ccc; font-size: 12px; font-weight: bold; margin-left: 15px; border-left: 1px solid #555; padding-left: 15px;
                    }}
                </style>
                </head>
                <body>
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
                        <div class="slider-group" style="min-width: 100px;">
                             <div style="display: flex; gap: 8px; align-items: center;">
                                <label style="color: white; font-size: 10px;"><input type="checkbox" id="muteV" checked> Vocals</label>
                                <label style="color: white; font-size: 10px;"><input type="checkbox" id="muteG" checked> Guitar</label>
                            </div>
                        </div>
                        <div id="timeDisplay" style="font-family: monospace; font-size: 12px; margin-left: auto;">00:00 / 00:00</div>
                        <div id="regionInfo">Selection: --</div>
                    </div>

                    <div class="waveform-box">
                        <div class="waveform-label">🗣️ Vocals</div>
                        <div id="waveform-v"></div>
                    </div>
                    <div class="waveform-box">
                        <div class="waveform-label">🎸 Guitar</div>
                        <div id="waveform-g"></div>
                    </div>

                    <script>
                        const vocalsData = "data:audio/mp3;base64,{vocals_b64}";
                        const guitarData = "data:audio/mp3;base64,{guitar_b64}";
                        const autoStart = {auto_loop_start if auto_loop_start is not None else 'null'};
                        const autoEnd = {auto_loop_end if auto_loop_end is not None else 'null'};

                        // Broadcast Channel Receiver
                        const bc = new BroadcastChannel('refret_sync');

                        // Elements
                        const playBtn = document.getElementById('playBtn');
                        const speedSlider = document.getElementById('speedSlider');
                        const speedVal = document.getElementById('speedVal');
                        const zoomSlider = document.getElementById('zoomSlider');
                        const muteV = document.getElementById('muteV');
                        const muteG = document.getElementById('muteG');
                        const timeDisplay = document.getElementById('timeDisplay');
                        const regionInfo = document.getElementById('regionInfo');

                        let wsV = WaveSurfer.create({{
                            container: '#waveform-v', waveColor: '#A855F7', progressColor: '#7E22CE', cursorColor: '#7E22CE',
                            barWidth: 2, barGap: 1, barRadius: 2, height: 70, normalize: true, minPxPerSec: 20
                        }});
                        let wsG = WaveSurfer.create({{
                            container: '#waveform-g', waveColor: '#F97316', progressColor: '#C2410C', cursorColor: '#C2410C',
                            barWidth: 2, barGap: 1, barRadius: 2, height: 70, normalize: true, minPxPerSec: 20,
                            plugins: [ WaveSurfer.Regions.create() ]
                        }});

                        wsV.load(vocalsData);
                        wsG.load(guitarData);

                        let isReadyV = false;
                        let isReadyG = false;

                        // Unified Play/Pause
                        const togglePlay = () => {{
                            if(wsV.isPlaying()) {{ wsV.pause(); wsG.pause(); playBtn.textContent = "▶"; }}
                            else {{ wsV.play(); wsG.play(); playBtn.textContent = "⏸"; }}
                        }};
                        playBtn.onclick = togglePlay;

                        // Ready Handler
                        const checkReady = () => {{
                            if(isReadyV && isReadyG) {{
                                if(autoStart !== null && autoEnd !== null) {{
                                    const wsGRegions = wsG.plugins[0];
                                    wsGRegions.addRegion({{ start: autoStart, end: autoEnd, color: "rgba(255, 0, 0, 0.3)", loop: true }});
                                    wsV.setTime(autoStart); wsG.setTime(autoStart);
                                    wsV.play(); wsG.play();
                                    playBtn.textContent = "⏸";
                                }}
                            }}
                        }};

                        wsV.on('ready', () => {{ isReadyV = true; checkReady(); }});
                        wsG.on('ready', () => {{ isReadyG = true; checkReady(); }});
                        
                        // Sync
                        wsV.on('seek', (p) => {{ wsG.seekTo(p); }});
                        wsG.on('seek', (p) => {{ wsV.seekTo(p); }});
                        wsV.on('finish', () => {{ playBtn.textContent = "▶"; }});

                        // Controls
                        speedSlider.oninput = () => {{
                            const rate = parseFloat(speedSlider.value);
                            wsV.setPlaybackRate(rate); wsG.setPlaybackRate(rate);
                            speedVal.textContent = rate.toFixed(1);
                        }};
                        zoomSlider.oninput = () => {{
                            const z = parseInt(zoomSlider.value);
                            wsV.zoom(z); wsG.zoom(z);
                        }};
                        muteV.onchange = () => {{ wsV.setMuted(!muteV.checked); }};
                        muteG.onchange = () => {{ wsG.setMuted(!muteG.checked); }};

                        // Time Display
                        wsV.on('timeupdate', () => {{
                            const cur = wsV.getCurrentTime();
                            const tot = wsV.getDuration() || 0;
                            const fmt = (s) => {{
                                const m = Math.floor(s/60); const sec = Math.floor(s%60);
                                return `${{m.toString().padStart(2,'0')}}:${{sec.toString().padStart(2,'0')}}`;
                            }};
                            timeDisplay.textContent = `${{fmt(cur)}} / ${{fmt(tot)}}`;
                        }});

                        // Region Info
                        const wsGRegions = wsG.plugins[0];
                        
                        // Enable Drag Selection
                        // Enable Drag Selection
                        wsGRegions.enableDragSelection({{
                            color: 'rgba(255, 0, 0, 0.3)',
                        }});

                        const updateInfo = (region) => {{
                            regionInfo.innerText = `Selection: ${{region.start.toFixed(2)}}s - ${{region.end.toFixed(2)}}s`;
                        }};
                        
                        wsGRegions.on('region-created', (region) => {{
                            // Enforce Single Region: Clear others
                            wsGRegions.getRegions().forEach(r => {{
                                if (r !== region) r.remove();
                            }});
                            updateInfo(region);
                        }});
                        
                        wsGRegions.on('region-updated', (region) => {{
                            updateInfo(region);
                        }});
                        
                        // Manual Loop Sync
                        wsGRegions.on('region-out', (region) => {{
                            wsV.setTime(region.start);
                            wsG.setTime(region.start);
                            wsV.play();
                            wsG.play();
                        }});
                        
                        wsGRegions.on('region-clicked', (region, e) => {{
                            e.stopPropagation();
                            wsV.setTime(region.start);
                            wsG.setTime(region.start);
                            wsV.play();
                            wsG.play();
                            playBtn.textContent = "⏸";
                            updateInfo(region);
                        }});

                        // Broadcast Listener (Seek)
                        bc.onmessage = (event) => {{
                            if (event.data.cmd === 'seek') {{
                                const t = event.data.time;
                                wsV.setTime(t); wsG.setTime(t);
                                wsV.play(); wsG.play();
                                playBtn.textContent = "⏸";
                            }}
                        }};
                    </script>
                </body>
                </html>
            """
            
            # --- 2. Summary Component HTML ---
            summary_html = f"""
                <html>
                <head>
                <style>
                    body {{ font-family: sans-serif; color: #333; margin: 0; padding: 10px; }}
                    h4 {{ margin-top: 10px; margin-bottom: 5px; color: #555; }}
                    ul {{ padding-left: 20px; }}
                    li {{ margin-bottom: 8px; line-height: 1.4; font-size: 14px; }}
                    .timestamp-link {{
                        color: #ff4b4b; text-decoration: none; font-weight: bold; cursor: pointer;
                        padding: 1px 4px; border-radius: 3px; background: #fff0f0;
                    }}
                    .timestamp-link:hover {{ background: #ffcccc; }}
                    code {{ background: #eee; padding: 2px 4px; border-radius: 4px; font-family: monospace; }}
                </style>
                </head>
                <body>
                    <h3>📝 Interactive Notes</h3>
                    <div id="summary-content">
            """
            
            if "error" in summary_content:
                summary_html += f"<div style='color:red'><strong>Error:</strong> {summary_content['error']}</div>"
            
            summary_html += f"""
                <p>{summary_content.get('summary', 'No summary.')}</p>
                <h4>Key Points</h4>
                <ul>
            """
            
            points = summary_content.get('key_points', [])
            for point_data in points:
                if isinstance(point_data, dict):
                    pt = point_data.get("point", "")
                    ts = point_data.get("timestamp", "00:00")
                else:
                    pt = str(point_data)
                    ts = "00:00"
                
                # Parse
                try:
                    parts = ts.split(":")
                    if len(parts) == 2:
                        ts_sec = int(parts[0]) * 60 + int(parts[1])
                    else:
                        ts_sec = 0
                except:
                    ts_sec = 0
                    
                summary_html += f"""
                    <li>
                        <a class="timestamp-link" onclick="seekTo({ts_sec})">[{ts}]</a> {pt}
                    </li>
                """
            
            summary_html += f"""
                </ul>
                <h4>Chords</h4>
                <code>{", ".join(summary_content.get('chords', []))}</code>
                
                <script>
                    const bc = new BroadcastChannel('refret_sync');
                    function seekTo(seconds) {{
                        bc.postMessage({{cmd: 'seek', time: seconds}});
                    }}
                </script>
                </div> <!-- End Summary Content -->
                </body>
                </html>
            """

            # --- RENDER LAYOUT ---
            
            # 1. Sticky Player Header
            st.markdown(
                """
                <style>
                    /* Stickiness for the first iframe (Player) */
                    iframe[title="streamlit.components.v1.html"]:nth-of-type(1) {
                        position: sticky;
                        top: 0;
                        z-index: 100;
                        background: #f0f2f6; 
                        border-bottom: 2px solid #ddd;
                    }
                </style>
                """, unsafe_allow_html=True
            )
            
            components.html(player_html, height=340, scrolling=False)
            
            # 2. Scrollable Content Area
            with st.container(height=600):
                # Summary
                components.html(summary_html, height=450, scrolling=True)
                
                st.divider()
                
                # --- Metadata & Memo Editor ---
                with st.expander("📝 Metadata & Memo", expanded=True):
                    with st.form("metadata_form_inline"):
                        # Tags
                        current_tags = metadata.get("tags", [])
                        all_existing_tags = get_all_tags()
                        
                        # New Tag Logic (Simple)
                        col_m1, col_m2 = st.columns([1, 2])
                        with col_m1:
                             new_tag_created = st.text_input("Create New Tag", key="new_tag_inline")
                        with col_m2:
                             if new_tag_created and new_tag_created not in all_existing_tags:
                                 all_existing_tags.append(new_tag_created)
                                 if new_tag_created not in current_tags:
                                     current_tags.append(new_tag_created)
                             
                             available_tags = sorted(list(set(all_existing_tags)))
                             updated_tags = st.multiselect("Tags", options=available_tags, default=current_tags)
                        
                        updated_memo = st.text_area("Memo (Markdown)", value=metadata.get("memo", ""), height=150)
                        
                        if st.form_submit_button("Save Metadata"):
                            metadata["tags"] = updated_tags
                            metadata["memo"] = updated_memo
                            save_metadata(lesson_path, metadata)
                            st.success("Metadata Saved!")
                            st.rerun()

                st.divider()

                # Manual Save Lick Form
                with st.expander("💾 Save Current Loop as Lick", expanded=True):
                    st.caption("Tip: Check 'Selection' in player above.")
                    with st.form("save_lick_form"):
                        col_l1, col_l2 = st.columns(2)
                        with col_l1:
                             lick_title_in = st.text_input("Lick Title")
                        with col_l2:
                             lick_tags_select = st.multiselect("Tags", options=get_all_tags())
                             lick_new_tag_in = st.text_input("New Tag")
                        
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                             lick_start_in = st.number_input("Start", min_value=0.0, step=0.1, format="%.2f")
                        with col_t2:
                             lick_end_in = st.number_input("End", min_value=0.0, step=0.1, format="%.2f")

                        if st.form_submit_button("Save to Library"):
                            if lick_title_in and (lick_end_in > lick_start_in):
                                f_tags = set(lick_tags_select)
                                if lick_new_tag_in:
                                    f_tags.add(lick_new_tag_in)
                                    save_global_tags(list(f_tags))
                                licks_manager.save_lick(st.session_state.selected_lesson, lick_title_in, list(f_tags), lick_start_in, lick_end_in)
                                st.success("Saved!")
                            else:
                                st.error("Invalid input.")

                st.divider()
                st.caption("Downloads")
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    if vocals_path.exists():
                        with open(vocals_path, "rb") as f:
                             st.download_button("Vocals (MP3)", f, file_name="vocals.mp3")
                with col_d2:
                    if guitar_path.exists():
                        with open(guitar_path, "rb") as f:
                             st.download_button("Guitar (MP3)", f, file_name="guitar.mp3")
                with col_d3:
                    if original_path.exists():
                        with open(original_path, "rb") as f:
                             st.download_button("Original (MP3)", f, file_name="original.mp3")

                # Transcript
                st.subheader("📜 Full Transcript")
                transcript_file = lesson_path / "transcript.txt"
                if transcript_file.exists():
                     with st.expander("Show Transcript", expanded=False):
                         with open(transcript_file, "r") as f:
                             st.text(f.read())

# --- Mode: Lick Library ---
# --- Mode: Lick Library ---
elif mode == "Lick Library 🎸":
    
    if "current_lick" in st.session_state and st.session_state.current_lick:
        # --- LICK PLAYER DETAIL VIEW ---
        lick = st.session_state.current_lick
        lesson_dir = lick['lesson_dir']
        lesson_path = data_dir / lesson_dir
        
        st.title(f"🎸 {lick['title']}")
        if st.button("← Back to Lick Library"):
            del st.session_state["current_lick"]
            st.rerun()
            
        # Load Audio
        vocals_path = lesson_path / "vocals.mp3"
        guitar_path = lesson_path / "guitar.mp3"
        
        vocals_b64 = get_audio_base64(vocals_path) if vocals_path.exists() else None
        guitar_b64 = get_audio_base64(guitar_path) if guitar_path.exists() else None
        
        auto_loop_start = lick['start']
        auto_loop_end = lick['end']
        
        # Player HTML (Copied from Review Mode)
        player_html = f"""
            <html>
            <head>
            <script src="https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.min.js"></script>
            <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>
            <style>
                body {{ font-family: sans-serif; color: #333; margin: 0; padding: 10px; background: #f9f9f9; overflow: hidden; }}
                /* Controls */
                .controls-area {{ 
                    background: #333; 
                    padding: 10px; 
                    border-radius: 8px; 
                    color: white;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 10px;
                    flex-wrap: wrap;
                }}
                .play-btn {{
                    background: #ff4b4b; color: white; border: none; width: 40px; height: 40px;
                    border-radius: 50%; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center;
                }}
                .play-btn:hover {{ background: #ff3333; }}
                .slider-group {{ display: flex; flex-direction: column; gap: 2px; min-width: 120px; }}
                .slider-group label {{ font-size: 11px; color: #ccc; }}
                input[type=range] {{ width: 100%; cursor: pointer; }}
                
                .waveform-box {{
                    margin-bottom: 10px; background: white; padding: 5px; border-radius: 6px; position: relative;
                    height: 80px;
                }}
                .waveform-label {{
                    position: absolute; top: 2px; left: 5px; font-size: 10px; font-weight: bold;
                    padding: 1px 4px; border-radius: 3px; background: rgba(255,255,255,0.8); pointer-events: none; z-index: 10;
                }}
                 #regionInfo {{
                    color: #ccc; font-size: 12px; font-weight: bold; margin-left: 15px; border-left: 1px solid #555; padding-left: 15px;
                }}
            </style>
            </head>
            <body>
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
                    <div class="slider-group" style="min-width: 100px;">
                            <div style="display: flex; gap: 8px; align-items: center;">
                            <label style="color: white; font-size: 10px;"><input type="checkbox" id="muteV" checked> Vocals</label>
                            <label style="color: white; font-size: 10px;"><input type="checkbox" id="muteG" checked> Guitar</label>
                        </div>
                    </div>
                    <div id="timeDisplay" style="font-family: monospace; font-size: 12px; margin-left: auto;">00:00 / 00:00</div>
                    <div id="regionInfo">Selection: --</div>
                </div>

                <div class="waveform-box">
                    <div class="waveform-label">🗣️ Vocals</div>
                    <div id="waveform-v"></div>
                </div>
                <div class="waveform-box">
                    <div class="waveform-label">🎸 Guitar</div>
                    <div id="waveform-g"></div>
                </div>

                <script>
                    const vocalsData = "data:audio/mp3;base64,{vocals_b64}";
                    const guitarData = "data:audio/mp3;base64,{guitar_b64}";
                    const autoStart = {auto_loop_start};
                    const autoEnd = {auto_loop_end};

                    // Broadcast Channel Receiver
                    const bc = new BroadcastChannel('refret_sync');

                    // Elements
                    const playBtn = document.getElementById('playBtn');
                    const speedSlider = document.getElementById('speedSlider');
                    const speedVal = document.getElementById('speedVal');
                    const zoomSlider = document.getElementById('zoomSlider');
                    const muteV = document.getElementById('muteV');
                    const muteG = document.getElementById('muteG');
                    const timeDisplay = document.getElementById('timeDisplay');
                    const regionInfo = document.getElementById('regionInfo');

                    let wsV = WaveSurfer.create({{
                        container: '#waveform-v', waveColor: '#A855F7', progressColor: '#7E22CE', cursorColor: '#7E22CE',
                        barWidth: 2, barGap: 1, barRadius: 2, height: 70, normalize: true, minPxPerSec: 20
                    }});
                    let wsG = WaveSurfer.create({{
                        container: '#waveform-g', waveColor: '#F97316', progressColor: '#C2410C', cursorColor: '#C2410C',
                        barWidth: 2, barGap: 1, barRadius: 2, height: 70, normalize: true, minPxPerSec: 20,
                        plugins: [ WaveSurfer.Regions.create() ]
                    }});

                    wsV.load(vocalsData);
                    wsG.load(guitarData);

                    let isReadyV = false;
                    let isReadyG = false;

                    // Unified Play/Pause
                    const togglePlay = () => {{
                        if(wsV.isPlaying()) {{ wsV.pause(); wsG.pause(); playBtn.textContent = "▶"; }}
                        else {{ wsV.play(); wsG.play(); playBtn.textContent = "⏸"; }}
                    }};
                    playBtn.onclick = togglePlay;

                    // Ready Handler
                    const checkReady = () => {{
                        if(isReadyV && isReadyG) {{
                            if(autoStart !== null && autoEnd !== null) {{
                                const wsGRegions = wsG.plugins[0];
                                wsGRegions.addRegion({{ start: autoStart, end: autoEnd, color: "rgba(255, 0, 0, 0.3)" }});
                                wsV.setTime(autoStart); wsG.setTime(autoStart);
                            }}
                        }}
                    }};

                    wsV.on('ready', () => {{ isReadyV = true; checkReady(); }});
                    wsG.on('ready', () => {{ isReadyG = true; checkReady(); }});
                    
                    // Sync
                    wsV.on('seek', (p) => {{ wsG.seekTo(p); }});
                    wsG.on('seek', (p) => {{ wsV.seekTo(p); }});
                    wsV.on('finish', () => {{ playBtn.textContent = "▶"; }});

                    // Controls
                    speedSlider.oninput = () => {{
                        const rate = parseFloat(speedSlider.value);
                        wsV.setPlaybackRate(rate); wsG.setPlaybackRate(rate);
                        speedVal.textContent = rate.toFixed(1);
                    }};
                    zoomSlider.oninput = () => {{
                        const z = parseInt(zoomSlider.value);
                        wsV.zoom(z); wsG.zoom(z);
                    }};
                    muteV.onchange = () => {{ wsV.setMuted(!muteV.checked); }};
                    muteG.onchange = () => {{ wsG.setMuted(!muteG.checked); }};

                    // Time Display
                    wsV.on('timeupdate', () => {{
                        const cur = wsV.getCurrentTime();
                        const tot = wsV.getDuration() || 0;
                        const fmt = (s) => {{
                            const m = Math.floor(s/60); const sec = Math.floor(s%60);
                            return `${{m.toString().padStart(2,'0')}}:${{sec.toString().padStart(2,'0')}}`;
                        }};
                        timeDisplay.textContent = `${{fmt(cur)}} / ${{fmt(tot)}}`;
                    }});

                    // Region Info
                    const wsGRegions = wsG.plugins[0];
                    
                    // Enable Drag Selection
                    wsGRegions.enableDragSelection({{
                        color: 'rgba(255, 0, 0, 0.3)',
                    }});

                    const updateInfo = (region) => {{
                        regionInfo.innerText = `Selection: ${{region.start.toFixed(2)}}s - ${{region.end.toFixed(2)}}s`;
                    }};
                    
                    wsGRegions.on('region-created', (region) => {{
                        // Enforce Single Region: Clear others
                        wsGRegions.getRegions().forEach(r => {{
                            if (r !== region) r.remove();
                        }});
                        updateInfo(region);
                    }});
                    
                    wsGRegions.on('region-updated', (region) => {{
                        updateInfo(region);
                    }});
                    
                    // Manual Loop Sync
                    wsGRegions.on('region-out', (region) => {{
                        wsV.setTime(region.start);
                        wsG.setTime(region.start);
                        wsV.play();
                        wsG.play();
                    }});
                    
                    wsGRegions.on('region-clicked', (region, e) => {{
                        e.stopPropagation();
                        wsV.setTime(region.start);
                        wsG.setTime(region.start);
                        wsV.play();
                        wsG.play();
                        playBtn.textContent = "⏸";
                        updateInfo(region);
                    }});
                </script>
            </body>
            </html>
        """
        
        # 1. Sticky Player Header
        st.markdown(
            """
            <style>
                iframe[title="streamlit.components.v1.html"]:nth-of-type(1) {
                    position: sticky;
                    top: 0;
                    z-index: 100;
                    background: #f0f2f6; 
                    border-bottom: 2px solid #ddd;
                }
            </style>
            """, unsafe_allow_html=True
        )
        
        components.html(player_html, height=340, scrolling=False)
        
        # 2. Scrollable Content
        with st.container(height=600):
            st.subheader("📝 Lick Memo")
            
            with st.form("lick_edit_form"):
                 # Memo
                 new_memo = st.text_area("Memo (Markdown supported)", value=lick.get("memo", ""), height=200)
                 
                 # Tags
                 current_tags = lick.get("tags", [])
                 all_tags = get_all_tags()
                 # Allow new tags? Simply multiselect for now for compactness
                 updated_tags = st.multiselect("Tags", all_tags, default=current_tags)
                 
                 if st.form_submit_button("Save Lick Details"):
                     updates = {"memo": new_memo, "tags": updated_tags}
                     licks_manager.update_lick(lick['id'], updates)
                     lick.update(updates) # Session update
                     st.session_state.current_lick = lick
                     st.success("Changes saved!")
            
            st.divider()
            
            st.info(f"Source: {lick['lesson_dir']} ({lick['start']}s - {lick['end']}s)")
            def go_full_review():
                 st.session_state.selected_lesson = lick['lesson_dir']
                 st.session_state["nav_mode"] = "Library (Review)"
                 del st.session_state["current_lick"]

            st.button("Go to Full Lesson Review", on_click=go_full_review)

    else:
        st.title("🎸 Lick Library")
        
        all_licks = licks_manager.load_licks()
        
        # Filter
        all_tags = sorted(list(set([t for lick in all_licks for t in lick.get("tags", [])])))
        selected_tags = st.multiselect("Filter by Tags", options=all_tags)
        
        if selected_tags:
            filtered_licks = [l for l in all_licks if any(t in selected_tags for t in l.get("tags", []))]
        else:
            filtered_licks = all_licks
        
        st.write(f"Showing {len(filtered_licks)} licks")
        
        if not filtered_licks:
            st.info("No licks saved yet. Go to the Player view and save loops as licks!")
        
        # Display Grid
        for lick in filtered_licks:
            with st.container(border=True):
                cols = st.columns([0.1, 0.7, 0.2])
                
                # Play Button
                with cols[0]:
                    st.button("▶", key=f"play_lick_{lick['id']}", help="Play Lick", on_click=play_lick, args=(lick,))
                
                # Info
                with cols[1]:
                    st.markdown(f"**{lick['title']}**")
                    st.caption(f"Lesson: {lick['lesson_dir']} | ⏱ {lick['start']}s - {lick['end']}s")
                    # Tags badge style
                    tags_html = " ".join([f"<span style='background:#eee;padding:2px 6px;border-radius:4px;font-size:12px'>{t}</span>" for t in lick['tags']])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                # Delete Button
                with cols[2]:
                    if st.button("🗑️", key=f"del_lick_{lick['id']}", help="Delete Lick"):
                        licks_manager.delete_lick(lick['id'])
                        st.rerun()

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
