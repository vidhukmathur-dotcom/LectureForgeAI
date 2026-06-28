import os
from docx import Document
from docx.shared import Pt

class DocumentGenerator:
    """The Model: Responsible ONLY for creating formatted Microsoft Word documents."""
    
    def save_narration_to_word(self, script_text: str, original_ppt_path: str) -> str:
        """Takes the AI script text and packages it into a styled Word file."""
        try:
            doc = Document()
            
            # Add a professional title
            title = doc.add_paragraph()
            title_run = title.add_run("LectureForge AI – Generated Narration Script")
            title_run.font.name = 'Arial'
            title_run.font.size = Pt(22)
            title_run.font.bold = True
            
            # Add file metadata
            base_name = os.path.basename(original_ppt_path)
            meta = doc.add_paragraph()
            meta_run = meta.add_run(f"Source Presentation: {base_name}")
            meta_run.font.italic = True
            meta_run.font.size = Pt(10)
            
            doc.add_paragraph("\n")

            # Parse paragraphs and headings
            paragraphs = script_text.split('\n')
            for para in paragraphs:
                trimmed = para.strip()
                if not trimmed:
                    continue
                
                if trimmed.startswith("---") or trimmed.lower().startswith("slide"):
                    p = doc.add_paragraph()
                    run = p.add_run(trimmed)
                    run.font.name = 'Arial'
                    run.font.size = Pt(14)
                    run.font.bold = True
                else:
                    p = doc.add_paragraph()
                    run = p.add_run(trimmed)
                    run.font.name = 'Georgia'
                    run.font.size = Pt(11)

            # Save next to the original presentation
            folder = os.path.dirname(original_ppt_path)
            raw_name, _ = os.path.splitext(base_name)
            output_filename = f"{raw_name}_Narration_Script.docx"
            output_path = os.path.join(folder, output_filename)
            
            doc.save(output_path)
            return output_path
            
        except Exception as e:
            return f"Error exporting document: {str(e)}"