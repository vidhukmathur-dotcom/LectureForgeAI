import streamlit as st
import os
import re
import shutil
from src.core.ppt_processor import PowerPointProcessor
from src.core.ai_engine import AIEngine
from src.core.doc_generator import DocumentGenerator
from src.core.audio_generator import AudioGenerator
from src.core.video_generator import VideoGenerator

# Set up clean modern web browser layout structure
st.set_page_config(page_title="LectureForge AI — Studio", page_icon="🎬", layout="wide")

st.title("🎬 LectureForge AI")
st.subheader("Academic Presentation Studio for Higher Education")
st.markdown("---")

# INTERACTIVE HOW-TO GUIDE FOR NEW USERS
with st.expander("📖 New User Guide: How to compile your first lecture video", expanded=False):
    st.markdown("""
### 🚀 Getting Started in 4 Simple Steps

1. **🔑 Secure Your Free Access Key**
   * Click the link in the sidebar to visit the **Groq Cloud Console**.
   * Log in with your email, create a new API key, and copy it.
   * Paste it into the **Groq API Key** box in the sidebar. *(Your key stays completely private to your session).*

2. **🎙️ Choose an Academic Voice**
   * Select your preferred instructional tone and accent from the **Voice Accent Profile** dropdown menu (e.g., *Male — US Academic* or *Female — Indian Classroom*).

3. **📂 Upload Your PowerPoint Deck**
   * Drag and drop your lecture presentation file (`.pptx`) into the upload area below.

4. **⚙️ Process & Download**
   * Click **Process Presentation Deck**. The AI engine will extract your slides, write a natural conversational script, record the narration, and combine everything into a high-definition video.
   * Once finished, review your script details on the right, preview the video on the left, and click **Download Lecture Video** to save it to your machine!

---
💡 *Note: The AI is programmed to synthesize and explain your slide content naturally as an instructor would, staying completely anchored to your presentation facts without just reading the text word-for-word.*
""")

# 1. SIDEBAR CONFIGURATION (SECURE KEY SHIELD & PREMIUM VOICES)
st.sidebar.header("⚙️ Studio Settings")

# MASKED KEY INPUT: type="password" hides characters securely behind placeholder dots
api_key_input = st.sidebar.text_input(
    "Groq API Key:",
    type="password",
    value=os.environ.get("GROQ_API_KEY", ""),
    help="Your token is session-isolated and completely private to your browser view layout."
)

# QUICK ONBOARDING LINK FOR COLLEAGUES
st.sidebar.markdown("[🔑 Get a free Groq API Key instantly here](https://console.groq.com/)")
st.sidebar.markdown("---")

# Premium Microsoft Neural Voices Mapping
voice_map = {
    "Male — US Academic (Brian)": "en-US-BrianNeural",
    "Female — US Studio (Emma)": "en-US-EmmaNeural",
    "Male — UK Professor (Ryan)": "en-GB-RyanNeural",
    "Female — UK Narrative (Sonia)": "en-GB-SoniaNeural",
    "Male — Indian Classroom (Neerja)": "en-IN-NeerjaNeural"
}
selected_voice_label = st.sidebar.selectbox("Premium Voice Accent Profile:", list(voice_map.keys()))
selected_voice = voice_map[selected_voice_label]

# 2. FILE UPLOADER PORTAL
uploaded_file = st.file_uploader("📂 Drop your lecture PowerPoint presentation here (.pptx)", type=["pptx"])

