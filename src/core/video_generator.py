"""
Location: /mount/src/lectureforgeai/src/core/video_generator.py
"""
import os
import re
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

        # Gather files and key them EXPLICITLY by slide number, rather than
        # sorting images and audio independently and assuming position i in
        # one list corresponds to position i in the other.
        #
        # That assumption is fragile: if even one file is missing on either
        # side (a failed audio generation that didn't raise loudly, a
        # skipped image render, etc.), every slide after the gap silently
        # shifts out of alignment with its audio -- with no error, just a
        # video where image and narration drift apart partway through.
        #
        # Keying explicitly by the number extracted from each filename
        # makes mismatches IMPOSSIBLE to silently paper over: if slide 14's
        # audio is missing, slide 14 is reported as missing, not silently
        # filled in with slide 15's audio shifted into its place.
        def extract_slide_number(filename):
            nums = re.findall(r'\d+', os.path.basename(filename))
            return int(nums[-1]) if nums else None

        image_files = [
            os.path.join(image_dir, f) for f in os.listdir(image_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        audio_files = [
            os.path.join(audio_dir, f) for f in os.listdir(audio_dir)
            if f.lower().endswith(('.mp3', '.wav', '.aac'))
        ]

        images_by_number = {}
        for path in image_files:
            num = extract_slide_number(path)
            if num is not None:
                images_by_number[num] = path

        audio_by_number = {}
        for path in audio_files:
            num = extract_slide_number(path)
            if num is not None:
                audio_by_number[num] = path

        # Verify we found assets matching the slide count expectations
        if not images_by_number or not audio_by_number:
            raise ValueError(
                f"Asset directories are empty or missing media formats. "
                f"Found {len(images_by_number)} images and {len(audio_by_number)} audio files."
            )

        expected_numbers = set(range(1, total_slides + 1)) if total_slides else (
            set(images_by_number.keys()) | set(audio_by_number.keys())
        )
        missing_images = sorted(n for n in expected_numbers if n not in images_by_number)
        missing_audio = sorted(n for n in expected_numbers if n not in audio_by_number)

        if missing_images or missing_audio:
            raise ValueError(
                f"Missing assets detected -- cannot guarantee correct slide/audio "
                f"alignment. Missing images for slide(s): {missing_images or 'none'}. "
                f"Missing audio for slide(s): {missing_audio or 'none'}."
            )

        slide_numbers_in_order = sorted(expected_numbers)

        if logger:
            logger(f"Compiling {len(slide_numbers_in_order)} slides into {output_path}...")

        clips = []
        for slide_num in slide_numbers_in_order:
            img = images_by_number[slide_num]
            audio = audio_by_number[slide_num]
            slide_clip = self.create_slide_clip(img, audio)
            clips.append(slide_clip)

        # Concatenate all slide clips sequentially
        final_video = concatenate_videoclips(clips, method="compose")

        # Write the final video file to disk.
        #
        # Speed notes:
        # - fps=15 is plenty for a static slideshow (image + narration, no real
        #   motion) and noticeably faster to encode than the previous fps=24.
        # - threads tells libx264 to use multiple CPU cores during encoding
        #   instead of a single core. Streamlit Cloud's free tier typically
        #   gives 2-4 cores; adjust this number to match your actual container.
        # - preset="veryfast" / "ultrafast" tells x264 to spend much less time
        #   searching for optimal compression. Default is "medium", which is
        #   tuned for content with real motion. For a slideshow (a still
        #   image held for several seconds, almost no inter-frame change),
        #   the quality difference between "medium" and "veryfast" is barely
        #   perceptible, but the encode time difference is large. Try
        #   "veryfast" first; drop to "ultrafast" if you want it faster still
        #   and don't mind a slightly larger output file.
        # - ffmpeg_params=["-crf", "23"] sets constant-rate-factor quality
        #   (lower = higher quality/larger file, 23 is a reasonable default).
        #   Combined with a fast preset, this keeps file size sane without
        #   spending extra encode time chasing marginal quality gains.
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

        # Close clips to release system resources
        final_video.close()
        for clip in clips:
            clip.close()

        if logger:
            logger("Lecture compilation complete.")

        return output_path
