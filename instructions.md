\# Project: Local Music Stemmer

\## Goal

Applicazione Python desktop (GUI) per separare tracce audio usando AI in locale.



\## Tech Stack

\- Language: Python 3.10 - 3.12 (versioni > 3.12 non supportate causa dipendenze)

\- GUI: Flet (Framework moderno)

\- AI Engine: audio-separator (wrapper di Demucs/MDX)

\- Audio Handling: ffmpeg-python



\## Constraints

1\. L'interfaccia non deve "freezare" durante l'elaborazione (usa Threading).

2\. Salva sempre i file separati nella cartella 'output/'.

3\. Leggi i file sorgente dalla cartella 'input/'.

4\. Usa 'pathlib' per la compatibilità Windows.

