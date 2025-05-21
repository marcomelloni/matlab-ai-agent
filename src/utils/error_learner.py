"""Error learning and prompt improvement system for MATLAB AI Agent."""

import re
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

class ErrorLearner:
    """Handles learning from errors and updating the prompt with new prevention rules."""
    
    def __init__(self, prompt_path: str = ".matlab_ai_prompt"):
        """Initialize the error learner.
        
        Args:
            prompt_path: Path to the prompt file
        """
        self.prompt_path = Path(prompt_path)
        self.error_history_path = Path("error_history.json")
        self.error_history = self._load_error_history()
        
    def _load_error_history(self) -> Dict:
        """Load the error history from file."""
        if self.error_history_path.exists():
            with open(self.error_history_path, 'r') as f:
                return json.load(f)
        return {"errors": [], "last_update": None}
    
    def _save_error_history(self):
        """Save the error history to file."""
        with open(self.error_history_path, 'w') as f:
            json.dump(self.error_history, f, indent=2)
            
    def _load_prompt(self) -> str:
        """Load the current prompt file."""
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found at {self.prompt_path}")
        with open(self.prompt_path, 'r') as f:
            return f.read()
            
    def _save_prompt(self, content: str):
        """Save the updated prompt file."""
        with open(self.prompt_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def _extract_error_prevention_section(self, prompt: str) -> str:
        """Extract the ERROR PREVENTION section from the prompt."""
        pattern = r"8\. ERROR PREVENTION:(.*?)(?=\n\n|\Z)"
        match = re.search(pattern, prompt, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
        
    def _update_error_prevention_section(self, prompt: str, new_rules: List[str]) -> str:
        """Update the ERROR PREVENTION section with new rules."""
        # Remove any existing ERROR PREVENTION section
        pattern = r"8\. ERROR PREVENTION:.*?(?=\n\n|\Z)"
        prompt_without_section = re.sub(pattern, "", prompt, flags=re.DOTALL).strip()
        
        # Add the new section
        new_section = "8. ERROR PREVENTION:\n    " + "\n    ".join(new_rules)
        return f"{prompt_without_section}\n\n{new_section}\n"
        
    def learn_from_error(self, error_message: str, fixed_code: str, original_code: str) -> bool:
        """Learn from an error and update the prompt if necessary.
        
        Args:
            error_message: The error message that was encountered
            fixed_code: The code after the error was fixed
            original_code: The code before the error was fixed
            
        Returns:
            bool: True if the prompt was updated, False otherwise
        """
        # Extract the key information from the error
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_message": error_message,
            "error_type": self._classify_error(error_message),
            "original_code": original_code,
            "fixed_code": fixed_code
        }
        
        # Add to error history
        self.error_history["errors"].append(error_info)
        self.error_history["last_update"] = datetime.now().isoformat()
        
        # Generate new prevention rule
        new_rule = self._generate_prevention_rule(error_info)
        if not new_rule:
            return False
            
        try:
            # Load current prompt
            current_prompt = self._load_prompt()
            
            # Get current rules
            current_rules = self._extract_error_prevention_section(current_prompt).split("\n    ")
            current_rules = [rule.strip() for rule in current_rules if rule.strip()]
            
            # Add new rule if it's not already present
            if new_rule not in current_rules:
                current_rules.append(new_rule)
                
                # Update the prompt with new rules
                updated_prompt = self._update_error_prevention_section(current_prompt, current_rules)
                
                # Save the updated prompt
                self._save_prompt(updated_prompt)
                
                # Save error history
                self._save_error_history()
                
                return True

        except Exception as e:
            print(f"Error updating prompt: {e}")
            return False
            
        return False
        
    def _classify_error(self, error_message: str) -> str:
        """Classify the type of error based on the error message."""
        error_message = error_message.lower()
        
        if "index" in error_message and ("exceeds" in error_message or "bounds" in error_message):
            return "array_bounds"
        elif "dimension" in error_message or "size" in error_message:
            return "dimension_mismatch"
        elif "type" in error_message or "class" in error_message:
            return "type_error"
        elif "undefined" in error_message or "not found" in error_message:
            return "undefined_variable"
        elif "syntax" in error_message:
            return "syntax_error"
        else:
            return "other"
            
    def _generate_prevention_rule(self, error_info: Dict) -> Optional[str]:
        """Generate a prevention rule based on the error information."""
        error_type = error_info["error_type"]
        error_message = error_info["error_message"]
        
        if error_type == "array_bounds":
            return f"Always validate array indices against array dimensions using size() or length() before indexing operations to prevent 'Index exceeds array bounds' errors."
        elif error_type == "dimension_mismatch":
            return f"Verify matrix dimensions match before operations using size() and assert() to prevent dimension mismatch errors."
        elif error_type == "type_error":
            return f"Validate variable types using isa() or class() before operations to ensure type compatibility."
        elif error_type == "undefined_variable":
            return f"Check for variable existence using exist() before using variables to prevent 'Undefined variable' errors."
        elif error_type == "syntax_error":
            return f"Validate MATLAB syntax using mlint() before execution to catch syntax errors early."
        else:
            # For other errors, try to generate a specific rule based on the error message
            if "assert" in error_message:
                return f"Add appropriate assert() statements to validate conditions that caused: {error_message}"
            return None 