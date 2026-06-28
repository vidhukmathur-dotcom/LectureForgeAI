import os
from tkinter import filedialog
import threading
import time
import re
from pygame import mixer
from src.core.ppt_processor import PowerPointProcessor
from src.core.ai_engine import AIEngine
from src.core.doc_generator import DocumentGenerator
from src.core.audio_generator import AudioGenerator
from src.core.video_generator import VideoGenerator
from proglog import ProgressBarLogger

class VideoExportLogger(ProgressBarLogger):
    """Feeds real-time video frame encoding metrics and velocity calculations down to the UI."""
    def __init__(self, controller_instance):
        super().__init__()
        self.controller = controller_instance
        self.start_time = None

    def callback(self, **changes):
        if self.controller.cancel_event.is_set():
            raise KeyboardInterrupt("User aborted the encoding pipeline.")

        if "t" in self.state and "index" in self.state["t"]:
            current_frame = self.state["t"]["index"]
            total_frames = self.state["t"].get("total", 0)
            
            if total_frames > 0:
                if self.start_time is None:
                    self.start_time = time.time()
                
                elapsed = time.time() - self.start_time
                percentage = int((current_frame / total_frames) * 100)
                
                if current_frame > 0:
                    eta_seconds = int((elapsed / current_frame) * (total_frames - current_frame))
                    eta_str = f"{eta_seconds // 60:02d}:{eta_seconds % 60:02d} left"
                else:
                    eta_str = "--:-- left"
                
                status_text = f"Packaging video timelines ({current_frame}/{total_frames})"
                time_metrics = f"Elapsed: {int(elapsed)//60:02d}:{int(elapsed)%60:02d} | {eta_str}"
                
                self.controller.ui.update_status(status_text, percentage, time_metrics)

