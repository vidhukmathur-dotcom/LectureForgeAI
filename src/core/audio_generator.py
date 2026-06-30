import os
import re
import asyncio
import edge_tts


def _sanitize_for_tts(text: str) -> str:
    """
    Strips emoji and other characters that edge-tts's underlying transport
    has been observed to choke on with encoding errors (e.g. "'latin-1'
    codec can't encode character..."). The AI-generated narration text can
    occasionally include emoji or other expressive Unicode characters even
    when not explicitly asked for, and those have caused TTS synthesis to
    fail outright rather than just rendering oddly.

    This removes characters outside the Basic Multilingual Plane's common
    text ranges (which covers standard Latin, accented characters, and
    most punctuation) -- specifically targeting emoji and symbol blocks,
    while leaving normal narration text untouched.
    """
    if not text:
        return text

    # Remove characters in common emoji/symbol Unicode ranges.
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001FAFF"  # symbols & pictographs, emoji, supplemental symbols
        "\U00002600-\U000027BF"  # misc symbols, dingbats (includes ❌, ✅, etc.)
        "\U0001F1E6-\U0001F1FF"  # regional indicator symbols (flags)
        "\U00002190-\U000021FF"  # arrows
        "\U00002B00-\U00002BFF"  # misc symbols and arrows
        "\U0000FE0F"             # variation selector (emoji presentation)
        "]+",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", text)

    # Collapse any double spaces left behind by the removal, and trim.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()

    return cleaned


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

        safe_text = _sanitize_for_tts(text)

        async def _synthesize():
            communicate = edge_tts.Communicate(safe_text, voice_profile)
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

        async def _synthesize_one(slide_num, text, output_path):
            safe_text = _sanitize_for_tts(text)
            async with semaphore:
                try:
                    print(f"[AudioGenerator] Starting slide {slide_num} -> {output_path}")
                    communicate = edge_tts.Communicate(safe_text, voice_profile)
                    await communicate.save(output_path)

                    # Verify the file actually landed on disk with real
                    # content, not just that the call returned without
                    # raising. A 0-byte or missing file with no exception
                    # would otherwise pass through silently undetected.
                    if not os.path.exists(output_path):
                        raise RuntimeError(
                            f"edge_tts.save() returned without error, but no file "
                            f"exists at {output_path}"
                        )
                    file_size = os.path.getsize(output_path)
                    if file_size == 0:
                        raise RuntimeError(
                            f"edge_tts.save() produced a 0-byte file at {output_path}"
                        )

                    print(f"[AudioGenerator] Finished slide {slide_num}: {file_size} bytes")
                    return output_path

                except Exception as e:
                    print(f"[AudioGenerator] FAILED slide {slide_num}: {type(e).__name__}: {e}")
                    raise

        async def _synthesize_all():
            tasks = [
                _synthesize_one(idx + 1, text, path)
                for idx, (text, path) in enumerate(zip(slide_scripts, output_paths))
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
