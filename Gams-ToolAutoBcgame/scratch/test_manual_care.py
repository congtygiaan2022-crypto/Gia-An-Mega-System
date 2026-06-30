import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import MainWindow

class TestManualCare(unittest.TestCase):
    @patch('gui.main_window.ctk.CTk.mainloop') # Mock mainloop to prevent blocking
    @patch('gui.main_window.BrowserController')
    @patch('gui.main_window.GoogleSheetsReporter')
    @patch('core.auditor.FlashScoreAuditor')
    def test_manual_care_validation_and_flow(self, mock_auditor_cls, mock_reporter_cls, mock_browser_cls, mock_mainloop):
        # Instantiate MainWindow
        app = MainWindow()
        
        # 1. Test validation failures
        # Empty match name
        app.ent_care_match.delete(0, 'end')
        app.ent_care_match.insert(0, "")
        app.ent_care_stake.delete(0, 'end')
        app.ent_care_stake.insert(0, "1000")
        app.ent_care_odds.delete(0, 'end')
        app.ent_care_odds.insert(0, "1.15")
        
        app._start_manual_care()
        self.assertFalse(app.is_running)
        
        # Invalid stake
        app.ent_care_match.insert(0, "Arsenal vs Bayern")
        app.ent_care_stake.delete(0, 'end')
        app.ent_care_stake.insert(0, "invalid_number")
        app._start_manual_care()
        self.assertFalse(app.is_running)
        
        # Correct inputs validation
        app.ent_care_stake.delete(0, 'end')
        app.ent_care_stake.insert(0, "1000")
        
        # Mocking browser, sheets, auditor behavior
        mock_browser = MagicMock()
        mock_browser.check_alive.return_value = True
        mock_browser_cls.return_value = mock_browser
        app.browser = mock_browser
        
        mock_reporter = MagicMock()
        mock_reporter_cls.return_value = mock_reporter
        
        mock_auditor = MagicMock()
        # Mock auditor to return 1-0 result on first check
        mock_auditor.check_result.return_value = ("LIVE", 1, 0)
        mock_auditor_cls.return_value = mock_auditor
        
        # We patch threading.Thread to run synchronously so we can test the target method _run_manual_care directly
        with patch('gui.main_window.threading.Thread') as mock_thread:
            app._start_manual_care()
            self.assertTrue(app.is_running)
            
            # Extract args passed to Thread
            thread_call_args = mock_thread.call_args[1]
            target_fn = thread_call_args['target']
            args = thread_call_args['args']
            
            # Execute the thread function synchronously
            target_fn(*args)
            
            # Verify browser is checked, reporter is called
            mock_reporter.add_bet_report.assert_called_once()
            mock_auditor.check_result.assert_called_once_with("Arsenal", "Bayern")
            mock_reporter.finalize_report.assert_called_once_with("Arsenal vs Bayern", True, 1.15, 1000.0)
            
            # The app should set is_running to False after finishing
            self.assertFalse(app.is_running)
            
        print("✅ Unit testing of validation and flow passed successfully!")

if __name__ == "__main__":
    unittest.main()
