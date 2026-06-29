"""
Location: /mount/src/lectureforgeai/src/core/video_generator.py
"""

# MoviePy v2.x compatibility imports
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips

class VideoGenerator:
    def __init__(self):
        """
        Initializes the VideoGenerator engine for LectureForgeAI.
        """
        pass

    def create_slide_clip(self, image_path: str, audio_path: str) -> ImageClip:
        """
        Combines a single slide image with its corresponding narration audio.
        """
        # Load the audio to determine duration
        audio_clip = AudioFileClip(audio_path)
        
        # Load the image and set its duration to match the audio
        slide_clip = ImageClip(image_path).with_duration(audio_clip.duration)
        
        # Attach the audio to the image clip
        slide_clip = slide_clip.with_audio(audio_clip)
        
        return slide_clip

    def generate_video(self, slide_images: list, audio_tracks: list, output_path: str):
        """
        Stitches multiple slides and audio tracks into a final lecture video.
        
        :param slide_images: List of file paths to slide images.
        :param audio_tracks: List of file paths to corresponding audio narrations.
        :param output_path: Destination path for the rendered MP4 file.
        """
        if len(slide_images) != len(audio_tracks):
            raise ValueError("The number of slide images must match the number of audio tracks.")

        clips = []
        for img, audio in zip(slide_images, audio_tracks):
            slide_clip = self.create_slide_clip(img, audio)
            clips.append(slide_clip)

        # Concatenate all slide clips sequentially
        final_video = concatenate_videoclips(clips, method="compose")

        # Write the final video file to disk
        # (Using libx264/aac for universal web and Streamlit compatibility)
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac"
        )
        
        # Close clips to release system resources
        final_video.close()
        for clip in clips:
            clip.close()
