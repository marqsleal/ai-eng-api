from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
SYSTEM_PROMPT_FILE = PROMPTS_DIR / "system_prompt.md"
GENERAL_INSTRUCTIONS_FILE = PROMPTS_DIR / "general_instructions.md"
