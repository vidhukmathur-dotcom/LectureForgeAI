import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

class VideoGenerator:
    def __init__(self):
        pass

    def compile_lecture_video(self, image_dir, audio_dir, slide_scripts, total_slides, original_ppt_path, logger_callback=None):
        """
        Combines exported slide canvases and neural audio segments into a unified MP4 timeline.
        Fully optimized for cross-platform path mapping.
        """
        clips = []
        
        for idx in range(1, total_slides + 1):
            # 🎯 SAFE CROSS-PLATFORM PATHS
            img_path = os.path.join(image_dir, f"slide_{idx}.png")
            audio_path = os.path.join(audio_dir, f"slide_{idx}.mp3")
            
            if os.path.exists(img_path) and os.path.exists(audio_path):
                # Create audio clip and match image frame duration to it perfectly
                audio_clip = AudioFileClip(audio_path)
                img_clip = ImageClip(img_path).set_duration(audio_clip.duration)
                video_clip = img_clip.set_audio(audio_clip)
                clips.append(video_clip)
                
        if not clips:
            raise ValueError("No valid image/audio segments found to compile into a video.")
            
        # Stitch all slide video clips together seamlessly
        final_video = concatenate_videoclips(clips, method="compose")
        
        # 🎯 SAFE CROSS-PLATFORM OUTPUT DESTINATION
        workspace_dir = os.path.dirname(image_dir)
        output_path = os.path.join(workspace_dir, "output_lecture.mp4")
        
        # Render out the final MP4 stream
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            logger=logger_callback
        )
        
        # Explicitly close all clip threads to release file locks
        final_video.close()
        for clip in clips:
            clip.close()
            
        return output_path
