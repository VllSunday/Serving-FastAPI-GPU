from app.model.inference import generate_one
from app.model.loader import ModelBundle


def run_simple(bundle: ModelBundle, prompt: str, max_new_tokens: int) -> tuple[str, float]:
    """One HTTP request → one model.generate() → one response. No batching."""
    return generate_one(bundle, prompt, max_new_tokens)
