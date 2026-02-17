# Audio Stem Separator

An application to separate audio tracks into isolated stems (vocals, drums, bass, other) using `audio-separator` and a modern Flet GUI.

## Features

- **Drag & Drop / File Picker**: Easily select audio files (MP3, WAV, FLAC).
- **Model Selection**: Choose between different separation models (default: `htdemucs_ft`).
- **Non-blocking Processing**: Audio separation runs in a background thread, keeping the GUI responsive.
- **Real-time Logs**: View progress and logs directly in the application.
- **Robust Output Management**: Automatically creates subfolders for separated tracks.

## Prerequisites

### 1. Python
Ensure you have Python 3.10 - 3.12 installed.
> **Note:** Python 3.13 and newer are currently not supported due to dependency incompatibilities (specifically `diffq` / `diffq-fixed` build errors).

### 2. FFmpeg (Required)
This application requires FFmpeg to process audio files.

- **Windows**:
  - Download from [ffmpeg.org](https://ffmpeg.org/download.html).
  - Extract the files and add the `bin` folder to your system PATH.
  - Verify by running `ffmpeg -version` in CMD/PowerShell.

- **macOS**:
  - Install using Homebrew: `brew install ffmpeg`

- **Linux (Ubuntu/Debian)**:
  - Run: `sudo apt-get install ffmpeg`

## Installation

1. Clone this repository or download the files.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

> **Note**: This installation uses the CPU version of `audio-separator`. If you have a compatible NVIDIA GPU and want faster processing, you can modify `requirements.txt` to use `audio-separator[gpu]` and install appropriate CUDA libraries.

## Usage

1. Run the application:

```bash
python main.py
```

2. Click "Select Audio File" to choose a track.
3. (Optional) Select a model from the dropdown. `htdemucs_ft` is recommended for high quality.
4. Click "Separate Stems".
5. Wait for the process to complete. The separated files will be saved in a new folder named after the input file, located in the same directory.

## Troubleshooting

- **"Failed to build 'diffq-fixed'" Error**:
  - This error typically occurs on Windows when using Python versions newer than 3.12 (e.g., Python 3.13, 3.14) or when C++ build tools are missing.
  - **Solution 1 (Recommended)**: Uninstall your current Python version and install **Python 3.12** from [python.org](https://www.python.org/downloads/).
  - **Solution 2**: If you are already on Python 3.10-3.12 and still see this error, you likely need to install the **Microsoft Visual C++ 14.0 or greater**. Download "Visual Studio Build Tools" and install the "Desktop development with C++" workload.

- **"Model file not found"**: The application attempts to download models automatically. Ensure you have an active internet connection on the first run.
- **Slow Processing**: Separation is computationally intensive. CPU processing can be slow. Consider using GPU if available.
- **FFmpeg Error**: If logs show FFmpeg errors, ensure it is correctly installed and added to your PATH.

## License

This project uses `audio-separator` which depends on various open-source models. Please respect the licenses of the models used.
