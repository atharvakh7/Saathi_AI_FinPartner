"""Prompt templates (`*.md` in this folder) with `{{name}}` placeholders.

`render("fraud_explain", language_name="Hindi", ...)` fails loudly on a missing value, so a
template and its caller can't silently drift apart. Untrusted text (user messages, pasted
scam messages) must go through `fence()` before it is placed in a template (spec §8.2).
"""

import re
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
_PLACEHOLDER = re.compile(r"{{\s*(\w+)\s*}}")

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "mr": "Marathi (Devanagari script)",
    "ta": "Tamil (Tamil script)",
}


@lru_cache
def _template(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"prompt template '{name}' not found")
    return path.read_text(encoding="utf-8").strip()


def placeholders(name: str) -> set[str]:
    return set(_PLACEHOLDER.findall(_template(name)))


def render(name: str, **values) -> str:
    template = _template(name)
    missing = placeholders(name) - values.keys()
    if missing:
        raise KeyError(f"prompt '{name}' is missing values for: {sorted(missing)}")
    return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), template)


def fence(text: str, tag: str = "message") -> str:
    """Wrap untrusted text in <tag>…</tag>, removing any tags inside that could close it early."""
    cleaned = re.sub(rf"</?\s*{re.escape(tag)}\s*>", "", text, flags=re.IGNORECASE)
    return f"<{tag}>\n{cleaned}\n</{tag}>"


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, "English")
