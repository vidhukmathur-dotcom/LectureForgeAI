import os
from pptx import Presentation
from PIL import Image

# --- HYBRID DETECTION LAYER ---
# Streamlit Cloud servers always set a specific environment variable when running.
# We check for it here to decide whether to load Windows modules or safe backups.
IS_ON_SERVER = os.environ.get("STREAMLIT_RUNTIME_MOCK_HEARTBEAT") is not None or "STREAMLIT_SERVER_PORT" in os.environ

if not IS_ON_SERVER:
    # Safely import Windows-only features ONLY when running locally on your computer
    import win32com.client
    class PowerPointProcessor:
    def __init__(self):
        pass

    def extract_text(self, ppt_path):
        """Extracts text loops cleanly across both environments."""
        if not os.path.exists(ppt_path):
            raise FileNotFoundError(f"Presentation file not found at: {ppt_path}")
            
        prs = Presentation(ppt_path)
        extracted_text = ""
        for idx, slide in enumerate(prs.slides):
            extracted_text += f"\n--- Slide {idx + 1} ---\n"
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    clean_text = " ".join(shape.text.split())
                    extracted_text += clean_text + "\n"
        return extracted_text

    def export_slide_images(self, ppt_path, output_dir):
        """
        Switches engines dynamically. Uses high-res win32com locally,
        and uses safe fallback canvas sheets on the web server.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # --- IF RUNNING LIVE ON THE WEB SERVER ---
        if IS_ON_SERVER:
            prs = Presentation(ppt_path)
            total_slides = len(prs.slides)
            for idx in range(1, total_slides + 1):
                image_filename = f"slide_{idx}.png"
                output_image_path = os.path.join(output_dir, image_filename)
                canvas = Image.new("RGB", (1280, 720), color="#F8F9FA")
                canvas.save(output_image_path, "PNG")
            return total_slides

        # --- IF RUNNING LOCAL DESKTOP APP ON YOUR MACHINE ---
        else:
            # Your original local win32com image export code execution goes here:
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            presentation = ppt_app.Presentations.Open(os.path.abspath(ppt_path), WithWindow=False)
            
            total_slides = presentation.Slides.Count
            for idx in range(1, total_slides + 1):
                slide = presentation.Slides(idx)
                output_image_path = os.path.join(output_dir, f"slide_{idx}.png")
                slide.Export(output_image_path, "PNG")
                
            presentation.Close()
            ppt_app.Quit()
            return total_slides
