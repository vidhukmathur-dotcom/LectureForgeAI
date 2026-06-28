import os
import re
# MODERN IMPORT PATHWAY FOR MOVIEPY v2.0+
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

class VideoGenerator:
    """The Model: Responsible ONLY for stitching slide images and audio recordings 
    together into a universally shareable MP4 video file (clean layout, no subtitles).
    """

    def compile_lecture_video(self, image_dir: str, audio_dir: str, slide_scripts: list, total_slides: int, original_ppt_path: str, logger_callback=None) -> str:
        """Assembles slide-by-slide image sheets and audio recordings into a master MP4 video timeline."""
        slide_clips = []
        all_images = os.listdir(image_dir) if os.path.exists(image_dir) else []

        try:
            for idx in range(1, total_slides + 1):
                audio_filename = f"slide_{idx}.mp3"
                audio_path = os.path.join(audio_dir, audio_filename)
                
                # Case-insensitive image lookup matching 'Slide1.PNG' or 'slide1.png'
                matched_image_name = None
                target_marker = f"slide{idx}.png"
                for img_name in all_images:
                    if img_name.lower() == target_marker:
                        matched_image_name = img_name
                        break
                
                image_path = os.path.join(image_dir, matched_image_name if matched_image_name else f"Slide{idx}.PNG")

                # Verify both mandatory media assets exist before processing
                if os.path.exists(audio_path) and os.path.exists(image_path):
                    
                    # --- PYTHON 3.13 PROTECTION GUARD ---
                    # Ensure the audio file is greater than 0 bytes so FFMPEG_AudioReader doesn't crash on init
                    if os.path.getsize(audio_path) == 0:
                        print(f"⚠️ Warning: Slide {idx} audio file is empty. Skipping to prevent Python 3.13 crash.")
                        continue
                    # -------------------------------------

                    try:
                        # 1. Open the audio file track safely
                        audio_clip = AudioFileClip(audio_path)
                        duration = audio_clip.duration
                        
                        # 2. Build the visual static base image clip matching the audio length
                        base_slide_clip = ImageClip(image_path).with_duration(duration)
                        
                        # 3. Attach soundtrack directly (No subtitles overlay layout)
                        composite_slide = base_slide_clip.with_audio(audio_clip)
                        slide_clips.append(composite_slide)
                    
                    except Exception as audio_err:
                        print(f"⚠️ Could not process media for slide {idx}: {str(audio_err)}")
                        continue
            
            if not slide_clips:
                return "Error: No matching, valid audio/image files found to export."

            # 4. CONCATENATION CHAINING
            master_lecture_timeline = concatenate_videoclips(slide_clips, method="compose")
            
            # Formulate output destination file path naming conventions next to the input deck folder
            folder = os.path.dirname(original_ppt_path)
            base_name = os.path.basename(original_ppt_path)
            raw_name, _ = os.path.splitext(base_name)
            output_video_path = os.path.join(folder, f"{raw_name}_Lecture_Video.mp4")
            
            # --- HIGH-SPEED ACCELERATED VIDEO WRITER ENCODING CONFIGURATION ---
            master_lecture_timeline.write_videofile(
                output_video_path, 
                fps=2, 
                codec="libx264", 
                audio_codec="aac",
                preset="ultrafast",
                threads=4,
                logger=logger_callback if logger_callback else 'bar'
            )
            # -------------------------------------------------------------------
            
            # Cleanly dismantle timeline objects out of RAM memory pipelines to release hard locks
            master_lecture_timeline.close()
            for clip in slide_clips:
                clip.close()
                
            return output_video_path
            
        except Exception as e:
            return f"Video rendering sequence aborted: {str(e)}"