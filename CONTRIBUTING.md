# 🛠️ Developer Guide — NatuStem

> **Version:** 1.0 · **Last Updated:** February 2026

This guide is for anyone who wants to contribute to, maintain, or extend **NatuStem**, a Python desktop application for separating audio tracks via AI (Demucs / MDX) with a Flet GUI.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Structure](#3-repository-structure)
4. [Code Architecture (`main.py`)](#4-code-architecture-mainpy)
5. [Development Environment Setup](#5-development-environment-setup)
6. [Execution Flow](#6-execution-flow)
7. [How to Add Features](#7-how-to-add-features)
8. [Patterns and Conventions](#8-patterns-and-conventions)
9. [Debugging and Troubleshooting](#9-debugging-and-troubleshooting)
10. [Testing](#10-testing)
11. [Dependency Management](#11-dependency-management)
12. [Contribution Workflow](#12-contribution-workflow)
13. [Release Notes](#13-release-notes)
14. [Known Issues and Limitations](#14-known-issues-and-limitations)
15. [Useful Resources](#15-useful-resources)

---

## 1. Project Overview

**NatuStem** separates audio files (MP3, WAV, FLAC) into individual musical components (*stems*): vocals, drums, bass, other — and optionally guitar and piano with 6-stem models.

| Feature | Detail |
|---|---|
| Application Type | Desktop GUI (single-window) |
| GUI Framework | [Flet](https://flet.dev/) |
| AI Engine | [`audio-separator`](https://github.com/karaokenerds/python-audio-separator) → Demucs |
| Primary Platform | Windows (macOS/Linux compatible) |
| Supported Python | **3.10 – 3.12** (3.13+ not supported) |

---

## 2. Tech Stack

| Component | Library / Tool | Role |
|---|---|---|
| **GUI** | `flet` | Cross-platform GUI framework based on Flutter |
| **Audio Separation** | `audio-separator` | Unified wrapper for Demucs, MDX-Net, and other models |
| **Inference** | `onnxruntime` / `onnxruntime-gpu` | Runtime for ONNX models |
| **Deep Learning** | `torch` (optional, for GPU) | PyTorch backend with CUDA |
| **Audio Processing** | `ffmpeg` (external) | Audio file decoding/encoding |
| **Path Management** | `pathlib` (stdlib) | Cross-platform path handling |
| **Concurrency** | `threading` (stdlib) | Non-blocking GUI separation |
| **Logging** | `logging` (stdlib) | Dual channel: GUI + file |

---

## 3. Repository Structure

```
NatuStem/
├── main.py                  # ← Main application (single source file)
├── requirements.txt         # CPU dependencies
├── requirements-gpu.txt     # GPU dependencies (CUDA 12.1)
├── install_cpu.ps1          # Switch → CPU mode script
├── install_gpu.ps1          # Switch → GPU mode script
├── instructions.md          # Original project specifications
├── README.md                # User documentation
├── CONTRIBUTING.md          # ← This guide
├── .gitignore               # Ignores venv, models, audio files, cache
├── input/                   # Source folder (gitignored)
├── output/                  # Output folder (gitignored)
└── venv/                    # Virtual environment (gitignored)
```

> ⚠️ **The project is currently a single-file application (`main.py`).** Any refactoring into modules is welcome — see [§7.4](#74-refactoring-into-modules).

---

## 4. Code Architecture (`main.py`)

The `main.py` file (~430 lines) contains 3 classes + 1 entry point:

### 4.1 `GuiLogHandler(logging.Handler)`
**Lines 13–39** · Custom handler for the `logging` module.

- **Purpose:** Redirects application logs (including `audio-separator` logs) to the GUI's `TextField`.
- **Critical Detail:** Suppresses `exc_info`, `stack_info`, and `exc_text` *only* for the GUI output, preserving them for other handlers (e.g., file). This avoids showing raw stack traces to the user.
- **Thread-safety:** `logging.Handler` is thread-safe by default due to its internal lock.

```
Flow:
  logging.info("msg")
      ↓
  GuiLogHandler.emit(record)
      ↓
  Remove traces → format → call append_log_callback()
      ↓
  TextField updated in GUI
```

### 4.2 `StderrTqdmHandler`
**Lines 42–74** · `sys.stderr` interceptor.

- **Purpose:** Captures `tqdm` output (progress bar) that `audio-separator` emits to stderr during model downloads and separation.
- **Mechanism:** Replaces `sys.stderr` with a custom object that:
  1. Passes all output to the original stderr (no data loss).
  2. Searches for heuristic patterns (`%|`, `it/s]`) typical of tqdm.
  3. Sends corresponding lines to the GUI via `status_callback`.
- **Buffer:** Accumulates characters until `\r` or `\n` to handle tqdm's in-place updates.

### 4.3 `AudioSeparatorApp`
**Lines 76–424** · Main application class.

#### Key Methods

| Method | Line | Responsibility |
|---|---|---|
| `__init__` | 77 | Initializes state (no Flet widgets here) |
| `main(page)` | 84 | Flet entry point: builds UI, configures logging |
| `setup_logging()` | 216 | Creates GUI + file handlers, silences noisy loggers |
| `pick_files_click(e)` | 258 | Opens file selection dialog (async) |
| `pick_files_result(files)` | 266 | Handles selection result |
| `start_separation(e)` | 290 | Disables UI, launches separation thread |
| `run_separation()` | 310 | **Core business logic** — executes in a separate thread |
| `append_log(msg)` | 280 | Adds line to GUI logs |
| `update_status(msg)` | 285 | Updates status text (tqdm progress) |
| `on_window_event(e)` | 210 | Restores stderr upon window closure |
| `on_shifts_change(e)` | 244 | Updates shifts slider label |
| `on_overlap_change(e)` | 248 | Updates overlap slider label |
| `on_model_change(e)` | 252 | Updates model description |

#### `run_separation()` – Detailed Flow

```
1. Determine input_path and output_dir (folder named after the file, next to the file)
2. Read UI parameters: model, shifts, overlap
3. Create Separator instance with demucs_params configuration
4. Load the model (separator.load_model) — automatic download on first use
5. Execute separation (separator.separate) — long/blocking operation
6. Post-processing: rename output files to readable names
   (e.g., "song_(Vocals)_htdemucs_ft.wav" → "vocal.wav")
7. Update status with output path
8. finally: re-enable all UI controls
```

### 4.4 Entry Point
**Lines 426–428**

```python
if __name__ == "__main__":
    app = AudioSeparatorApp()
    ft.app(target=app.main)
```

---

## 5. Development Environment Setup

### 5.1 Prerequisites

- **Python 3.10–3.12** (3.12.x recommended via `pyenv-win`)
- **FFmpeg** installed and in `PATH`
- **Git**

### 5.2 Initial Setup

```powershell
# Clone the repository
git clone https://github.com/<your-username>/NatuStem.git
cd NatuStem

# Create a virtual environment
python -m venv venv

# Activate the venv
.\venv\Scripts\Activate.ps1

# Install dependencies (CPU)
pip install -r requirements.txt

# Or GPU (NVIDIA + CUDA 12.1)
.\install_gpu.ps1
```

### 5.3 Execution

```powershell
python main.py
```

### 5.4 Recommended Editor

- **VS Code** with extensions: Python, Pylance, GitLens
- Open the workspace file `NatuStem.code-workspace` for default configuration

---

## 6. Execution Flow

```
                    ┌──────────────────────────┐
                    │      ft.app(target)       │
                    │   Creates Flet window     │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     app.main(page)        │
                    │  - Builds widgets         │
                    │  - setup_logging()        │
                    │  - Intercepts stderr      │
                    └────────────┬─────────────┘
                                 │
         ┌───────────────────────▼────────────────────────┐
         │              GUI EVENT LOOP                   │
         │  User interacts with the UI:                   │
         │  • Select file → pick_files_click()           │
         │  • Change model → on_model_change()           │
         │  • Adjust sliders → on_shifts/overlap_change()│
         │  • Click Separate → start_separation()        │
         └───────────────────────┬───────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   start_separation()      │
                    │  - Disables controls      │
                    │  - Starts daemon thread   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   [THREAD] run_separation │
                    │  - Creates Separator      │
                    │  - Loads model            │
                    │  - Separates audio        │  ← Heavy operation
                    │  - Renames output         │
                    │  - Re-enables controls    │
                    └──────────────────────────┘
```

---

## 7. How to Add Features

### 7.1 Adding a New Model

1. Add an `ft.dropdown.Option("model_name.yaml")` in the `main()` method within `self.model_dropdown.options`.
2. Add the description to the `self.model_descriptions` dictionary.
3. If the model produces different stems (e.g., 6 stems), verify that the keywords in the `rename_map` within `run_separation()` cover the new stems.

```python
# Example: adding support for an MDX model
ft.dropdown.Option("UVR-MDX-NET-Inst_HQ_3.onnx"),
```

### 7.2 Adding a New UI Parameter

Pattern to follow (example: "segment_size"):

1. **Create the widget** in `main()`:
   ```python
   self.segment_slider = ft.Slider(min=1, max=100, value=40, ...)
   self.segment_value_text = ft.Text(value="40", ...)
   ```

2. **Add the callback**:
   ```python
   def on_segment_change(self, e):
       self.segment_value_text.value = str(int(e.control.value))
       self.page.update()
   ```

3. **Insert the widget into the layout** (inside the main `ft.Column`).

4. **Read the value** in `run_separation()` and pass it to `demucs_params`:
   ```python
   segment_val = int(self.segment_slider.value)
   demucs_params={"segment_size": segment_val, ...}
   ```

5. **Disable/re-enable** the widget in `start_separation()` and in the `finally` block of `run_separation()`.

### 7.3 Adding Output Formats

Currently, output is hardcoded to WAV. To support other formats:

1. Add an `ft.Dropdown` for format (WAV, FLAC, MP3).
2. Pass the value to `Separator(output_format=...)`.
3. Update extensions in the `rename_map`.

### 7.4 Refactoring into Modules

If the file exceeds ~600 lines, consider splitting it into:

```
NatuStem/
├── main.py              # Entrypoint: ft.app(target=app.main)
├── app/
│   ├── __init__.py
│   ├── ui.py            # AudioSeparatorApp + layout construction
│   ├── separator.py     # Separation logic (run_separation)
│   ├── logging_setup.py # GuiLogHandler, StderrTqdmHandler, setup_logging
│   └── constants.py     # Models, descriptions, rename_map
```

> **Refactoring Rules:**
> - `AudioSeparatorApp` should remain the only entry point.
> - Flet widgets should never be imported into modules that do not handle UI.
> - `run_separation()` can become a standalone function that receives parameters and callbacks.

---

## 8. Patterns and Conventions

### 8.1 Threading

- Separation **must** occur in a daemon thread (`thread.daemon = True`).
- All GUI updates from secondary threads pass through `self.page.update()`. Flet handles cross-thread access internally.
- **Never use** `asyncio` for separation: `audio-separator` is synchronous and blocking.

### 8.2 Dual-Channel Logging

```
                    ┌─────────────┐
  logging.info() ──►│ Root Logger │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
    ┌─────────────────┐      ┌──────────────────┐
    │  GuiLogHandler  │      │  FileHandler     │
    │  (no stack)     │      │  (with stack)    │
    │  → TextField    │      │  → .log file     │
    └─────────────────┘      └──────────────────┘
```

- **GUI:** Shows only readable messages (no traceback).
- **File (`audio_separator.log`):** Includes full tracebacks for debugging.
- `flet` and `urllib3` loggers are silenced to WARNING.

### 8.3 Path Management

- **Always** use `pathlib.Path` for paths.
- Output is saved next to the source file (`input_path.parent / input_path.stem`).
- Never use `os.path.join()`.

### 8.4 Error Handling

- In `run_separation()`, the `try/except/finally` block:
  - **GUI:** Shows generic message ("An unexpected error occurred").
  - **Log file:** Logs full error with `exc_info=True`.
  - **Finally:** **Always** re-enables UI controls, even if an error occurs.

### 8.5 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Variables | `snake_case` | `audio_file_path` |
| Classes | `PascalCase` | `AudioSeparatorApp` |
| Constants | `UPPER_SNAKE_CASE` | `LOG_FILE_NAME` |
| Output files | `lowercase.ext` | `vocal.wav` |
| Flet callbacks | `on_<event>` / `<action>_click` | `on_model_change`, `pick_files_click` |

---

## 9. Debugging and Troubleshooting

### 9.1 Debug Logs

The `audio_separator.log` file in the project root contains full logs with stack traces. This is the **first place** to look for information when an error occurs.

```powershell
# Follow logs in real-time
Get-Content .\audio_separator.log -Wait -Tail 50
```

### 9.2 Debugging with VS Code

Add this configuration to `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "NatuStem Debug",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

> `"justMyCode": false` allows stepping into `audio-separator` and `flet` code with the debugger.

### 9.3 Common Developer Issues

| Issue | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: flet` | venv not activated | `.\venv\Scripts\Activate.ps1` |
| GUI does not update | Missing `self.page.update()` | Add `page.update()` after every widget modification |
| App freezes during separation | `run_separation()` running on main thread | Ensure it is in `threading.Thread` |
| Widgets disabled after error | `finally` does not restore state | Check the `finally` block in `run_separation()` |
| Stderr not restored | Crash before `on_window_event` | `daemon=True` mitigates, but verify |
| `diffq-fixed` build error | Python > 3.12 | Use Python 3.10–3.12 |
| Model not found | First run without internet | Connect to internet; models are downloaded to `~/.cache` |

### 9.4 Useful Log Levels

For deep debugging, lower the logger level:

```python
# In setup_logging(), temporarily change:
logger.setLevel(logging.DEBUG)
```

---

## 10. Testing

> ⚠️ The project currently **lacks automated tests**. Adding tests is a priority for contributors.

### 10.1 Recommended Testing Strategy

```
tests/
├── test_rename_logic.py    # Unit tests for rename logic
├── test_logging.py         # Tests for GuiLogHandler and StderrTqdmHandler
├── test_separator.py       # Integration tests with sample audio files
└── conftest.py             # pytest fixtures
```

### 10.2 What to Test First

1. **Rename Logic** (`rename_map` matching) — pure logic, easily testable:
   ```python
   def test_rename_vocals():
       filename = "song_(Vocals)_htdemucs_ft.wav"
       # Verify it matches "vocal.wav"
   ```

2. **`GuiLogHandler`** — Verify `exc_info` is suppressed for the callback but preserved for the record:
   ```python
   def test_gui_handler_suppresses_traceback():
       handler = GuiLogHandler(lambda msg: captured.append(msg))
       # ...
   ```

3. **`StderrTqdmHandler`** — Verify tqdm output parsing:
   ```python
   def test_tqdm_detection():
       handler = StderrTqdmHandler(lambda msg: captured.append(msg))
       handler.write("50%|████     | 5/10 [00:05<00:05, 1.00it/s]\r")
       handler.write("\n")
       assert len(captured) == 1
   ```

### 10.3 Recommended Framework

```powershell
pip install pytest pytest-mock
pytest tests/ -v
```

---

## 11. Dependency Management

### 11.1 Two Sets of Requirements

| File | Mode | Key Differences |
|---|---|---|
| `requirements.txt` | CPU | `audio-separator[cpu]`, `onnxruntime` |
| `requirements-gpu.txt` | GPU | `audio-separator[gpu]`, `onnxruntime-gpu` |

### 11.2 Adding a New Dependency

1. Add the dependency to **both** requirements files (if needed in both modes).
2. Specify **version pinning** for critical dependencies:
   ```
   new-lib>=1.0,<2.0
   ```
3. Test with a clean installation (create a new venv).

### 11.3 Switching CPU ↔ GPU

The `install_cpu.ps1` and `install_gpu.ps1` scripts:
1. Uninstall packages from the opposite mode.
2. Reinstall correct packages.

> ⚠️ **Do not mix** CPU and GPU packages in the same venv. Always use the provided scripts.

### 11.4 Python Constraint

The `Python 3.10–3.12` constraint is due to `diffq-fixed`, a dependency of `audio-separator` that requires C++ compilation and does not yet support Python 3.13+. Monitor `audio-separator` releases for changes.

---

## 12. Contribution Workflow

### 12.1 Branch Strategy

```
main          ← stable branch, always working
  └── feature/name-of-feature
  └── fix/bug-description
  └── refactor/what-is-being-restructured
```

### 12.2 How to Contribute

1. **Fork** the repository.
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Implement** changes following conventions in [§8](#8-patterns-and-conventions).
4. **Test** manually (and with automated tests if available).
5. **Commit** with clear messages:
   ```
   feat: add output format selection dropdown
   fix: prevent crash when no file is selected
   refactor: extract separation logic to separate module
   docs: update developer guide with testing section
   ```
6. **Push** and open a **Pull Request** to `main`.

### 12.3 PR Checklist

- [ ] App starts without errors (`python main.py`).
- [ ] UI controls work (file selection, model change, sliders).
- [ ] Separation completes and produces correctly renamed files.
- [ ] No widgets remain disabled after error or completion.
- [ ] Logs appear in GUI without stack traces.
- [ ] `audio_separator.log` file contains errors with stack traces.
- [ ] Necessary dependencies are in `requirements.txt` and/or `requirements-gpu.txt`.
- [ ] `.gitignore` covers any new generated files.

---

## 13. Release Notes

### 13.1 Packaging (Future)

To distribute NatuStem as an executable:

```powershell
# Option 1: PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed main.py

# Option 2: Flet pack (experimental)
flet pack main.py --name NatuStem --icon icon.png
```

> **Note:** Packaging requires special attention to AI models and FFmpeg, which must be bundled or documented as external dependencies.

### 13.2 Versioning

We recommend adopting [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):
- **MAJOR:** Breaking changes (e.g., removing model support).
- **MINOR:** New backward-compatible features.
- **PATCH:** Bug fixes.

---

## 14. Known Issues and Limitations

| # | Issue | Impact | Developer Note |
|---|---|---|---|
| 1 | `instructions.md` mentions `input/` and `output/` folders but app saves next to source file | Low | Document discrepancy; current behavior (next to source) is correct |
| 2 | No cancellation of ongoing separation | Medium | `audio-separator` does not support cancellation; would need `multiprocessing` + process termination |
| 3 | Daemon thread may corrupt files if app is closed during write | Low | Could add a controlled cancellation flag |
| 4 | Progress bar is indeterminate | Low | Real progress is shown via tqdm in status text |
| 5 | No drag & drop support | Low | Flet supports drag & drop, but it is not implemented |
| 6 | No automated tests | High | See [§10](#10-testing) |
| 7 | File renaming relies on heuristic keyword matching | Medium | May fail with models using different naming |

---

## 15. Useful Resources

### Documentation

- **Flet:** [flet.dev/docs](https://flet.dev/docs/)
- **audio-separator:** [GitHub](https://github.com/karaokenerds/python-audio-separator)
- **Demucs (Meta):** [GitHub](https://github.com/facebookresearch/demucs)
- **ONNX Runtime:** [onnxruntime.ai](https://onnxruntime.ai/)
- **Python `logging`:** [docs.python.org](https://docs.python.org/3/library/logging.html)

---

> 📝 **This guide is a living document.** Update it whenever you add features, change architecture, or discover new useful information for the next developer.
