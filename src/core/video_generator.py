"""
Location: /mount/src/lectureforgeai/src/core/video_generator.py
"""

import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

class VideoGenerator:
    def __init__(self, *args, **kwargs):
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

    def compile_lecture_video(self, *args, **kwargs):
        """
        Stitches multiple slides and audio tracks into a final lecture video.
        Dynamically resolves paths from image_dir and audio_dir.
        """
        # Extract environment variables sent by app.py
        image_dir = kwargs.get('image_dir')
        audio_dir = kwargs.get('audio_dir')
        total_slides = kwargs.get('total_slides', 0)
        
        # Determine an output path fallback if app.py handles writing outside or expects it here
        # Usually it looks next to the original ppt or inside the output stack
        original_ppt = kwargs.get('original_ppt_path', 'lecture.pptx')
        output_path = kwargs.get('output_path') or os.path.splitext(original_ppt)[0] + ".mp4"

        # Log progress if callback exists
        logger = kwargs.get('logger_callback')
        if logger:
            logger("Resolving assets from directories...")

        if not image_dir or not os.path.exists(image_dir):
            raise ValueError(f"Invalid or missing image directory: {image_dir}")
        if not audio_dir or not os.path.exists(audio_dir):
            raise ValueError(f"Invalid or missing audio directory: {audio_dir}")

        # Gather and sort files numerically/alphabetically
        slide_images = sorted([
            os.path.join(image_dir, f) for f in os.listdir(image_dir) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        
        audio_tracks = sorted([
            os.path.join(audio_dir, f) for f in os.listdir(audio_dir) 
            if f.lower().endswith(('.mp3', '.wav', '.aac'))
        ])

        # Verify we found assets matching the slide count expectations
        if not slide_images or not audio_tracks:
            raise ValueError(
                f"Asset directories are empty or missing media formats. "
                f"Found {len(slide_images)} images and {len(audio_tracks)} audio files."
            )

        if len(slide_images) != len(audio_tracks):
            raise ValueError(
                f"Mismatch in asset count. "
                f"Found {len(slide_images)} images and {len(audio_tracks)} audio tracks."
            )

        if logger:
            logger(f"Compiling {len(slide_images)} slides into {output_path}...")

        clips = []
        for img, audio in zip(slide_images, audio_tracks):
            slide_clip = self.create_slide_clip(img, audio)
            clips.append(slide_clip)

        # Concatenate all slide clips sequentially
        final_video = concatenate_videoclips(clips, method="compose")

        # Write the final video file to disk
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

        if logger:
            logger("Lecture compilation complete.")
            
        return output_path
