import sys
import os
from unittest.mock import MagicMock, patch
import unittest
import tempfile
import shutil
from pathlib import Path

# Mock dependencies compatible with other tests
mock_flet = MagicMock()
mock_flet.Colors.WHITE = "white"
mock_flet.Colors.GREY_400 = "grey400"
sys.modules["flet"] = mock_flet

# Mock audio_separator structure
mock_as = MagicMock()
sys.modules["audio_separator"] = mock_as
sys.modules["audio_separator.separator"] = mock_as.separator

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import AudioSeparatorApp

class TestCollisionHandling(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app = AudioSeparatorApp()
        # Mock UI elements
        self.app.model_dropdown = MagicMock()
        self.app.model_dropdown.value = "htdemucs_ft.yaml"
        self.app.shifts_slider = MagicMock()
        self.app.shifts_slider.value = 1
        self.app.overlap_slider = MagicMock()
        self.app.overlap_slider.value = 0.5
        self.app.status_text = MagicMock()
        self.app.log_output = MagicMock()
        self.app.page = MagicMock()
        self.app.select_file_btn = MagicMock()
        self.app.separate_btn = MagicMock()
        self.app.progress_bar = MagicMock()
        self.app.select_file_btn = MagicMock()
        self.app.model_dropdown = MagicMock()
        self.app.shifts_slider = MagicMock()
        self.app.overlap_slider = MagicMock()
        self.app.file_path_text = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.Separator')
    def test_overwrite_protection(self, MockSeparator):
        # Setup
        input_file = Path(self.test_dir) / "test_song.mp3"
        input_file.touch()
        self.app.audio_file_path = str(input_file)

        cwd = os.getcwd()
        os.chdir(self.test_dir)

        try:
            # Setup the mock separator
            separator_instance = MockSeparator.return_value
            # The separator returns the list of filenames relative to output_dir
            separator_instance.separate.return_value = ["test_song_(Vocals)_htdemucs_ft.wav"]

            # Create the 'output/test_song' directory
            output_dir = Path("output") / "test_song"
            output_dir.mkdir(parents=True)

            # Create the file that the separator "generated"
            generated_file = output_dir / "test_song_(Vocals)_htdemucs_ft.wav"
            generated_file.write_text("new content")

            # Create the file that would have been overwritten
            target_file = output_dir / "vocal.wav"
            target_file.write_text("original content")

            # Run separation
            self.app.run_separation()

            # Check if target_file content is "original content" (fixed)
            content = target_file.read_text()
            self.assertEqual(content, "original content", "Original file was overwritten!")

            # Check if new file was created
            new_file = output_dir / "vocal_1.wav"
            self.assertTrue(new_file.exists(), "New file with counter suffix not found!")
            self.assertEqual(new_file.read_text(), "new content", "New file content is incorrect!")
            # print("Success: 'vocal.wav' was preserved and 'vocal_1.wav' was created.")

        finally:
            os.chdir(cwd)

if __name__ == '__main__':
    unittest.main()
