import streamlit as st
import os
import json
from pathlib import Path
from processor import AudioProcessor

# Page Config
st.set_page_config(page_title="Guitar Lesson Review", page_icon="🎸", layout="wide")

# Initialize Processor
# Using cache_resource to keep the model loaded, but added ttl to ensure updates propagate during dev
@st.cache_resource(ttl="1h") 
def get_processor():
    return AudioProcessor()

processor = get_processor()

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
mode = st.sidebar.radio("Navigation", ["New Lesson (Upload)", "Library (Review)"])

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
                
                # Load Summary
                summary_file = lesson_path / "summary.json"
                summary_content = None
                if summary_file.exists():
                    with open(summary_file, "r") as f:
                        try:
                            summary_content = json.load(f)
                        except json.JSONDecodeError:
                            st.error("Error reading summary file.")

                # Layout
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("🎧 Audio Tracks")
                    
                    vocals_path = lesson_path / "vocals.wav"
                    guitar_path = lesson_path / "guitar.wav"
                    original_path = lesson_path / "original.wav"

                    if original_path.exists():
                        st.caption("Original Mix")
                        st.audio(str(original_path))
                    
                    st.divider()
                    
                    if vocals_path.exists():
                        st.write("**🗣️ Vocals Only**")
                        st.audio(str(vocals_path))
                    else:
                        st.warning("Vocals track not found.")
                        
                    if guitar_path.exists():
                        st.write("**🎸 Guitar Only**")
                        st.audio(str(guitar_path))
                    else:
                        st.warning("Guitar track not found.")

                with col2:
                    st.subheader("📝 Summary & Notes")
                    if summary_content:
                        # Display Summary nicely
                        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
                        st.markdown(f"### Key Takeaways")
                        if "summary" in summary_content:
                            st.write(summary_content["summary"])
                        
                        if "key_points" in summary_content and isinstance(summary_content["key_points"], list):
                            st.markdown("**Points:**")
                            for point in summary_content["key_points"]:
                                st.markdown(f"- {point}")
                        
                        if "chords" in summary_content and isinstance(summary_content["chords"], list):
                            st.markdown("**Chords Mentioned:**")
                            st.code(", ".join(summary_content["chords"]))
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Raw JSON Viewer
                        with st.expander("View Raw Summary JSON"):
                            st.json(summary_content)
                    else:
                        st.info("No summary available for this lesson.")

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
