import os
from pptx import Presentation
from PIL import Image

# ==============================================================================
# 🔍 HYBRID SERVER DETECTION LAYER
# ==============================================================================
IS_ON_SERVER = os.environ.get("STREAMLIT_RUNTIME_MOCK_HEARTBEAT") is not None or "STREAMLIT_SERVER_PORT" in os.environ
# ==============================================================================

class PowerPointProcessor:
    def __init__(self):
        pass

    def extract_text(self, ppt_path):
        """
        Extracts structural text elements from presentation slide layouts cleanly.
        Runs identically on both local desktop and cloud server environments.
        """
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
        Switches engines dynamically: Uses safe fallback canvas sheets on the web cloud 
        server, and dynamically imports win32com locally only when executing on Windows.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 🌐 RUNNING LIVE ON THE WEB SERVER (LINUX)
        if IS_ON_SERVER:
            prs = Presentation(ppt_path)
            total_slides = len(prs.slides)
            
            for idx in range(1, total_slides + 1):
                image_filename = f"slide_{idx}.png"
                output_image_path = os.path.join(output_dir, image_filename)
                
                canvas = Image.new("RGB", (1280, 720), color="#F8F9FA")
                canvas.save(output_image_path, "PNG")
                
            return total_slides

        # 💻 RUNNING LOCAL DESKTOP APP ON YOUR MACHINE (WINDOWS)
        else:
            # --- LOCAL FUNCTIONAL IMPORT: Safe from Linux server engine sweeps ---
            import win32com.client
            
            # Wakes up your local copy of desktop Microsoft PowerPoint in the background
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            
            # Open the file silently without stealing screen window focus
            presentation = ppt_app.Presentations.Open(os.path.abspath(ppt_path), WithWindow=False)
            
            total_slides = presentation.Slides.Count
            for idx in range(1, total_slides + 1):
                slide = presentation.Slides(idx)
                output_image_path = os.path.join(output_dir, f"slide_{idx}.png")
                
                # Export the slide to a sharp, high-res local image asset
                slide.Export(output_image_path, "PNG")
                
            # Close files and terminate the desktop application process cleanly
            presentation.Close()
            ppt_app.Quit()
            
            return total_slides
