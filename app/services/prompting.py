from pathlib import Path

from app.core.globals import GENERAL_INSTRUCTIONS_FILE, SYSTEM_PROMPT_FILE


def _read_prompt_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_final_prompt(
    *,
    user_prompt: str,
    system_instruction: str | None = None,
    context: str | None = None,
) -> str:
    segments: list[str] = []
    base_system_prompt = _read_prompt_file(SYSTEM_PROMPT_FILE)
    if base_system_prompt:
        segments.append(base_system_prompt)

    if system_instruction:
        segments.append(system_instruction.strip())

    general_instructions = _read_prompt_file(GENERAL_INSTRUCTIONS_FILE)
    if general_instructions:
        segments.append(general_instructions)

    if context:
        segments.append(f"Context:\n{context.strip()}")

    segments.append(user_prompt.strip())
    return "\n\n".join(segments)
