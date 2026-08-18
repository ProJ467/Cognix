"""Multilingual helpers for COGNIX.

COGNIX sends the user's original language to the AI model instead of forcing
commands through a hard-coded Russian/English parser. This module provides
small helpers for confirmations, exit phrases, and language hints.
"""

from __future__ import annotations

import re
from typing import Final


LANGUAGE_HINTS: Final[dict[str, tuple[str, ...]]] = {
    "ru": ("рус", "россий", "russian"),
    "en": ("english", "англ"),
    "es": ("español", "espanol", "spanish", "испан"),
    "de": ("deutsch", "german", "немец"),
    "fr": ("français", "francais", "french", "француз"),
    "it": ("italiano", "italian", "итальян"),
    "pt": ("português", "portugues", "portuguese", "португал"),
    "pl": ("polski", "polish", "польск"),
    "uk": ("україн", "ukrainian", "украин"),
}

YES_WORDS: Final[set[str]] = {
    "yes", "y", "да", "д", "sí", "si", "oui", "ja", "tak", "так",
    "sim", "ano", "давай", "ok", "okay", "sure", "confirm", "confirmed",
}

NO_WORDS: Final[set[str]] = {
    "no", "n", "нет", "н", "non", "nein", "nie", "não", "nao",
    "cancel", "cancelled", "cancelar", "annuler", "abbrechen",
}

EXIT_PHRASES: Final[set[str]] = {
    "exit", "quit", "goodbye", "bye", "salir", "adiós", "adios",
    "au revoir", "auf wiedersehen", "beenden", "wyjdź", "wyjdz",
    "выход", "пока", "закрой себя", "выйди",
}


def normalize_text(text: str) -> str:
    """Normalize user input without translating it."""
    return re.sub(r"\s+", " ", text.strip()).casefold()


def parse_confirmation(text: str) -> bool | None:
    """Return True/False for common multilingual confirmations, else None."""
    normalized = normalize_text(text)
    if normalized in YES_WORDS:
        return True
    if normalized in NO_WORDS:
        return False
    return None


def is_exit_command(text: str) -> bool:
    """Recognize common exit phrases in several languages."""
    normalized = normalize_text(text)
    return normalized in EXIT_PHRASES


def language_hint(text: str) -> str | None:
    """Return a coarse language hint when the user explicitly mentions a language."""
    normalized = normalize_text(text)
    for language, hints in LANGUAGE_HINTS.items():
        if any(hint in normalized for hint in hints):
            return language
    return None


def build_multilingual_instruction() -> str:
    """Instruction intended for the AI agent's system/developer prompt."""
    return (
        "Understand the user's request in the language they use. "
        "Reply in the same language unless the user asks for another language. "
        "Preserve filenames, paths, URLs, application names, commands, and code exactly. "
        "Never bypass COGNIX permission gates because the request is multilingual."
    )
