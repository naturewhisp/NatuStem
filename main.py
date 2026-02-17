import flet as ft
from audio_separator.separator import Separator
import logging
import threading
import sys
from pathlib import Path
import re

# Custom Logging Handler to redirect logs to Flet GUI
class GuiLogHandler(logging.Handler):
    def __init__(self, append_log_callback):
        super().__init__()
        self.append_log_callback = append_log_callback

    def emit(self, record):
        try:
            msg = self.format(record)
            self.append_log_callback(msg)
        except Exception:
            self.handleError(record)

# Stderr handler to capture tqdm progress
class StderrTqdmHandler:
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.original_stderr = sys.stderr
        self.buffer = ""

    def write(self, message):
        # Pass through to original stderr
        try:
            self.original_stderr.write(message)
        except (OSError, ValueError):
            pass

        self.buffer += message
        # Process complete lines or carriage returns
        if '\r' in self.buffer or '\n' in self.buffer:
            # Split by either \r or \n
            chunks = re.split(r'[\r\n]+', self.buffer)
            self.buffer = chunks[-1] # Keep the last incomplete part

            for chunk in chunks[:-1]:
                clean_chunk = chunk.strip()
                if not clean_chunk:
                    continue
                # Heuristic for tqdm progress bar: looks for percentage or iteration speed
                if "%|" in clean_chunk or "it/s]" in clean_chunk:
                    self.status_callback(clean_chunk)

    def flush(self):
        try:
            self.original_stderr.flush()
        except (OSError, ValueError):
            pass

