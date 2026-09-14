from __future__ import annotations

from transformers import PreTrainedTokenizerBase

from app.config import settings


def format_prompts(
    tokenizer: PreTrainedTokenizerBase,
    prompts: list[str],
) -> tuple[list[str], bool]:
    """Применяет родной chat template модели, если он есть.

    У базовых моделей вроде GPT-2 шаблона нет. Для них и для тестовых tokenizer
    сохраняем обычный plain text.
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
