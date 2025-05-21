import os
import unittest
from src.utils.prompt_generator import generate_prompt


class TestPromptGenerator(unittest.TestCase):
    def setUp(self):
        self.test_path = ".test_matlab_ai_prompt"

    def tearDown(self):
        # Cleans up the file created during tests
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def test_generate_prompt_creates_file(self):
        content = generate_prompt(self.test_path)
        self.assertTrue(os.path.exists(self.test_path))
        with open(self.test_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(content, file_content)
        self.assertIn("MATLAB simulation expert. STRICT RULES:", content)

    def test_generate_prompt_default_path(self):
        # Tests that the .matlab_ai_prompt file is created in the current
        # folder
        default_file = ".matlab_ai_prompt"
        if os.path.exists(default_file):
            os.remove(default_file)

        content = generate_prompt()
        self.assertTrue(os.path.exists(default_file))
        with open(default_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(content, file_content)

        # Cleanup
        os.remove(default_file)


if __name__ == "__main__":
    unittest.main()
