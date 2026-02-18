import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock flet before importing main
mock_flet = MagicMock()
# Mock ft.Colors which is used in pick_files_result
mock_flet.Colors.WHITE = "white"
mock_flet.Colors.GREY_400 = "grey400"
sys.modules["flet"] = mock_flet

# Mock audio_separator
mock_audio_separator = MagicMock()
sys.modules["audio_separator"] = mock_audio_separator
sys.modules["audio_separator.separator"] = mock_audio_separator

# Now import main
import main
from main import AudioSeparatorApp

class TestSecurityFix(unittest.TestCase):
    def setUp(self):
        self.app = AudioSeparatorApp()
        # Set a sensitive input path to simulate the vulnerability
        self.app.audio_file_path = "/sensitive/path/song.mp3"

        # Mock UI elements that might be accessed
        self.app.model_dropdown = MagicMock()
        self.app.model_dropdown.value = "test_model"
        self.app.shifts_slider = MagicMock()
        self.app.shifts_slider.value = 2
        self.app.overlap_slider = MagicMock()
        self.app.overlap_slider.value = 0.25
        self.app.append_log = MagicMock()
        self.app.update_status = MagicMock()
        self.app.page = MagicMock()

        # Additional mocks needed for run_separation
        self.app.separate_btn = MagicMock()
        self.app.select_file_btn = MagicMock()
        self.app.progress_bar = MagicMock()
        self.app.log_output = MagicMock()
        self.app.logs = [] # Using a list instead of deque for simplicity in tests

    @patch("pathlib.Path.mkdir")
    @patch("main.Separator")
    def test_run_separation_output_dir_security(self, mock_separator_cls, mock_mkdir):
        # Mock separator instance methods
        mock_separator_instance = mock_separator_cls.return_value
        mock_separator_instance.separate.return_value = [] # Return empty list so we don't hit processing loop

        # Run the method
        # This runs in the main thread in the test, so no threading issues
        self.app.run_separation()

        # Check Separator initialization args to see where output_dir is pointing
        call_args = mock_separator_cls.call_args
        self.assertIsNotNone(call_args, "Separator should have been initialized")

        _, kwargs = call_args
        output_dir_arg = kwargs.get("output_dir")

        # In the vulnerable version, output_dir = input_path.parent / input_path.stem
        # So for input "/sensitive/path/song.mp3", output is "/sensitive/path/song"

        # In the secure version, output_dir should be inside "output/" folder
        # We expect something that ends with "output/song" (or "output\song" on Windows)
        expected_suffix = os.path.join("output", "song")

        # This assertion should FAIL on the vulnerable code
        self.assertTrue(str(output_dir_arg).endswith(expected_suffix),
                        f"SECURITY VULNERABILITY: Output directory '{output_dir_arg}' does not end with '{expected_suffix}'. "
                        "It seems to be writing to the input directory instead of a safe 'output' folder.")

    @patch("pathlib.Path.mkdir")
    @patch("main.Separator")
    def test_status_message_absolute_path(self, mock_separator_cls, mock_mkdir):
        # Mock separator instance methods
        mock_separator_instance = mock_separator_cls.return_value
        mock_separator_instance.separate.return_value = []

        self.app.run_separation()

        # Verify update_status calls
        # We expect the last call to update_status to contain the ABSOLUTE path
        # The code currently uses relative path: output/song
        # We want: /abs/path/to/output/song

        expected_output_path = Path("output") / "song"
        expected_abs_path = str(expected_output_path.resolve())

        # Get all calls to update_status
        calls = self.app.update_status.call_args_list
        success_call = None
        for call in calls:
            arg = call[0][0]
            if "Success!" in arg:
                success_call = arg
                break

        self.assertIsNotNone(success_call, "Success message not found in update_status calls")

        # Assertion: Check if the message contains the absolute path
        # This fails if the code uses relative path
        self.assertIn(expected_abs_path, success_call,
                      f"Status message '{success_call}' does not contain absolute path '{expected_abs_path}'")

if __name__ == '__main__':
    unittest.main()
