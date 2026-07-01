import os
import json
import base64
import requests


class AIEngine:
    """
    Interacts with the Groq API to generate professional, slide-bound
    academic lecture narration scripts using:

    - openai/gpt-oss-120b  : main text narration model (replaces deprecated
                             llama-3.3-70b-versatile)
    - meta-llama/llama-4-scout-17b-16e-instruct : vision model for slides
                             that have no extractable text (image-only slides).
                             This model is technically deprecated on Groq but
                             remains the only vision-capable option available
                             there currently. Swap model_vision when Groq
                             releases a non-deprecated replacement.

    Strategy for image-only slides:
        1. Detect slides with empty/near-empty extracted text.
        2. Load the slide's already-rendered PNG from image_dir.
        3. Send it (base64-encoded) to the vision model with the deck's
           overall topic as context, asking for a brief visual description.
        4. Substitute that description into the extracted_text passed to
           the main narration call, so the text model generates a proper
           spoken narration grounded in what the image actually shows --
           rather than generic filler or empty output.
    """

    TEXT_MODEL  = "openai/gpt-oss-120b"
    VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    MIN_SLIDE_TEXT_CHARS = 20  # below this, treat a slide as image-only

    def __init__(self):
        self.api_key  = os.environ.get("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def generate_lecture_narration(
        self,
        extracted_slide_text: str,
        total_slides: int,
        image_dir: str = None,
    ) -> list:
        """
        Generates an engaging lecture script for the whole deck in one call
        (preserving full cross-slide narrative context), returning a list of
        per-slide narration strings.

        Args:
            extracted_slide_text : combined text of all slides as produced by
                                   PowerPointProcessor.extract_text(), with
                                   "--- Slide N ---" separators.
            total_slides         : expected number of slides.
            image_dir            : path to the folder containing slide_N.png
                                   files. Required for vision enrichment of
                                   image-only slides; pass None to skip.

        Returns:
            list[str] of length total_slides, in slide order.
        """
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Please supply a valid Groq access key."
            )

        # Step 1: enrich image-only slides with vision descriptions
        enriched_text = self._enrich_image_slides(
            extracted_slide_text, total_slides, image_dir
        )

        # Step 2: generate full narration from enriched text
        narration_list = self._request_narration(enriched_text, total_slides)

        # Step 3: retry once if slide count is wrong
        if len(narration_list) != total_slides:
            narration_list = self._request_narration(
                enriched_text,
                total_slides,
                retry_correction=(
                    f"Your previous response had {len(narration_list)} entries "
                    f"but there are exactly {total_slides} slides. "
                    f"Return exactly {total_slides} entries in the 'slides' array."
                ),
            )

        # Step 4: pad / truncate as last resort
        if len(narration_list) < total_slides:
            narration_list += [
                f"Moving forward to slide {len(narration_list) + i + 1}."
                for i in range(total_slides - len(narration_list))
            ]
        elif len(narration_list) > total_slides:
            narration_list = narration_list[:total_slides]

        return narration_list

    # ------------------------------------------------------------------ #
    #  Vision enrichment                                                   #
    # ------------------------------------------------------------------ #

    def _enrich_image_slides(
        self, extracted_slide_text: str, total_slides: int, image_dir: str
    ) -> str:
        """
        For slides whose extracted text is below MIN_SLIDE_TEXT_CHARS, sends
        the slide's rendered PNG to the Groq vision model and substitutes
        a visual description into the extracted text block, so the main
        narration call has real content to work from instead of nothing.
        """
        if not image_dir or not os.path.exists(image_dir):
            return extracted_slide_text

        lines = extracted_slide_text.split("\n")
        enriched_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Detect a slide header line
            import re
            header_match = re.match(
                r'^---\s*Slide\s+(\d+)\s*---', line.strip(), re.IGNORECASE
            )
            if not header_match:
                enriched_lines.append(line)
                i += 1
                continue

            slide_num = int(header_match.group(1))
            enriched_lines.append(line)
            i += 1

            # Collect the body text for this slide (up to the next header)
            body_lines = []
            while i < len(lines):
                if re.match(r'^---\s*Slide\s+\d+', lines[i].strip(), re.IGNORECASE):
                    break
                body_lines.append(lines[i])
                i += 1

            body_text = "\n".join(body_lines).strip()

            if len(body_text) < self.MIN_SLIDE_TEXT_CHARS:
                # Image-only slide -- ask vision model to describe it
                image_path = os.path.join(image_dir, f"slide_{slide_num}.png")
                description = self._describe_image(image_path, slide_num, total_slides)
                if description:
                    enriched_lines.append(
                        f"[Visual slide -- image description: {description}]"
                    )
                    print(f"[AIEngine] Enriched image-only slide {slide_num} with vision description.")
                else:
                    enriched_lines.extend(body_lines)
            else:
                enriched_lines.extend(body_lines)

        return "\n".join(enriched_lines)

    def _describe_image(self, image_path: str, slide_num: int, total_slides: int) -> str:
        """
        Sends a single slide image to the Groq vision model and returns a
        concise description suitable for use as lecture narration source text.
        Returns an empty string on any failure (caller falls back to filler).
        """
        if not os.path.exists(image_path):
            print(f"[AIEngine] Vision: image not found at {image_path}")
            return ""

        try:
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"[AIEngine] Vision: failed to read image: {e}")
            return ""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"This is slide {slide_num} of {total_slides} in an academic "
                                f"lecture presentation. The slide contains primarily visual content "
                                f"with little or no text. Please describe what you see in this slide "
                                f"concisely and factually (2-4 sentences), focusing on what an "
                                f"instructor would draw attention to when presenting it to students. "
                                f"Do not invent content that isn't visible."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        }

        try:
            response = requests.post(
                self.base_url, json=payload, headers=headers, timeout=60
            )
            data = response.json()
            if response.status_code == 200:
                return data["choices"][0]["message"]["content"].strip()
            else:
                err = data.get("error", {}).get("message", "unknown error")
                print(f"[AIEngine] Vision API error for slide {slide_num}: {err}")
                return ""
        except Exception as e:
            print(f"[AIEngine] Vision request failed for slide {slide_num}: {e}")
            return ""

    # ------------------------------------------------------------------ #
    #  Main narration call                                                 #
    # ------------------------------------------------------------------ #

    def _request_narration(
        self, extracted_slide_text: str, total_slides: int, retry_correction: str = None
    ) -> list:
        system_instruction = (
            "You are an elite higher education professor delivering a professional, "
            "clear classroom lecture. Your task is to write a spoken narration script "
            "based on the extracted slide text provided below.\n\n"
            "CRITICAL CONSTRAINTS FOR BALANCED NARRATION:\n"
            "1. DO NOT JUST READ THE SLIDE: Synthesise, explain, and elaborate on the "
            "points naturally as a human instructor would. Use professional spoken "
            "transitions that reference earlier and upcoming slides where it aids flow.\n"
            "2. STAY ANCHORED TO THE FACTS: Do NOT introduce completely new external "
            "data, outside anecdotes, or ungrounded case examples.\n"
            f"3. MATCH SLIDE COUNT EXACTLY: The presentation has exactly {total_slides} "
            f"slides. Return exactly {total_slides} entries in the JSON array -- one per "
            "slide, in order. Do not skip, merge, or split slides.\n"
            "4. IMAGE-ONLY SLIDES: Some slides have a [Visual slide -- image description: ...]"
            " block instead of bullet text. Use that description to write a natural "
            "spoken narration for those slides, explaining the visual to students.\n\n"
            "STRICT OUTPUT FORMAT -- JSON ONLY:\n"
            "Respond with ONLY a single JSON object, no other text, no markdown fences:\n"
            '{"slides": ["narration for slide 1", "narration for slide 2", ...]}\n'
            f"The 'slides' array must have exactly {total_slides} string elements."
        )

        user_content = f"Here is the extracted slide text:\n{extracted_slide_text}"
        if retry_correction:
            user_content = f"{retry_correction}\n\n{user_content}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.TEXT_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user",   "content": user_content},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }

        try:
            response = requests.post(
                self.base_url, json=payload, headers=headers, timeout=120
            )
            data = response.json()
            if response.status_code != 200:
                err = data.get("error", {}).get("message", "Unknown API error.")
                raise RuntimeError(f"Groq API error ({response.status_code}): {err}")
            raw = data["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to reach Groq API: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Groq API response shape: {e}")

        return self._parse_narration_json(raw)

    def _parse_narration_json(self, raw_content: str) -> list:
        """Parses the model's JSON response, tolerating markdown code fences."""
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) >= 2 else cleaned.strip("`")
            cleaned = cleaned.strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Groq returned invalid JSON. Parse error: {e}. "
                f"Raw response started with: {raw_content[:200]!r}"
            )

        slides = parsed.get("slides")
        if not isinstance(slides, list):
            raise RuntimeError(
                f"Groq JSON missing 'slides' array. Got keys: "
                f"{list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}"
            )

        return [str(s).strip() for s in slides]