if uploaded_file is not None:
    # Set up clean internal directory frameworks for web media assets
    workspace_dir = os.path.join(os.getcwd(), "web_workspace")
    img_dir = os.path.join(workspace_dir, "images")
    audio_dir = os.path.join(workspace_dir, "audio")

    # Overwrite paths in place safely to avoid Windows lock restrictions
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    # Stream file buffer out to disk storage paths safely
    temp_ppt_path = os.path.join(workspace_dir, uploaded_file.name)
    with open(temp_ppt_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Initialize modular execution core components
    ppt_processor = PowerPointProcessor()
    ai_engine = AIEngine()
    doc_generator = DocumentGenerator()
    audio_generator = AudioGenerator()
    video_generator = VideoGenerator()

    # Override engine credentials using the browser side input text value dynamically
    if api_key_input:
        ai_engine.api_key = api_key_input

    if st.button("🚀 Process Presentation Deck", type="primary"):
        # --- FIXED: Variable name now matches api_key_input perfectly ---
        if not api_key_input:
            st.error("⚠️ Please supply a valid Groq API key in the sidebar configuration to execute.")
        else:
            # Setup clean structural loader hooks
            status_container = st.empty()
            progress_bar = st.progress(0)

            # Wipe any leftover slide images / audio from a previous run.
            # Without this, leftover slide_N.png / slide_N.mp3 files from an
            # earlier (and possibly longer) presentation can stick around
            # and get pulled into THIS video, since video_generator simply
            # globs every file sitting in these folders.
            for stale_dir in (img_dir, audio_dir):
                shutil.rmtree(stale_dir, ignore_errors=True)
                os.makedirs(stale_dir, exist_ok=True)

            try:
                # Phase 1: PowerPoint Text Parsing Extraction
                status_container.info("⚙️ Step 1/5: Extracting presentation text outline layers...")
                progress_bar.progress(10)
                extracted_text = ppt_processor.extract_text(temp_ppt_path)

                # Phase 2: Frame Canvas Image Export Pass
                status_container.info("⚙️ Step 2/5: Rendering visual slide frames into high-res sheets...")
                progress_bar.progress(30)
                total_slides = ppt_processor.export_slide_images(temp_ppt_path, img_dir)

                # Phase 3: Llama 3.3 Prompting via Groq Ecosystem
                status_container.info("⚙️ Step 3/5: Consulting Groq Llama 3.3 to structure balanced lecture narration script...")
                progress_bar.progress(50)
                ai_script = ai_engine.generate_lecture_narration(extracted_text)

                # Dynamic slide boundary regex script parser layout splitting
                raw_chunks = re.split(r'(?i)(?:---|\*\*)*\s*slide\s*\d+\s*(?:---|\*\*|:)*', ai_script)
                first_marker_match = re.search(r'(?i)(?:---|\*\*)*\s*slide\s*1\s*(?:---|\*\*|:)*', ai_script)

                if first_marker_match and raw_chunks:
                    intro_text = ai_script[:first_marker_match.start()].strip()
                    remaining_chunks = raw_chunks[1:]
                    if remaining_chunks:
                        if intro_text:
                            remaining_chunks[0] = f"{intro_text}\n\n{remaining_chunks[0]}"
                        valid_chunks = [chunk.strip() for chunk in remaining_chunks]
                    else:
                        valid_chunks = []
                else:
                    valid_chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]

                slide_scripts = []
                for idx in range(1, total_slides + 1):
                    if (idx - 1) < len(valid_chunks) and valid_chunks[idx - 1]:
                        slide_scripts.append(valid_chunks[idx - 1])
                    else:
                        slide_scripts.append(f"Moving forward to slide {idx}.")

                # Save out raw narration text outline over to Microsoft Word framework files
                doc_generator.save_narration_to_word(ai_script, temp_ppt_path)

                # Phase 4: Edge Premium Neural Audio Audio Processing Track
                status_container.info("⚙️ Step 4/5: Synthesizing premium neural text-to-speech audio layers...")
                progress_bar.progress(75)
                audio_generator.generate_all_slide_audio(
                    slide_scripts=slide_scripts,
                    audio_dir=audio_dir,
                    voice_profile=selected_voice,
                )

                # Phase 5: Final Video Compilation Layout Assembly
                status_container.info("⚙️ Step 5/5: Compiling timeline arrays and formatting final lecture video...")
                progress_bar.progress(90)
                output_video_path = video_generator.compile_lecture_video(
                    image_dir=img_dir,
                    audio_dir=audio_dir,
                    slide_scripts=slide_scripts,
                    total_slides=total_slides,
                    original_ppt_path=temp_ppt_path,
                    logger_callback=None
                )

                # Master UI state display completion update pass
                progress_bar.progress(100)
                status_container.success("🎯 Academic Lecture Audio & Video Compiled Successfully!")

                # Render Clean Browser View Split Panel Display Output Previews
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown("### 🎬 Completed Lecture Video Output")
                    if os.path.exists(output_video_path):
                        # Video Player
                        with open(output_video_path, "rb") as video_file:
                            st.video(video_file)
                        # Click-to-Download Portal Button
                        with open(output_video_path, "rb") as video_file:
                            st.download_button(
                                label="📥 Download Lecture Video (.mp4)",
                                data=video_file,
                                file_name=f"LectureForge_{uploaded_file.name.replace('.pptx', '')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                with col2:
                    st.markdown("### 📝 Grounded Narrative Script Details")
                    st.text_area("Live Generated Speech Output:", value=ai_script, height=420)

            except Exception as e:
                progress_bar.empty()
                status_container.error(f"❌ Processing engine thread aborted: {str(e)}")
