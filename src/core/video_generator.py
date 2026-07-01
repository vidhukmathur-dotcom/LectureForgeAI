"""
Location: /mount/src/lectureforgeai/src/core/video_generator.py
"""
import os
import re
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips


def _slide_number(filepath):
    """Extract the slide number from a filename like slide_7.png or slide_14.mp3."""
    name = os.path.splitext(os.path.basename(filepath))[0]  # e.g. "slide_7"
    match = re.search(r'(\d+)$', name)  # last digits at end of stem
    return int(match.group(1)) if match else 0


class VideoGenerator:
    def __init__(self, *args, **kwargs):
        pass

    def create_slide_clip(self, image_path: str, audio_path: str) -> ImageClip:
        """Combines a single slide image with its corresponding narration audio."""
        audio_clip = AudioFileClip(audio_path)
        slide_clip = ImageClip(image_path).with_duration(audio_clip.duration)
        slide_clip = slide_clip.with_audio(audio_clip)
        return slide_clip

    def compile_lecture_video(self, *args, **kwargs):
        """
        Stitches multiple slides and audio tracks into a final lecture video.
        """
        image_dir = kwargs.get('image_dir')
        audio_dir = kwargs.get('audio_dir')
        total_slides = kwargs.get('total_slides', 0)
        original_ppt = kwargs.get('original_ppt_path', 'lecture.pdf')
        output_path = kwargs.get('output_path') or os.path.splitext(original_ppt)[0] + ".mp4"
        logger = kwargs.get('logger_callback')

        if logger:
            logger("Resolving assets from directories...")

        if not image_dir or not os.path.exists(image_dir):
            raise ValueError(f"Invalid or missing image directory: {image_dir}")
        if not audio_dir or not os.path.exists(audio_dir):
            raise ValueError(f"Invalid or missing audio directory: {audio_dir}")

        # Collect and sort by extracted slide number
        slide_images = sorted(
            [os.path.join(image_dir, f) for f in os.listdir(image_dir)
             if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
            key=_slide_number
        )
        audio_tracks = sorted(
            [os.path.join(audio_dir, f) for f in os.listdir(audio_dir)
             if f.lower().endswith(('.mp3', '.wav', '.aac'))],
            key=_slide_number
        )

        if not slide_images:
            raise ValueError(f"No images found in {image_dir}")
        if not audio_tracks:
            raise ValueError(f"No audio files found in {audio_dir}")
        if len(slide_images) != len(audio_tracks):
            raise ValueError(
                f"Image/audio count mismatch: "
                f"{len(slide_images)} images vs {len(audio_tracks)} audio files.\n"
                f"Images: {[os.path.basename(f) for f in slide_images]}\n"
                f"Audio:  {[os.path.basename(f) for f in audio_tracks]}"
            )

        if logger:
            logger(f"Compiling {len(slide_images)} slides into {output_path}...")

        clips = []
        for img, audio in zip(slide_images, audio_tracks):
            slide_clip = self.create_slide_clip(img, audio)
            clips.append(slide_clip)

        final_video = concatenate_videoclips(clips, method="compose")

        output_dir = os.path.dirname(os.path.abspath(output_path)) or "."
        final_video.write_videofile(
            output_path,
            fps=15,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="veryfast",
            ffmpeg_params=["-crf", "23"],
            temp_audiofile_path=output_dir,
        )

        final_video.close()
        for clip in clips:
            clip.close()

        if logger:
            logger("Lecture compilation complete.")

        return output_path
