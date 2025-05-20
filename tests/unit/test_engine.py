import os
import tempfile
import hashlib
import time
import unittest
from unittest.mock import MagicMock, patch

from src.engine import MatlabEngine


class TestMatlabEngine(unittest.TestCase):
    def setUp(self):
        # patch matlab.engine module
        self.eng_patcher = patch.dict('sys.modules', {
            'matlab': MagicMock(),
            'matlab.engine': MagicMock()
        })
        self.eng_patcher.start()
        # Mock start_matlab returning mock engine
        import matlab.engine
        self.mock_eng = MagicMock()
        matlab.engine.start_matlab.return_value = self.mock_eng

    def tearDown(self):
        self.eng_patcher.stop()

    def test_start_engine_success(self):
        engine = MatlabEngine(startup=True)
        self.assertTrue(engine.is_available)
        self.assertIs(engine.eng, self.mock_eng)

    def test_validate_code_no_engine(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = False
        self.assertEqual(
            engine.validate_code("code"),
            ["MATLAB Engine not available."])

    def test_validate_code_empty(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        self.assertEqual(engine.validate_code(""), ["No code to validate."])

    def test_validate_code_success(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        # mock checkcode return
        msg = MagicMock()
        msg.line = 10
        msg.message = "Warn"
        self.mock_eng.checkcode.return_value = [msg]
        result = engine.validate_code("disp('hi')")
        self.assertEqual(result, ["[Line 10] Warn"])

    def test_validate_code_no_issues(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        self.mock_eng.checkcode.return_value = []
        result = engine.validate_code("disp('hi')")
        self.assertEqual(result, ["No issues found."])

    def test_validate_code_exception(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        # raise exception when writing file
        with patch('builtins.open', side_effect=Exception('fail')):
            result = engine.validate_code("code")
            self.assertTrue(result and "Error during validation:" in result[0])

    def test_clean_ascii(self):
        text = 'café'
        self.assertEqual(MatlabEngine._clean_ascii(text), 'cafe')

    def test_execute_code_no_engine(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = False
        engine.eng = None
        msg, res = engine.execute_code("code")
        self.assertFalse(res['success'])
        self.assertIn('not available', res['error'])

    def test_execute_code_no_code(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        msg, res = engine.execute_code("")
        self.assertFalse(res['success'])
        self.assertIn('No code to execute.', msg)

    def test_execute_code_success_and_figure(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        # first eval runs script, second gets error_msg
        self.mock_eng.eval.side_effect = ["", ""]

        with tempfile.TemporaryDirectory() as tmp:
            with patch('tempfile.gettempdir', return_value=tmp):
                msg, res = engine.execute_code("disp('hi')")
                self.assertIn('Simulation executed', msg)
                self.assertIn('success', res)
                self.assertIn('output', res)
                self.assertIn('figure', res)

    def test_execute_code_exception(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        # force exception in makedirs
        with patch('os.makedirs', side_effect=Exception('faildir')):
            msg, res = engine.execute_code("disp('hi')")
            self.assertFalse(res['success'])
            self.assertIn('Error:', msg)

    def test_shutdown(self):
        engine = MatlabEngine(startup=False)
        engine.is_available = True
        engine.eng = self.mock_eng
        engine.shutdown()
        self.mock_eng.quit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
