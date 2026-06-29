import os
import asyncio
import edge_tts


class AudioGenerator:
    def __init__(self):
        pass

    def generate_slide_audio(self, text, output_path, voice_profile="en-US-BrianNeural"):
        """
        Synthesizes a single script string into a high-fidelity neural audio
        file. Kept for backward compatibility / single-slide use.
        """
        target_dir = os.path.dirname(output_path)
        os.makedirs(target_dir, exist_ok=True)

        async def _synthesize():
            communicate = edge_tts.Communicate(text, voice_profile)
            await communicate.save(output_path)

        asyncio.run(_synthesize())
        return output_path

    def generate_all_slide_audio(self, slide_scripts, audio_dir, voice_profile="en-US-BrianNeural"):
        """
        Synthesizes narration audio for ALL slides concurrently, inside a
        single event loop, instead of making one blocking edge-tts call per
        slide. Since each edge-tts call is mostly waiting on a network
        request to Microsoft's TTS service, running them concurrently
        (rather than one-after-another) cuts total audio generation time
        roughly proportional to the number of slides.

        Args:
            slide_scripts: list of narration strings, one per slide, in
                slide order (slide_scripts[0] -> slide 1, etc.)
            audio_dir: directory to write slide_<n>.mp3 files into
            voice_profile: edge-tts voice id, e.g. "en-US-BrianNeural"

        Returns:
            List of output file paths, in the same order as slide_scripts.
        """
        os.makedirs(audio_dir, exist_ok=True)

        output_paths = [
            os.path.join(audio_dir, f"slide_{idx}.mp3")
            for idx in range(1, len(slide_scripts) + 1)
        ]

        async def _synthesize_one(text, output_path):
            communicate = edge_tts.Communicate(text, voice_profile)
            await communicate.save(output_path)

        async def _synthesize_all():
            tasks = [
                _synthesize_one(text, path)
                for text, path in zip(slide_scripts, output_paths)
            ]
            await asyncio.gather(*tasks)

        asyncio.run(_synthesize_all())
        return output_paths
