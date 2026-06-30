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

    def generate_all_slide_audio(self, slide_scripts, audio_dir, voice_profile="en-US-BrianNeural", max_concurrent=6):
        """
        Synthesizes narration audio for ALL slides concurrently, inside a
        single event loop, instead of making one blocking edge-tts call per
        slide. Since each edge-tts call is mostly waiting on a network
        request to Microsoft's TTS service, running them concurrently
        (rather than one-after-another) cuts total audio generation time
        roughly proportional to the number of slides.

        Two important reliability details handled here:

        1. asyncio.gather() is all-or-nothing by default: if ANY one task
           raises an exception, gather() immediately cancels every other
           still-running task. With 20-30 slides fired off at once, a
           single transient network hiccup on ONE slide would silently
           wipe out audio for every other slide that hadn't finished
           writing yet -- which is exactly what produced "missing audio
           for slides 1,2,4-26" with only slide 3 surviving (it happened
           to finish writing before the cancellation reached it).
           Fixed by passing return_exceptions=True, so a failure on one
           slide is captured and reported, not allowed to cancel the rest.

        2. Firing 20-30 simultaneous connections at Microsoft's edge-tts
           endpoint in one burst is also a plausible trigger for that
           initial failure in the first place (rate limiting / connection
           resets under burst load). A semaphore caps how many requests run
           concurrently at once (default 6), trading a little speed for
           real reliability.

        Args:
            slide_scripts: list of narration strings, one per slide, in
                slide order (slide_scripts[0] -> slide 1, etc.)
            audio_dir: directory to write slide_<n>.mp3 files into
            voice_profile: edge-tts voice id, e.g. "en-US-BrianNeural"
            max_concurrent: max number of simultaneous edge-tts requests

        Returns:
            List of output file paths, in the same order as slide_scripts.

        Raises:
            RuntimeError if any slide's audio failed to generate, naming
            exactly which slide(s) and why -- rather than silently
            returning a partial/corrupted result.
        """
        os.makedirs(audio_dir, exist_ok=True)

        output_paths = [
            os.path.join(audio_dir, f"slide_{idx}.mp3")
            for idx in range(1, len(slide_scripts) + 1)
        ]

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _synthesize_one(text, output_path):
            async with semaphore:
                communicate = edge_tts.Communicate(text, voice_profile)
                await communicate.save(output_path)

        async def _synthesize_all():
            tasks = [
                _synthesize_one(text, path)
                for text, path in zip(slide_scripts, output_paths)
            ]
            # return_exceptions=True is the critical fix: without it, one
            # failing task cancels every other in-flight task immediately,
            # silently destroying audio for slides that would otherwise
            # have succeeded.
            return await asyncio.gather(*tasks, return_exceptions=True)

        results = asyncio.run(_synthesize_all())

        failures = [
            (idx + 1, result)
            for idx, result in enumerate(results)
            if isinstance(result, Exception)
        ]

        if failures:
            failure_details = "; ".join(f"slide {num}: {err}" for num, err in failures)
            raise RuntimeError(
                f"Audio generation failed for {len(failures)} of {len(slide_scripts)} "
                f"slide(s). This is usually a transient network issue with the TTS "
                f"service -- try again. Details: {failure_details}"
            )

        return output_paths