class AudioSeparatorApp:
    def __init__(self):
        self.audio_file_path = None
        self.output_folder = None
        self.is_separating = False
        self.log_handler = None
        self.stderr_handler = None

    def main(self, page: ft.Page):
        self.page = page
        page.title = "Audio Stem Separator"
        page.theme_mode = ft.ThemeMode.DARK
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.window_width = 800
        page.window_height = 700
        page.scroll = ft.ScrollMode.AUTO

        # UI Components
        self.pick_files_dialog = ft.FilePicker()
        self.file_path_text = ft.Text(value="No file selected", size=16, color=ft.Colors.GREY_400)
        self.select_file_btn = ft.Button(
            "Select Audio File",
            icon="audio_file", # Corrected from ft.icons.AUDIO_FILE
            on_click=self.pick_files_click
        )

        self.model_dropdown = ft.Dropdown(
            label="Model",
            width=300,
            options=[
                ft.dropdown.Option("htdemucs_ft.yaml"),
                ft.dropdown.Option("htdemucs.yaml"),
                ft.dropdown.Option("htdemucs_6s.yaml"),
                ft.dropdown.Option("hdemucs_mmi.yaml"),
            ],
            value="htdemucs_ft.yaml"
        )

        self.separate_btn = ft.Button(
            "Separate Stems",
            icon="music_note", # Corrected from ft.icons.Music_NOTE
            on_click=self.start_separation,
            disabled=True
        )

        # Indeterminate progress bar
        self.progress_bar = ft.ProgressBar(width=600, visible=False)
        self.status_text = ft.Text(value="", size=14, font_family="monospace")

        self.log_output = ft.TextField(
            label="Console Output",
            multiline=True,
            read_only=True,
            min_lines=15,
            max_lines=15,
            text_size=12,
            expand=True
        )

        # Layout
        page.add(
            ft.Column(
                controls=[
                    ft.Text("Audio Stem Separator", size=30, weight=ft.FontWeight.BOLD),
                    ft.Row([self.select_file_btn, self.file_path_text], alignment=ft.MainAxisAlignment.START),
                    ft.Row([self.model_dropdown], alignment=ft.MainAxisAlignment.START),
                    ft.Row([self.separate_btn], alignment=ft.MainAxisAlignment.START),
                    self.status_text,
                    self.progress_bar,
                    ft.Divider(),
                    ft.Text("Logs:"),
                    self.log_output
                ],
                spacing=20,
                expand=True
            )
        )

        # Configure Logging
        self.setup_logging()

        # Configure Stderr redirection
        self.stderr_handler = StderrTqdmHandler(self.update_status)
        sys.stderr = self.stderr_handler

        # Restore stderr on window destroy
        # Note: page.on_close is available in newer flet versions, or window_destroy on desktop
        page.window.on_event = self.on_window_event

        page.update()

    def on_window_event(self, e):
        if e.data == "close":
            if self.stderr_handler and hasattr(self.stderr_handler, 'original_stderr'):
                sys.stderr = self.stderr_handler.original_stderr
            self.page.window.destroy()

    def setup_logging(self):
        # Create custom handler
        self.log_handler = GuiLogHandler(self.append_log)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.log_handler.setFormatter(formatter)

        # Add handler to root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Suppress noisy loggers
        logging.getLogger("flet").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        # Avoid adding multiple handlers if setup_logging is called multiple times
        if not any(isinstance(h, GuiLogHandler) for h in logger.handlers):
            logger.addHandler(self.log_handler)

    async def pick_files_click(self, e):
        files = await self.pick_files_dialog.pick_files(
            allow_multiple=False,
            allowed_extensions=["mp3", "wav", "flac"],
            file_type=ft.FilePickerFileType.CUSTOM
        )
        self.pick_files_result(files)

    def pick_files_result(self, files):
        if files:
            file_path = files[0].path
            self.audio_file_path = file_path
            self.file_path_text.value = file_path
            self.file_path_text.color = ft.Colors.WHITE
            self.separate_btn.disabled = False
            self.page.update()
        else:
            self.file_path_text.value = "No file selected"
            self.file_path_text.color = ft.Colors.GREY_400
            self.separate_btn.disabled = True
            self.page.update()

    def append_log(self, message):
        if self.page:
            self.log_output.value += message + "\n"
            self.page.update()

    def update_status(self, message):
        if self.page:
            self.status_text.value = message
            self.page.update()

    def start_separation(self, e):
        if not self.audio_file_path:
            return

        self.is_separating = True
        self.separate_btn.disabled = True
        self.select_file_btn.disabled = True
        self.model_dropdown.disabled = True
        self.progress_bar.visible = True
        self.status_text.value = "Starting separation..."
        self.log_output.value = "" # Clear logs
        self.page.update()

        # Start separation in a separate thread
        thread = threading.Thread(target=self.run_separation)
        thread.daemon = True
        thread.start()

    def run_separation(self):
        try:
            input_path = Path(self.audio_file_path)

            # Create output directory: same folder as input file / [filename_no_ext]
            output_dir = input_path.parent / input_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)

            self.append_log(f"Input file: {input_path}")
            self.append_log(f"Output directory: {output_dir}")

            model_name = self.model_dropdown.value
            self.append_log(f"Selected model: {model_name}")

            # Initialize Separator
            self.append_log("Initializing Separator...")
            # We pass output_dir to Separator so it saves files there
            separator = Separator(
                log_level=logging.INFO,
                output_dir=str(output_dir),
                output_format="WAV"
            )

            # Load Model
            self.append_log(f"Loading model {model_name}...")
            separator.load_model(model_filename=model_name)
            self.append_log("Model loaded.")

            # Separate (removed invalid custom_output_names arg)
            self.append_log(f"Separating {input_path.name}...")
            output_files = separator.separate(str(input_path))

            self.append_log(f"Separation complete! Renaming files...")

            # Post-processing rename logic
            # Expected outputs from htdemucs usually follow pattern:
            # {input_filename}_(Vocals)_{model_name}.wav
            # We want: vocal.wav, bass.wav, drums.wav, other.wav

            renamed_files = []

            # Mapping of keyword in filename -> desired filename
            # Note: htdemucs output names can vary, but usually contain the stem name in parens or appended
            rename_map = {
                "Vocals": "vocal.wav",
                "Drums": "drums.wav",
                "Bass": "bass.wav",
                "Other": "other.wav"
            }

            for file in output_files:
                original_path = output_dir / file
                if not original_path.exists():
                    self.append_log(f"Warning: Expected file {file} not found.")
                    continue

                new_name = None
                for keyword, target in rename_map.items():
                    # Check if keyword is in filename (case-insensitive check might be safer but usually it's Capitalized)
                    if f"({keyword})" in file or f"_{keyword}_" in file or keyword in file:
                         new_name = target
                         break

                if new_name:
                    new_path = output_dir / new_name
                    # If target exists, overwrite or skip? Overwrite seems standard for "processing this file"
                    if new_path.exists():
                        try:
                            new_path.unlink()
                        except (OSError, ValueError) as e:
                            self.append_log(f"Error deleting existing {new_name}: {e}")

                    try:
                        original_path.rename(new_path)
                        renamed_files.append(new_name)
                        self.append_log(f"Renamed {file} -> {new_name}")
                    except (OSError, ValueError) as e:
                        self.append_log(f"Error renaming {file}: {e}")
                else:
                    self.append_log(f"Could not match stem for {file}, keeping original name.")
                    renamed_files.append(file)

            self.append_log(f"Generated files: {renamed_files}")

            # Final status update needs to happen on main thread via update_status or setting value
            self.update_status(f"Success! Output saved to {output_dir}")

        except Exception as e:
            self.append_log(f"Error: {e}")
            self.update_status("Error during separation.")
            logging.error(f"Separation failed", exc_info=True)
        finally:
            self.is_separating = False
            self.separate_btn.disabled = False
            self.select_file_btn.disabled = False
            self.model_dropdown.disabled = False
            self.progress_bar.visible = False
            self.page.update()

if __name__ == "__main__":
    app = AudioSeparatorApp()
    ft.app(target=app.main)
