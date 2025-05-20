import unittest
from unittest.mock import patch, MagicMock
from src.llm import LLMInterface


class TestLLMInterface(unittest.TestCase):

    @patch("src.llm.OpenAI")
    def test_generate_code_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="```matlab\nx = 1;\n```"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        llm = LLMInterface(model="gpt-4o-mini")
        result = llm.generate_code("Create a simple MATLAB script")

        self.assertEqual(result, "x = 1;")
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.llm.OpenAI")
    def test_generate_code_failure(self, mock_openai_class):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "API error")
        mock_openai_class.return_value = mock_client

        llm = LLMInterface(model="gpt-4o-mini")
        result = llm.generate_code("Invalid prompt")

        self.assertTrue(result.startswith("% Error generating code"))
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.llm.OpenAI")
    def test_fix_code_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="```matlab\ny = 2;\n```"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        llm = LLMInterface(model="gpt-4o-mini")
        original_code = "x = ;"
        errors = ["Error: unexpected end of expression"]
        result = llm.fix_code(original_code, errors)

        self.assertEqual(result, "y = 2;")
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.llm.OpenAI")
    def test_fix_code_failure(self, mock_openai_class):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "API error")
        mock_openai_class.return_value = mock_client

        llm = LLMInterface(model="gpt-4o-mini")
        original_code = "x = ;"
        errors = ["Error: unexpected end of expression"]
        result = llm.fix_code(original_code, errors)

        self.assertEqual(result, original_code)
        mock_client.chat.completions.create.assert_called_once()

    def test_clean_code(self):
        llm = LLMInterface(model="gpt-4o-mini")
        self.assertEqual(llm._clean_code("```matlab\nx = 5;\n```"), "x = 5;")
        self.assertEqual(llm._clean_code("```x = 10;```"), "x = 10;")
        self.assertEqual(llm._clean_code("x = 15;"), "x = 15;")


if __name__ == "__main__":
    unittest.main()
