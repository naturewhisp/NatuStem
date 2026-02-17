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
Ensure you have Python 3.10 - [3.12](https://www.python.org/downloads/release/python-31210/) installed.
> **Note:** Python 3.13 and newer are currently not supported due to dependency incompatibilities (specifically `diffq` / `diffq-fixed` build errors).

#### Managing Multiple Python Versions (Windows) - Recommended
If you have a newer version of Python installed (e.g., 3.13+) and need to use Python 3.12 for this project without uninstalling your current version, we recommend using **pyenv-win**.

1. **Install pyenv-win**:
   Open PowerShell as Administrator and run the following command:
   ```powershell
   Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
   ```
   *Note: You may need to close and reopen PowerShell for the changes to take effect.*

2. **Install Python 3.12**:
   ```powershell
   pyenv install 3.12.9
   ```

3. **Set Local Version**:
   Navigate to the project directory and set the local Python version. This ensures that `python` commands in this folder use version 3.12.
   ```powershell
   cd path\to\your\project
   pyenv local 3.12.9
   ```

4. **Verify Installation**:
   Check that the correct version is active:
   ```powershell
   python --version
   # Output should be: Python 3.12.9
   ```

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
2. Install the default required Python packages (CPU mode):

```bash
pip install -r requirements.txt
```

### Switching between CPU and GPU Modes (Windows)

This application supports both CPU and GPU (NVIDIA CUDA) processing. By default, the CPU mode is installed.
To switch between modes, use the provided PowerShell scripts.

#### Enable GPU Mode (Requires NVIDIA GPU)
This will install PyTorch with CUDA 12.1 support and the GPU-optimized version of `audio-separator`.

1. Open PowerShell in the project directory.
2. Run the installation script:
   ```powershell
   .\install_gpu.ps1
   ```
3. Once complete, the application will automatically use your GPU for processing.

#### Revert to CPU Mode
If you encounter issues or want to switch back to CPU processing:

1. Open PowerShell in the project directory.
2. Run the revert script:
   ```powershell
   .\install_cpu.ps1
   ```

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
