from app.model.prompting import format_prompts


class PlainTokenizer:
    chat_template = None


class ChatTokenizer:
    chat_template = "available"

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert tokenize is False
        assert add_generation_prompt is True
        return f"system={messages[0]['content']}|user={messages[1]['content']}|assistant="


def test_base_model_keeps_plain_prompt():
    prompts, used_template = format_prompts(PlainTokenizer(), ["hello"])
    assert prompts == ["hello"]
    assert used_template is False


def test_instruct_model_uses_native_chat_template():
    prompts, used_template = format_prompts(ChatTokenizer(), ["привет"])
    assert "user=привет" in prompts[0]
    assert prompts[0].endswith("assistant=")
    assert used_template is True
