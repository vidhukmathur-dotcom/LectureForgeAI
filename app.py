import streamlit as st
import os
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

3. **📂 Upload Your Lecture Deck (as PDF)**
   * Export your presentation to PDF first — in PowerPoint: File → Export → Create PDF/XPS. In Google Slides: File → Download → PDF Document. Both are one-click.
   * Drag and drop the resulting `.pdf` file into the upload area below.

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

# INSTITUTIONAL BRANDING FOOTER
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #1a2f5e 0%, #1e3a6e 100%);
        border-left: 4px solid #f0a500;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 8px;
    ">
        <div style="
            color: #f0a500;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 8px;
        ">Developed by</div>
        <div style="
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            line-height: 1.4;
            margin-bottom: 4px;
        ">Vidhu K. Mathur</div>
        <div style="
            color: #c8d8f0;
            font-size: 11px;
            line-height: 1.5;
            margin-bottom: 10px;
        ">
            <span style="color: #f0a500; font-weight: 600;">IBS</span> — The ICFAI University, Jaipur
        </div>
        <div style="
            border-top: 1px solid rgba(240,165,0,0.3);
            padding-top: 8px;
            margin-top: 4px;
        ">
            <a href="mailto:vidhuk.mathur@iujaipur.edu.in" style="
                color: #a8c4e8;
                font-size: 11px;
                text-decoration: none;
            ">📧 vidhuk.mathur@iujaipur.edu.in</a>
        </div>
        <div style="
            color: rgba(200,216,240,0.5);
            font-size: 10px;
            margin-top: 8px;
            text-align: right;
        ">LectureForge AI v1.0</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 2. FILE UPLOADER PORTAL
uploaded_file = st.file_uploader("📂 Drop your lecture presentation here (.pdf)", type=["pdf"])
st.caption(
    "💡 Export your deck to PDF first (File → Export/Save As PDF in PowerPoint or Google Slides — "
    "a one-click action) then upload the PDF here. This keeps rendering fast and reliable on the server."
)

