import unittest
from unittest.mock import patch, MagicMock
from src.llm import LLMInterface


class TestLLMInterface(unittest.TestCase):

    @patch("src.llm.OpenAI")
    def setUp(self, mock_openai):
        # Mock OpenAI client to avoid real API calls
        self.mock_client = MagicMock()
        mock_openai.return_value = self.mock_client

        # Patch system prompt to avoid file dependency
        with patch.object(LLMInterface, "_load_system_prompt", return_value="You are a MATLAB code assistant."):
            self.llm = LLMInterface(model="gpt-4o-mini")

    def test_clean_code_removes_markdown(self):
        raw_code = "```matlab\nx = 1;\n```"
        expected_code = "x = 1;"
        self.assertEqual(self.llm._clean_code(raw_code), expected_code)

    @patch("src.llm.OpenAI")
    def test_generate_code(self, mock_openai):
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="x = 1;"))]
        self.mock_client.chat.completions.create.return_value = mock_response

        result = self.llm.generate_code(prompt="Create a variable x = 1")
        self.assertIn("x = 1", result)

    @patch("src.llm.OpenAI")
    def test_fix_code(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="x = 1;"))]
        self.mock_client.chat.completions.create.return_value = mock_response

        broken_code = "x = ;"
        errors = ["Missing expression after ="]
        result = self.llm.fix_code(broken_code, errors)
        self.assertIn("x = 1", result)

    def test_model_name_is_stored(self):
        self.assertEqual(self.llm.model, "gpt-4o-mini")

    @patch("src.llm.OpenAI")
    def test_generate_code_handles_exceptions(self, mock_openai):
        self.mock_client.chat.completions.create.side_effect = Exception(
            "API Error")

        result = self.llm.generate_code("Make x = 1")
        self.assertIn("Error generating code", result)

    @patch("src.llm.OpenAI")
    def test_fix_code_handles_exceptions(self, mock_openai):
        self.mock_client.chat.completions.create.side_effect = Exception(
            "Fix Error")

        broken_code = "x = ;"
        result = self.llm.fix_code(broken_code, ["Some error"])
        self.assertEqual(result, broken_code)  # Should return original


if __name__ == "__main__":
    unittest.main()
