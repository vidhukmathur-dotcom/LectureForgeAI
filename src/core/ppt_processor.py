import os
from pptx import Presentation

class PowerPointProcessor:
    """The Model: Responsible for extracting text and exporting slide images from PowerPoints."""
    
    def extract_text(self, file_path: str) -> str:
        """Opens a PowerPoint file and extracts text from every slide."""
        if not os.path.exists(file_path):
            return "Error: File not found."
            
        try:
            prs = Presentation(file_path)
            output = []
            for i, slide in enumerate(prs.slides, start=1):
                output.append(f"--- Slide {i} ---")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        output.append(shape.text.strip())
                output.append("") 
            return "\n".join(output)
        except Exception as e:
            return f"Failed to read PowerPoint file: {str(e)}"

    def export_slide_images(self, file_path: str, output_folder: str) -> int:
        """
        Uses Windows COM integration to open PowerPoint in the background 
        and export every slide cleanly as a PNG image.
        """
        # Ensure the output directory folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Absolute paths are strictly required by Windows system integrations
        abs_file_path = os.path.abspath(file_path)
        abs_output_folder = os.path.abspath(output_folder)
        
        # This dynamic import prevents crashes on non-Windows development environments
        import win32com.client
        
        try:
            # Launch an invisible background instance of Microsoft PowerPoint
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            
            # Open the presentation file safely in read-only background mode
            presentation = ppt_app.Presentations.Open(abs_file_path, WithWindow=False, ReadOnly=True)
            
            # Use PowerPoint's native engine to export all slides as images instantly
            # This saves files as slide1.PNG, slide2.PNG, etc. inside the folder
            presentation.Export(abs_output_folder, "PNG")
            
            # Clean up and close the presentation safely
            slide_count = presentation.Slides.Count
            presentation.Close()
            ppt_app.Quit()
            
            return slide_count
            
        except Exception as e:
            print(f"Windows Slide Image Export Failed: {str(e)}")
            return 0