class MainController:
    """The Controller: Acts as the core orchestration center, managing background threads,
    AI pipelines, file generation tasks, and responsive interface communication handles.
    """
    def __init__(self):
        self.ui = None 
        self.ppt_processor = PowerPointProcessor()
        self.ai_engine = AIEngine()
        self.doc_generator = DocumentGenerator()
        self.audio_generator = AudioGenerator()
        self.video_generator = VideoGenerator() 
        
        mixer.init()
        self.audio_dir = ""
        self.image_dir = ""
        self.current_ppt_path = "" 
        self.total_slides = 0
        self.current_slide = 1
        
        self.is_running = True
        self.slide_scripts = []
        self.cancel_event = threading.Event()

    def set_ui(self, ui):
        self.ui = ui

    def get_selected_voice_accent(self):
        return self.ui.get_selected_voice_accent()

    def handle_select_file(self):
        filename = filedialog.askopenfilename(
            title="Select a PowerPoint",
            filetypes=[("PowerPoint Files", "*.pptx")]
        )
        if filename:
            self.current_ppt_path = filename
            self.current_slide = 1
            self.slide_scripts = []
            self.cancel_event.clear()
            self.ui.enable_kill_button()
            
            worker_thread = threading.Thread(target=self._process_presentation_worker, args=(filename,))
            worker_thread.start()

    def handle_kill_process(self):
        self.cancel_event.set()
        mixer.music.stop()
        self.ui.update_status("Operation cancelled by user.", 0, "Aborted")
        self.ui.display_content("Process stopped cleanly. Ready to accept a new presentation outline.")
        self.ui.disable_kill_button()

    def _process_presentation_worker(self, filename: str):
        start_process = time.time()
        try:
            if self.cancel_event.is_set(): return
            
            self.ui.update_status("Extracting presentation layout outlines...", 10, "Phase 1/5")
            extracted_text = self.ppt_processor.extract_text(filename)
            
            if self.cancel_event.is_set(): return self.handle_kill_process()
            
            self.ui.update_status("Exporting high-resolution visual slide sheets...", 30, "Phase 2/5")
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.image_dir = os.path.join(project_root, "assets", "images")
            self.total_slides = self.ppt_processor.export_slide_images(filename, self.image_dir)
            
            if self.cancel_event.is_set(): return self.handle_kill_process()
            
            # --- FIXED: UI CHAT LABEL NOW MATCHES THE FREE GROQ CLOUD HOSTS ---
            self.ui.update_status("Consulting Groq Llama 3.3 to build lecture script...", 50, "Phase 3/5")
            ai_script = self.ai_engine.generate_lecture_narration(extracted_text)
            # -------------------------------------------------------------------
            
            if self.cancel_event.is_set(): return self.handle_kill_process()
            
            self.ui.update_status("Compiling narrative framework to Microsoft Word...", 70, "Phase 4/5")
            word_path = self.doc_generator.save_narration_to_word(ai_script, filename)
            
            if self.cancel_event.is_set(): return self.handle_kill_process()
            
            self.ui.update_status("Initializing text-to-speech synchronization...", 85, "Phase 5/5")
            self.audio_dir = os.path.join(project_root, "assets", "audio")
            
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
                valid_chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]

            self.slide_scripts = []
            for idx in range(1, self.total_slides + 1):
                if (idx - 1) < len(valid_chunks) and valid_chunks[idx - 1]:
                    self.slide_scripts.append(valid_chunks[idx - 1])
                else:
                    self.slide_scripts.append(f"Moving to slide {idx}.")
            
            selected_accent = self.get_selected_voice_accent()
            
            for idx in range(1, self.total_slides + 1):
                if self.cancel_event.is_set(): return self.handle_kill_process()
                
                audio_progress = 85 + int((idx / self.total_slides) * 14)
                self.ui.update_status(f"Generating audio track slice {idx}/{self.total_slides}...", audio_progress, f"{idx}/{self.total_slides}")
                
                audio_output_path = os.path.join(self.audio_dir, f"slide_{idx}.mp3")
                script_text = self.slide_scripts[idx - 1]
                
                success = self.audio_generator.generate_slide_audio(script_text, audio_output_path, voice_profile=selected_accent)
                if not success:
                    raise RuntimeError(f"Audio Engine failed on Slide {idx}. No streaming voice bytes received.")
            
            if self.is_running and not self.cancel_event.is_set():
                elapsed = int(time.time() - start_process)
                self.ui.update_status("Synchronization complete. Ready to review or export.", 100, f"Done ({elapsed}s)")
                
                first_slide_img = os.path.join(self.image_dir, "Slide1.PNG")
                if not os.path.exists(first_slide_img):
                    first_slide_img = os.path.join(self.image_dir, "slide1.PNG")
                
                self.ui.project_slide_image(first_slide_img)
                self.ui.enable_play_button()
                self.ui.disable_kill_button()
                self.ui.display_content(
                    f"Lecture Built Successfully!\n\n"
                    f"Slides Processed: {self.total_slides}\n"
                    f"Audio Duration Tracks Synced: {len(self.slide_scripts)}\n\n"
                    "Select an action from the menu system or ribbon toolbar above to proceed."
                )
            
        except Exception as e:
            if self.is_running and not self.cancel_event.is_set():
                error_msg = str(e)
                print(f"🚨 Pipeline Exception Caught: {error_msg}")
                self.ui.update_status(f"Error: {error_msg}", 0, "Pipeline Failed")
                self.ui.display_content(
                    f"❌ PIPELINE ERROR OCCURRED\n\n"
                    "The background processing thread was aborted due to the following system failure:\n\n"
                    f"⚠️ {error_msg}\n\n"
                    "Please check your Groq API key setup, internet connection, or parameters and try again."
                )
                self.ui.disable_kill_button()

    def handle_export_video(self):
        self.cancel_event.clear()
        self.ui.enable_kill_button()
        self.ui.update_status("Initializing video encoder timeline...", 0, "Starting")
        video_thread = threading.Thread(target=self._export_video_worker)
        video_thread.start()

    def _export_video_worker(self):
        try:
            custom_logger = VideoExportLogger(self)
            output_path = self.video_generator.compile_lecture_video(
                image_dir=self.image_dir,
                audio_dir=self.audio_dir,
                slide_scripts=self.slide_scripts,
                total_slides=self.total_slides,
                original_ppt_path=self.current_ppt_path,
                logger_callback=custom_logger
            )
            
            if self.is_running and not self.cancel_event.is_set():
                if "Error" in output_path:
                    raise RuntimeError(output_path)
                
                self.ui.update_status("Video packaged successfully!", 100, "Complete")
                self.ui.display_content(f"🎬 VIDEO COMPILED!\n\nYour lecture video file has been successfully generated and saved next to your presentation:\n📁 {output_path}")
                self.ui.disable_kill_button()
        except KeyboardInterrupt:
            self.handle_kill_process()
        except Exception as e:
            if self.is_running and not self.cancel_event.is_set():
                error_msg = str(e)
                self.ui.update_status(f"Export Error: {error_msg}", 0, "Failed")
                self.ui.display_content(f"❌ VIDEO EXPORT FAILED\n\nMoviePy encoder aborted due to the following failure:\n\n⚠️ {error_msg}")
                self.ui.disable_kill_button()

    def handle_play_audio(self):
        self.current_slide = 1
        self.cancel_event.clear()
        self.ui.enable_kill_button()
        playback_thread = threading.Thread(target=self._lecture_playback_loop)
        playback_thread.start()

    def _lecture_playback_loop(self):
        try:
            all_images = os.listdir(self.image_dir) if os.path.exists(self.image_dir) else []
            while self.current_slide <= self.total_slides and self.is_running and not self.cancel_event.is_set():
                audio_path = os.path.join(self.audio_dir, f"slide_{self.current_slide}.mp3")
                
                matched_image_name = None
                target_marker = f"slide{self.current_slide}.png"
                for img_name in all_images:
                    if img_name.lower() == target_marker:
                        matched_image_name = img_name
                        break
                
                image_path = os.path.join(self.image_dir, matched_image_name if matched_image_name else f"Slide{self.current_slide}.PNG")

                if os.path.exists(audio_path) and os.path.exists(image_path):
                    self.ui.project_slide_image(image_path)
                    slide_percentage = int((self.current_slide / self.total_slides) * 100)
                    self.ui.update_status(f"Presenting Slide {self.current_slide} of {self.total_slides}", slide_percentage, f"Slide {self.current_slide}")
                    
                    if (self.current_slide - 1) < len(self.slide_scripts):
                        self.ui.display_content(self.slide_scripts[self.current_slide - 1])
                    
                    mixer.music.load(audio_path)
                    mixer.music.play()
                    
                    time.sleep(0.15)
                    while mixer.music.get_busy() and self.is_running and not self.cancel_event.is_set():
                        time.sleep(0.5)
                    self.current_slide += 1
                else:
                    self.current_slide += 1

            if self.is_running and not self.cancel_event.is_set():
                self.ui.update_status("Presentation run complete.", 100, "Finished")
                self.ui.disable_kill_button()
                
        except Exception as e:
            if self.is_running:
                self.ui.update_status(f"Playback Error: {str(e)}", 0, "Error")
                self.ui.disable_kill_button()

    def handle_window_close(self):
        print("Shutting down LectureForge AI core processes cleanly...")
        self.is_running = False  
        mixer.music.stop()       
        self.ui.root.destroy()