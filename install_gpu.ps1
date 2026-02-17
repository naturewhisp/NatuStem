Write-Host "Disinstallazione versioni CPU di torch, onnxruntime e audio-separator..."
pip uninstall -y torch torchvision torchaudio onnxruntime audio-separator

Write-Host "Installazione PyTorch con supporto CUDA 12.1..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

Write-Host "Installazione dipendenze GPU da requirements-gpu.txt..."
pip install -r requirements-gpu.txt

Write-Host "Installazione completata! Ora l'ambiente è configurato per la GPU."