if uploaded_file is not None:
    # Guard 1: File size sanity check, before any disk writes or processing.
    # A standard slide-deck PDF (15-30 slides) is typically well under 20MB.
    # Anything dramatically larger usually signals something unintended --
    # embedded video, uncompressed high-res images, or simply the wrong
    # file -- and would strain both processing time and Streamlit Cloud's
    # memory ceiling. This blocks outright rather than just warning, since
    # there's no reasonable "proceed anyway" case for a deck this size.
    #
    # NOTE: this value should match maxUploadSize in .streamlit/config.toml,
    # which controls what Streamlit's file_uploader widget itself displays
    # and enforces ("Limit XXMB per file"). This check here is a second
    # layer of defense in case that config isn't present (e.g. running
    # locally without the .streamlit folder) -- keep both numbers in sync.
    MAX_UPLOAD_SIZE_MB = 30
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        st.error(
            f"⚠️ This file is {file_size_mb:.1f}MB, which is larger than the "
            f"{MAX_UPLOAD_SIZE_MB}MB limit for this tool. A typical 15-30 slide "
            f"deck PDF should be well under this. If your file is genuinely this "
            f"large, it may contain embedded video or very high-resolution images "
            f"-- try re-exporting with image compression enabled."
        )
        st.stop()

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

    # Guard 2 + presentation-shape check, combined: this app is built and
    # tested for 15-30 slide decks. A much larger PDF means dramatically
    # more Groq calls, TTS calls, and image renders than tested -- a real
    # risk for both cost and Streamlit Cloud's memory ceiling. This warns
    # rather than hard-blocks, since a 35-40 slide deck will likely still
    # work, just slower; only an extreme outlier gets a stronger caution.
    MAX_RECOMMENDED_SLIDES = 40
    try:
        validation_result = ppt_processor.validate_is_presentation(temp_ppt_path)
        total_pages_detected = validation_result["total_pages"]

        if total_pages_detected > MAX_RECOMMENDED_SLIDES:
            st.warning(
                f"⚠️ This PDF has {total_pages_detected} pages. This tool is built "
                f"and tested for decks of roughly 15-30 slides. A deck this large "
                f"will take significantly longer to process and may be more likely "
                f"to hit server resource limits. You can still proceed, but consider "
                f"splitting very long decks into smaller sections if you run into issues."
            )

        if not validation_result["is_likely_presentation"]:
            st.warning(
                "⚠️ This PDF doesn't look like an exported slide presentation "
                "(its page proportions don't match standard 16:9 / 4:3 / 16:10 "
                "slide dimensions). It may be a regular document instead. "
                "You can still proceed, but slide images and narration may "
                "not turn out well — dense paragraph text doesn't render or "
                "narrate cleanly as a 'slide'. For best results, upload a PDF "
                "exported directly from PowerPoint or Google Slides."
            )
    except Exception:
        # Don't let a validation hiccup block the user from proceeding --
        # this check is purely advisory.
        pass

    # Override engine credentials using the browser side input text value dynamically
    if api_key_input:
        ai_engine.api_key = api_key_input

    # Guard 3: prevent overlapping runs from a double-click or impatient
    # re-click while a previous run is still processing. Without this, two
    # concurrent runs could write to the same web_workspace folders at once,
    # reintroducing the exact slide/audio mixing bug fixed earlier.
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

    process_clicked = st.button(
        "🚀 Process Presentation Deck",
        type="primary",
        disabled=st.session_state.is_processing,
    )

    if st.session_state.is_processing:
        st.info("⏳ A video is already being processed. Please wait for it to finish before starting another.")

    if process_clicked:
        # --- FIXED: Variable name now matches api_key_input perfectly ---
        if not api_key_input:
            st.error("⚠️ Please supply a valid Groq API key in the sidebar configuration to execute.")
        else:
            st.session_state.is_processing = True

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
                # Phase 1: Text extraction
                status_container.info("⚙️ Step 1/5: Extracting presentation text outline layers...")
                progress_bar.progress(10)
                extracted_text = ppt_processor.extract_text(temp_ppt_path)

                # Phase 2: Slide image rendering
                status_container.info("⚙️ Step 2/5: Rendering visual slide frames into high-res sheets...")
                progress_bar.progress(30)
                total_slides = ppt_processor.export_slide_images(temp_ppt_path, img_dir)

                # Phase 3: AI narration generation
                # Uses openai/gpt-oss-120b for text slides (full deck context
                # preserved in one call), and meta-llama/llama-4-scout for
                # image-only slides that have no extractable text.
                status_container.info("⚙️ Step 3/5: Generating lecture narration script via Groq AI...")
                progress_bar.progress(50)

                slide_scripts = ai_engine.generate_lecture_narration(
                    extracted_text,
                    total_slides,
                    image_dir=img_dir,
                )

                # Final safety net: replace any empty narration strings before
                # they reach edge-tts (empty text to TTS causes audio failures).
                for idx in range(len(slide_scripts)):
                    if not slide_scripts[idx] or not slide_scripts[idx].strip():
                        slide_scripts[idx] = (
                            "This slide presents a visual element. "
                            "Let's take a moment to look at it before moving forward."
                        )

                # Build human-readable combined script for Word backup and UI preview
                ai_script = "\n\n".join(
                    f"--- Slide {idx} ---\n{text}"
                    for idx, text in enumerate(slide_scripts, start=1)
                )
                doc_generator.save_narration_to_word(ai_script, temp_ppt_path)

                # Phase 4: TTS audio generation
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
                st.session_state.is_processing = False

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
                                file_name=f"LectureForge_{uploaded_file.name.replace('.pdf', '')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                with col2:
                    st.markdown("### 📝 Grounded Narrative Script Details")
                    st.text_area("Live Generated Speech Output:", value=ai_script, height=420)

            except Exception as e:
                progress_bar.empty()
                status_container.error(f"❌ Processing engine thread aborted: {str(e)}")
                st.session_state.is_processing = False
