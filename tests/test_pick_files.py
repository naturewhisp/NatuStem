import sys
from unittest.mock import MagicMock

# Mock flet and audio_separator before importing main
mock_flet = MagicMock()
# Mock ft.Colors which is used in pick_files_result
mock_flet.Colors.WHITE = "white"
mock_flet.Colors.GREY_400 = "grey400"
sys.modules["flet"] = mock_flet

mock_audio_separator = MagicMock()
sys.modules["audio_separator"] = mock_audio_separator
sys.modules["audio_separator.separator"] = MagicMock()

# Now import the class to test
from main import AudioSeparatorApp

import unittest

class TestPickFilesResult(unittest.TestCase):
    def setUp(self):
        self.app = AudioSeparatorApp()
        # Mock the UI components that pick_files_result interacts with
        self.app.file_path_text = MagicMock()
        self.app.separate_btn = MagicMock()
        self.app.page = MagicMock()

    def test_pick_files_result_with_files(self):
        # Create a mock file object with a path attribute
        mock_file = MagicMock()
        mock_file.path = "/test/path/audio.mp3"
        files = [mock_file]

        self.app.pick_files_result(files)

        # Assertions
        self.assertEqual(self.app.audio_file_path, "/test/path/audio.mp3")
        self.assertEqual(self.app.file_path_text.value, "/test/path/audio.mp3")
        self.assertEqual(self.app.file_path_text.color, "white")
        self.assertIs(self.app.separate_btn.disabled, False)
        self.app.page.update.assert_called_once()

    def test_pick_files_result_with_none(self):
        # Initial state: assume a file was previously selected
        self.app.audio_file_path = "/old/path.mp3"

        self.app.pick_files_result(None)

        # Assertions
        # Note: current implementation does NOT clear self.audio_file_path if files is None
        self.assertEqual(self.app.audio_file_path, "/old/path.mp3")
        self.assertEqual(self.app.file_path_text.value, "No file selected")
        self.assertEqual(self.app.file_path_text.color, "grey400")
        self.assertIs(self.app.separate_btn.disabled, True)
        self.app.page.update.assert_called_once()

    def test_pick_files_result_with_empty_list(self):
        self.app.pick_files_result([])

        # Assertions
        self.assertEqual(self.app.file_path_text.value, "No file selected")
        self.assertEqual(self.app.file_path_text.color, "grey400")
        self.assertIs(self.app.separate_btn.disabled, True)
        self.app.page.update.assert_called_once()

if __name__ == '__main__':
    unittest.main()
