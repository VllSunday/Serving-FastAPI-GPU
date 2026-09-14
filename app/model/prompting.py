from __future__ import annotations

from transformers import PreTrainedTokenizerBase

from app.config import settings


def format_prompts(
    tokenizer: PreTrainedTokenizerBase,
    prompts: list[str],
) -> tuple[list[str], bool]:
    """Render user prompts with the model's native chat template when present.

    Base models such as GPT-2 do not define a chat template, so tests and custom
    base-model configurations keep the original plain-text behavior.
    """
    if not getattr(tokenizer, "chat_template", None):
        return prompts, False

    formatted = [
        tokenizer.apply_chat_template(
            [
                {"role": "system", "content": settings.system_prompt},
                {"role": "user", "content": prompt},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        for prompt in prompts
    ]
    return formatted, True
