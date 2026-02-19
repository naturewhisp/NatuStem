
import sys
import unittest
from unittest.mock import MagicMock, patch
import os
from collections import deque
import logging

# We need to mock flet and audio_separator before importing main because
# main.py imports them at the top level and instantiates them.

# Mock flet
mock_flet = MagicMock()
mock_flet.Colors.GREY_400 = "grey400"
mock_flet.Colors.GREY_500 = "grey500"
mock_flet.Colors.WHITE = "white"
mock_flet.MainAxisAlignment.START = "start"
mock_flet.CrossAxisAlignment.CENTER = "center"
mock_flet.ThemeMode.DARK = "dark"
mock_flet.ScrollMode.AUTO = "auto"
mock_flet.FontWeight.BOLD = "bold"
mock_flet.padding.only = lambda left=0: f"padding_left_{left}"
mock_flet.dropdown.Option = lambda x: x # just return the value for simple testing

sys.modules["flet"] = mock_flet

# Mock audio_separator
mock_audio_separator = MagicMock()
mock_separator_class = MagicMock()
mock_audio_separator.separator.Separator = mock_separator_class
sys.modules["audio_separator"] = mock_audio_separator
sys.modules["audio_separator.separator"] = mock_audio_separator.separator

# Now we can import main
# We need to add the current directory to sys.path to import main
sys.path.append(os.getcwd())
import main

class TestPersistence(unittest.TestCase):

    def setUp(self):
        # Reset mocks
        mock_separator_class.reset_mock()

        # Instantiate App
        self.app = main.AudioSeparatorApp()
        self.app.page = MagicMock() # Mock the page object
        self.app.status_text = MagicMock()
        self.app.log_output = MagicMock()
        self.app.progress_bar = MagicMock()
        self.app.separate_btn = MagicMock()
        self.app.select_file_btn = MagicMock()
        self.app.model_dropdown = MagicMock()
        self.app.shifts_slider = MagicMock()
        self.app.overlap_slider = MagicMock()

        # Set default UI values
        self.app.audio_file_path = "/path/to/audio.mp3"
        self.app.model_dropdown.value = "htdemucs_ft.yaml"
        self.app.shifts_slider.value = 2
        self.app.overlap_slider.value = 0.25

        # Mock the Separator instance returned by the class
        self.mock_separator_instance = MagicMock()
        mock_separator_class.return_value = self.mock_separator_instance
        self.mock_separator_instance.separate.return_value = ["vocal.wav", "drums.wav"] # Simulate output

    def test_separator_persistence(self):
        """
        Test that the Separator instance is reused across multiple calls to run_separation,
        and load_model is only called when the model changes.
        """

        # --- First Run ---
        print("Running separation 1...")
        self.app.run_separation()

        # Verification 1: Separator should be instantiated
        mock_separator_class.assert_called_once()
        # Verification 2: load_model should be called with the initial model
        self.mock_separator_instance.load_model.assert_called_with(model_filename="htdemucs_ft.yaml")
        # Verification 3: separate should be called
        self.mock_separator_instance.separate.assert_called()

        # Reset call counts for the instance methods, but NOT the class constructor (to verify it's not called again)
        self.mock_separator_instance.load_model.reset_mock()
        self.mock_separator_instance.separate.reset_mock()

        # --- Second Run (Same Model) ---
        print("Running separation 2 (same model)...")
        self.app.run_separation()

        # Verification 4: Separator constructor should NOT be called again (count remains 1)
        mock_separator_class.assert_called_once()

        # Verification 5: load_model should NOT be called (cached)
        self.mock_separator_instance.load_model.assert_not_called()

        # Verification 6: separate should be called again
        self.mock_separator_instance.separate.assert_called()


        # --- Third Run (Different Model) ---
        print("Running separation 3 (different model)...")
        self.app.model_dropdown.value = "htdemucs.yaml" # Change model
        self.app.run_separation()

        # Verification 7: load_model SHOULD be called with the new model
        self.mock_separator_instance.load_model.assert_called_with(model_filename="htdemucs.yaml")

if __name__ == '__main__':
    unittest.main()
