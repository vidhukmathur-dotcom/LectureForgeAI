import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from PIL import Image, ImageTk

class LectureForgeUI:
    """The View: Implements a clean, modern Windows Ribbon-style interface layout
    featuring grid-locked informational tracking fields and premium voice selection.
    """
    def __init__(self, controller):
        self.controller = controller
        
        self.root = tk.Tk()
        self.root.title("LectureForge AI — Academic Presentation Studio")
        self.root.geometry("1280x820")
        self.root.configure(bg="#f3f3f3") 
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TProgressbar", thickness=6, troughcolor="#e6e6e6", background="#0078d4", borderwidth=0)
        
        self.root.protocol("WM_DELETE_WINDOW", self.controller.handle_window_close)
        
        self._build_menu_bar()
        self._build_ribbon_bar()
        self._build_workspace_widgets()

    def _build_menu_bar(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="📁 Open PowerPoint Presentation...", accelerator="Ctrl+O", command=self.controller.handle_select_file)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit Studio", accelerator="Alt+F4", command=self.controller.handle_window_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        action_menu = tk.Menu(menu_bar, tearoff=0)
        action_menu.add_command(label="▶ Play Synced Presentation View", command=self.controller.handle_play_audio)
        action_menu.add_command(label="🎬 Export Standalone MP4 Video...", command=self.controller.handle_export_video)
        action_menu.add_separator()
        action_menu.add_command(label="⏹ Emergency Stop Process", command=self.controller.handle_kill_process)
        menu_bar.add_cascade(label="Actions", menu=action_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="📂 Open Output Folder Location", command=self._open_project_directory)
        tools_menu.add_command(label="📝 Open Generated Word Script", command=self._open_word_document)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="ℹ️ About LectureForge AI", command=self._show_about_dialog)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _open_project_directory(self):
        if self.controller.current_ppt_path:
            folder_path = os.path.dirname(self.controller.current_ppt_path)
            if os.path.exists(folder_path):
                os.startfile(folder_path)
        else:
            self.update_status("No active presentation path selected yet.", 0)

    def _open_word_document(self):
        if self.controller.current_ppt_path:
            folder = os.path.dirname(self.controller.current_ppt_path)
            base_name = os.path.basename(self.controller.current_ppt_path)
            raw_name, _ = os.path.splitext(base_name)
            word_file = os.path.join(folder, f"{raw_name}_Narration_Script.docx")
            
            if os.path.exists(word_file):
                os.startfile(word_file)
            else:
                self.update_status("Word script file not generated or missing.", 0)
        else:
            self.update_status("Please select and process a PowerPoint deck first.", 0)

    def _show_about_dialog(self):
        messagebox.showinfo(
            "About LectureForge AI",
            "LectureForge AI — Academic Presentation Studio\nVersion 1.2\n\n"
            "An automated orchestration engine designed to extract slide layers, "
            "synthesize professional scripts via Groq AI, and compile clean synchronized MP4 "
            "lecture videos for higher education modules."
        )

    def _build_ribbon_bar(self):
        self.ribbon = tk.Frame(self.root, bg="#ffffff", height=42, highlightthickness=1, highlightbackground="#e0e0e0")
        self.ribbon.grid(row=0, column=0, sticky="ew")
        self.ribbon.grid_propagate(False)
        
        ribbon_font = ("Segoe UI", 9)
        
        # SECTION 1: DOCUMENT OPERATIONS GROUP
        doc_group = tk.Frame(self.ribbon, bg="#ffffff")
        doc_group.pack(side="left", padx=(10, 5), fill="y")
        
        self.button = tk.Button(
            doc_group, text="📁 Open PPTX", font=ribbon_font, bg="#ffffff", fg="#202020",
            activebackground="#eaeaea", activeforeground="#202020", disabledforeground="#b0b0b0",
            bd=0, relief="flat", padx=12, pady=4, cursor="hand2", command=self.controller.handle_select_file
        )
        self.button.pack(side="left", fill="y", pady=2)
        
        div1 = tk.Frame(self.ribbon, bg="#e0e0e0", width=1)
        div1.pack(side="left", fill="y", padx=8, pady=6)
        
        # SECTION 2: PRODUCTION CONTROLS GROUP
        prod_group = tk.Frame(self.ribbon, bg="#ffffff")
        prod_group.pack(side="left", padx=5, fill="y")
        
        self.play_button = tk.Button(
            prod_group, text="▶ Play Preview", font=ribbon_font, bg="#ffffff", fg="#202020",
            activebackground="#eaeaea", activeforeground="#202020", disabledforeground="#b0b0b0",
            bd=0, relief="flat", state="disabled", padx=12, pady=4, cursor="hand2", command=self.controller.handle_play_audio
        )
        self.play_button.pack(side="left", fill="y", pady=2)
        
        self.export_button = tk.Button(
            prod_group, text="🎬 Render Video", font=ribbon_font, bg="#ffffff", fg="#202020",
            activebackground="#eaeaea", activeforeground="#202020", disabledforeground="#b0b0b0",
            bd=0, relief="flat", state="disabled", padx=12, pady=4, cursor="hand2", command=self.controller.handle_export_video
        )
        self.export_button.pack(side="left", fill="y", pady=2)
        
        div2 = tk.Frame(self.ribbon, bg="#e0e0e0", width=1)
        div2.pack(side="left", fill="y", padx=8, pady=6)
        
        # SECTION 3: VOICE CONFIGURATION DROPDOWN GROUP
        voice_group = tk.Frame(self.ribbon, bg="#ffffff")
        voice_group.pack(side="left", padx=5, fill="y")
        
        voice_lbl = tk.Label(voice_group, text="Voice Accent:", font=ribbon_font, bg="#ffffff", fg="#505050")
        voice_lbl.pack(side="left", padx=(5, 5), pady=8)
        
        self.voice_map = {
            "Male — US Academic (Brian)": "en-US-BrianNeural",
            "Female — US Studio (Emma)": "en-US-EmmaNeural",
            "Male — UK Professor (Ryan)": "en-GB-RyanNeural",
            "Female — UK Narrative (Sonia)": "en-GB-SoniaNeural",
            "Male — Indian Classroom (Neerja)": "en-IN-NeerjaNeural"
        }
        
        self.voice_combo = ttk.Combobox(voice_group, values=list(self.voice_map.keys()), font=ribbon_font, state="readonly", width=28)
        self.voice_combo.set("Male — US Academic (Brian)")
        self.voice_combo.pack(side="left", padx=2, pady=6)

        div3 = tk.Frame(self.ribbon, bg="#e0e0e0", width=1)
        div3.pack(side="left", fill="y", padx=8, pady=6)
        
        # SECTION 4: SYSTEM CANCEL GROUP
        sys_group = tk.Frame(self.ribbon, bg="#ffffff")
        sys_group.pack(side="left", padx=5, fill="y")
        
        self.kill_button = tk.Button(
            sys_group, text="⏹ Stop Process", font=ribbon_font, bg="#ffffff", fg="#a80000",
            activebackground="#fde7e9", activeforeground="#a80000", disabledforeground="#b0b0b0",
            bd=0, relief="flat", state="disabled", padx=12, pady=4, cursor="hand2", command=self.controller.handle_kill_process
        )
        self.kill_button.pack(side="left", fill="y", pady=2)

    # --- THE MISSING METHOD RE-ADDED HERE ---
    def get_selected_voice_accent(self) -> str:
        """Retrieves the active premium neural voice string configuration from dropdown selections."""
        display_name = self.voice_combo.get()
        return self.voice_map.get(display_name, "en-US-BrianNeural")
    # ----------------------------------------

    def _build_workspace_widgets(self):
        workspace = tk.Frame(self.root, bg="#f3f3f3", padx=15, pady=12)
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.columnconfigure(0, weight=68) 
        workspace.columnconfigure(1, weight=32)
        workspace.rowconfigure(0, weight=1)

        self.slide_frame = tk.Label(
            workspace, 
            text="Presentation Monitor\n\nSlide view previews populate here during execution passes.", 
            font=("Segoe UI", 10), 
            bg="#ffffff", 
            fg="#606060", 
            bd=0,
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        self.slide_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        right_container = tk.Frame(workspace, bg="#ffffff", highlightthickness=1, highlightbackground="#e0e0e0")
        right_container.grid(row=0, column=1, sticky="nsew")
        right_container.columnconfigure(0, weight=1)
        right_container.rowconfigure(0, weight=0)
        right_container.rowconfigure(1, weight=1)
        
        panel_lbl = tk.Label(right_container, text="Active Narration Script Text", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#202020", anchor="w", pady=6, padx=12)
        panel_lbl.grid(row=0, column=0, sticky="ew")
        
        self.text_display = tk.Text(
            right_container, 
            wrap="word", 
            font=("Segoe UI Edit", 10), 
            bg="#fafafa", 
            fg="#202020", 
            bd=0,
            padx=12,
            pady=6,
            state="disabled"
        )
        self.text_display.grid(row=1, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=self.text_display.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.text_display['yscrollcommand'] = scrollbar.set

        # BOTTOM DUAL-ZONE INFOBAR STATUS FOOTER (GRID LOCKED)
        footer_frame = tk.Frame(self.root, bg="#ffffff", height=50, highlightthickness=1, highlightbackground="#e0e0e0")
        footer_frame.grid(row=2, column=0, sticky="ew")
        footer_frame.grid_propagate(False)
        
        footer_frame.columnconfigure(0, weight=1)
        footer_frame.columnconfigure(1, weight=0)
        footer_frame.rowconfigure(0, weight=0)
        footer_frame.rowconfigure(1, weight=1)
        
        self.progress_bar = ttk.Progressbar(footer_frame, style="TProgressbar", orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.status_left = tk.Label(footer_frame, text="Ready.", font=("Segoe UI", 9), fg="#505050", bg="#ffffff", anchor="w")
        self.status_left.grid(row=1, column=0, sticky="w", padx=(15, 0), pady=(2, 0))
        
        self.status_right = tk.Label(footer_frame, text="Elapsed: --:-- | Remaining: --:--", font=("Segoe UI", 9, "bold"), fg="#0078d4", bg="#ffffff", anchor="e")
        self.status_right.grid(row=1, column=1, sticky="e", padx=(0, 15), pady=(2, 0))

    def update_status(self, left_msg: str, progress_val: int = None, right_msg: str = None):
        self.root.after(0, self._update_status_safeguard, left_msg, progress_val, right_msg)

    def _update_status_safeguard(self, left_msg: str, progress_val: int, right_msg: str):
        self.status_left.config(text=f"⚙️ {left_msg}")
        if right_msg is not None:
            self.status_right.config(text=right_msg)
        if progress_val is not None:
            self.progress_bar["value"] = progress_val
        self.root.update_idletasks()

    def _set_btn_state(self, btn, state):
        if state == "disabled":
            btn.config(state="disabled", bg="#ffffff")
        else:
            btn.config(state="normal", bg="#ffffff")

    def enable_play_button(self):
        self._set_btn_state(self.play_button, "normal")
        self._set_btn_state(self.export_button, "normal")

    def enable_kill_button(self):
        self.kill_button.config(state="normal", bg="#ffffff")
        self._set_btn_state(self.button, "disabled")
        self._set_btn_state(self.play_button, "disabled")
        self._set_btn_state(self.export_button, "disabled")

    def disable_kill_button(self):
        self.kill_button.config(state="disabled", bg="#ffffff")
        self._set_btn_state(self.button, "normal")
        self._set_btn_state(self.play_button, "normal")
        self._set_btn_state(self.export_button, "normal")

    def display_content(self, text: str):
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert(tk.END, text)
        self.text_display.config(state="disabled")

    def project_slide_image(self, image_path: str):
        if not os.path.exists(image_path): return
        try:
            img = Image.open(image_path)
            self.root.update_idletasks()
            width = self.slide_frame.winfo_width() - 4
            height = self.slide_frame.winfo_height() - 4
            if width < 10: width = 850 
            if height < 10: height = 580
            
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.slide_frame.config(image=self.tk_img, text="", bg="#ffffff")
        except Exception as e:
            print(f"Canvas drawing glitch: {str(e)}")

    def run(self):
        self.root.mainloop()