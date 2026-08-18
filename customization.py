"""COGNIX customization module.

Keeps user-facing personalization separate from the core agent so updates to
main.py do not have to replace the existing security/tool implementation.
"""

import json
from pathlib import Path
from typing import Any

CONFIG_FILE = Path(__file__).resolve().parent / "cognix_config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "assistant_name": "Cognix",
    "assistant_prefix": "COGNIX",
    "language": "auto",
    "voice_rate": 175,
}

EASTER_EGGS = {
    "санс": "Ты чего? Хочешь превратить меня в Undertale? 💀",
    "sans": "Ты чего? Хочешь превратить меня в Undertale? 💀",
    "джарвис": "Режим Джарвиса активирован.",
    "jarvis": "Режим Джарвиса активирован.",
    "окей гугл": "Я не Google, но ладно. 😎",
    "okay google": "Я не Google, но ладно. 😎",
    "кортана": "Кортана? Теперь у меня новое имя.",
    "cortana": "Кортана? Теперь у меня новое имя.",
}


def load_config() -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()

    if not CONFIG_FILE.exists():
        return config

    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            config.update(data)
    except (OSError, json.JSONDecodeError):
        pass

    return config


def save_config(config: dict[str, Any]) -> bool:
    try:
        CONFIG_FILE.write_text(
            json.dumps(config, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def get_settings() -> dict[str, Any]:
    return load_config()


def change_name(new_name: str) -> str:
    config = load_config()
    new_name = new_name.strip()

    if not new_name:
        return str(config["assistant_name"])

    config["assistant_name"] = new_name
    save_config(config)
    return new_name


def change_language(language: str) -> str:
    config = load_config()
    language = language.strip()

    if language:
        config["language"] = language
        save_config(config)

    return str(config["language"])


def change_voice_rate(rate: int) -> int:
    config = load_config()
    rate = max(80, min(300, int(rate)))
    config["voice_rate"] = rate
    save_config(config)
    return rate


def customize(
    name: str | None = None,
    prefix: str | None = None,
    language: str | None = None,
    voice_rate: int | None = None,
) -> dict[str, Any]:
    config = load_config()

    if name is not None and name.strip():
        config["assistant_name"] = name.strip()

    if prefix is not None and prefix.strip():
        config["assistant_prefix"] = prefix.strip()

    if language is not None and language.strip():
        config["language"] = language.strip()

    if voice_rate is not None:
        config["voice_rate"] = max(80, min(300, int(voice_rate)))

    save_config(config)
    return config


def get_easter_egg(name: str) -> str | None:
    return EASTER_EGGS.get(name.strip().lower())


def process_name_command(text: str) -> tuple[bool, str | None, str | None]:
    """Return (matched, new_name, easter_egg_message)."""
    prefixes = (
        "твоё имя ",
        "твое имя ",
        "тебя зовут ",
        "your name is ",
        "tu nombre es ",
        "twoje imię to ",
    )

    lowered = text.strip().lower()

    for prefix in prefixes:
        if lowered.startswith(prefix):
            name = text.strip()[len(prefix):].strip()
            if not name:
                return True, None, None
            return True, name, get_easter_egg(name)

    return False, None, None
