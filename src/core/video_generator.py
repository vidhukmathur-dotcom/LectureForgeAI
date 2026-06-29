"""
Location: /mount/src/lectureforgeai/src/core/video_generator.py
"""

# Alternative MoviePy v2.x top-level namespace imports
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

class VideoGenerator:
    def __init__(self, *args, **kwargs):
        """
        Initializes the VideoGenerator engine for LectureForgeAI.
        Accepts any configuration arguments passed by the factory.
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
        Flexibly extracts arguments whether passed positionally or via keywords.
        """
        # 1. Extract slide_images (Check positional index 0, then keywords)
        slide_images = args[0] if len(args) > 0 else kwargs.get('slide_images') or kwargs.get('image_paths') or kwargs.get('images')
        
        # 2. Extract audio_tracks (Check positional index 1, then keywords)
        audio_tracks = args[1] if len(args) > 1 else kwargs.get('audio_tracks') or kwargs.get('audio_paths') or kwargs.get('audios')
        
        # 3. Extract output_path (Check positional index 2, then keywords)
        output_path = args[2] if len(args) > 2 else kwargs.get('output_path') or kwargs.get('output_file') or kwargs.get('video_path')

        # Fallback validation check
        if not slide_images or not audio_tracks or not output_path:
            raise ValueError(
                f"Missing required video compilation data. "
                f"Received slide_images: {bool(slide_images)}, "
                f"audio_tracks: {bool(audio_tracks)}, "
                f"output_path: {bool(output_path)}. "
                f"Full kwargs keys: {list(kwargs.keys())}"
            )

        if len(slide_images) != len(audio_tracks):
            raise ValueError("The number of slide images must match the number of audio tracks.")

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
