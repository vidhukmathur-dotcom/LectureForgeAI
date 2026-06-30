"""
Location: /mount/src/lectureforgeai/src/core/ppt_processor.py

NOTE: Despite the filename (kept for backward compatibility with existing
imports in app.py), this module now processes PDF files, not PPTX files.

Why the switch: PPTX rendering on Linux required LibreOffice running in
headless mode, which is a heavyweight subprocess (full office suite startup
cost, significant RAM, fragile apt package installs on Streamlit Cloud).

The new approach asks the user to export their deck to PDF themselves
(a one-click action in both PowerPoint and Google Slides) before uploading.
That moves the expensive PPTX -> PDF conversion onto the user's own machine,
for free, using software they already have. The server then only has to do
the cheap remaining step: read an already-finished PDF.

PyMuPDF (the 'fitz' module) handles BOTH text extraction and PDF-to-image
rendering natively, in-process, in pure Python -- no LibreOffice, no
pdftoppm subprocess, no packages.txt entries needed for this step at all.
"""
import os
import fitz  # PyMuPDF


class PowerPointProcessor:
    """
    Class name kept as-is for backward compatibility with existing imports
    (app.py does `from src.core.ppt_processor import PowerPointProcessor`).
    Internally, this now processes PDF files.
    """

    def __init__(self):
        pass

    def extract_text(self, pdf_path):
        """
        Extracts text from each page of the PDF, structured identically to
        the old PPTX version's output format (so downstream code -- the AI
        prompt, etc. -- doesn't need to change).
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        doc = fitz.open(pdf_path)
        extracted_text = ""

        for idx, page in enumerate(doc):
            extracted_text += f"\n--- Slide {idx + 1} ---\n"
            page_text = page.get_text("text").strip()
            if page_text:
                # Collapse excess whitespace the same way the old PPTX
                # extractor did, for consistent downstream formatting.
                clean_text = " ".join(page_text.split())
                extracted_text += clean_text + "\n"

        doc.close()
        return extracted_text

    def extract_text_per_slide(self, pdf_path):
        """
        Same as extract_text(), but returns a list of per-page strings
        instead of one combined string. Useful if a future change wants to
        send each slide's text independently (e.g. to an AI engine) rather
        than parsing one big combined block.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        doc = fitz.open(pdf_path)
        per_slide_text = []

        for page in doc:
            page_text = page.get_text("text").strip()
            clean_text = " ".join(page_text.split()) if page_text else ""
            per_slide_text.append(clean_text)

        doc.close()
        return per_slide_text

    def export_slide_images(self, pdf_path, output_dir, dpi=100):
        """
        Renders each page of the PDF to a PNG image, directly in-process via
        PyMuPDF -- no external binary, no subprocess call, no LibreOffice.

        Args:
            pdf_path: path to the uploaded PDF file
            output_dir: directory to write slide_1.png, slide_2.png, ... into
            dpi: rendering resolution. 100 is plenty for 720p-1080p video
                frames; raise it if you need sharper stills for some other
                purpose.

        Returns:
            total_slides (int)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        os.makedirs(output_dir, exist_ok=True)

        doc = fitz.open(pdf_path)
        total_slides = len(doc)

        if total_slides == 0:
            doc.close()
            raise ValueError(f"PDF at '{pdf_path}' contains no pages.")

        # PyMuPDF renders at 72 DPI by default (PDF's native unit). To get
        # a different DPI, scale the rendering matrix accordingly.
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for idx, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix)
            output_image_path = os.path.join(output_dir, f"slide_{idx}.png")
            pix.save(output_image_path)

        doc.close()
        return total_slides
