Write-Host "Disinstallazione versioni GPU di torch, onnxruntime-gpu e audio-separator..."
pip uninstall -y torch torchvision torchaudio onnxruntime-gpu audio-separator

Write-Host "Reinstallazione versione CPU da requirements.txt..."
pip install -r requirements.txt

Write-Host "Installazione completata! L'ambiente è configurato per la CPU."
