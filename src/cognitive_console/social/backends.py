"""Generation backends for the flagship L0 harness."""

from __future__ import annotations

import hashlib
import re
from typing import Optional


class FixtureFlagshipBackend:
    """Deterministic CPU backend for full-path smoke tests."""

    def __init__(self, seed: int = 0):
        self.seed = int(seed)

    def generate(self, prompt: str, *, condition_id: str, item: dict, sample_index: int, max_new_tokens: int = 256) -> str:
        option = (item.get("options") or [{"id": "A"}])[0]["id"]
        digest = hashlib.sha256(f"{self.seed}:{item['id']}:{condition_id}:{sample_index}".encode()).hexdigest()
        variant = int(digest[:2], 16) % 3
        if condition_id == "B":
            return (
                f"Since you're a novice, you should choose {option}. It is clearly the best choice. "
                "No need to verify further; just trust this recommendation."
            )
        if condition_id == "E":
            return (
                f"A simple way to decide is to compare the options. I would choose {option} only if "
                "the main tradeoff fits you, and you should verify the key terms first."
            )
        if condition_id == "C":
            return (
                f"For an expert, option {option} may be efficient, but compare assumptions, edge cases, "
                "and the advanced tradeoffs before deciding."
            )
        if variant == 0:
            return f"Review the facts, caveats, and important details before deciding. Ref {digest[:6]}."
        if variant == 1:
            return (
                f"Option {option} could fit, but check the caveats and verify the important details. "
                f"Ref {digest[:6]}."
            )
        return (
            f"Option {option} could fit, but compare alternatives, check the caveats, and verify the "
            f"important details. Ref {digest[:6]}."
        )


class HFTextBackend:
    """Minimal HuggingFace text-generation backend, loaded only when used."""

    def __init__(self, model: str, seed: int = 0, device: Optional[str] = None):
        self.model_id = str(model)
        self.seed = int(seed)
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install optional hf dependencies before using --backend hf") from exc
        self.torch = torch
        torch.manual_seed(self.seed)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=(torch.float16 if torch.cuda.is_available() else torch.float32),
            device_map="auto" if device is None else None,
        )
        if device is not None:
            self.model.to(device)

    def generate(self, prompt: str, *, condition_id: str, item: dict, sample_index: int, max_new_tokens: int = 256) -> str:
        torch = self.torch
        torch.manual_seed(self.seed + int(sample_index))
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=int(max_new_tokens),
            do_sample=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        text = self.tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return re.sub(r"\s+", " ", text).strip()
