"""Natural-language memory commands for COGNIX.

Supported keywords:
    Live Memory [ПАМЯТЬ]: <key> = <value>
    Time Memory [ПАМЯТЬ] <seconds>: <key> = <value>
    Forget Memory [ПАМЯТЬ]: <key>
    Show Memory [ПАМЯТЬ]

Live Memory is permanent until explicitly forgotten.
Time Memory expires automatically.
"""

import re

import memory


LIVE_RE = re.compile(
    r"^live\s+memory\s*\[память\]\s*:\s*(.+)$",
    re.IGNORECASE,
)

TIME_RE = re.compile(
    r"^time\s+memory\s*\[память\]\s+(\d+)\s*(s|m|h|d)\s*:\s*(.+)$",
    re.IGNORECASE,
)

FORGET_RE = re.compile(
    r"^forget\s+memory\s*\[память\]\s*:\s*(.+)$",
    re.IGNORECASE,
)

SHOW_RE = re.compile(
    r"^show\s+memory\s*\[память\]\s*$",
    re.IGNORECASE,
)


def _split_assignment(value: str) -> tuple[str, str] | None:
    if "=" not in value:
        return None

    key, item = value.split("=", 1)
    key = key.strip()
    item = item.strip()

    if not key or not item:
        return None

    return key, item


def _seconds(amount: int, unit: str) -> int:
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
    }
    return amount * multipliers[unit.lower()]


def handle_memory_command(text: str) -> tuple[bool, str]:
    """Handle a COGNIX memory command.

    Returns (handled, response).
    """
    text = text.strip()

    match = LIVE_RE.match(text)
    if match:
        pair = _split_assignment(match.group(1))
        if pair is None:
            return True, "Формат: Live Memory [ПАМЯТЬ]: ключ = значение"

        key, value = pair
        ok = memory.set_live(key, value)
        return True, "Live Memory сохранена." if ok else "Не удалось сохранить Live Memory."

    match = TIME_RE.match(text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        pair = _split_assignment(match.group(3))
        if pair is None:
            return True, "Формат: Time Memory [ПАМЯТЬ] 2h: ключ = значение"

        key, value = pair
        ok = memory.set_time(key, value, _seconds(amount, unit))
        return True, "Time Memory сохранена." if ok else "Не удалось сохранить Time Memory."

    match = FORGET_RE.match(text)
    if match:
        key = match.group(1).strip()
        live_removed = memory.forget_live(key)
        time_removed = memory.forget_time(key)
        if live_removed and time_removed:
            return True, f"Память '{key}' удалена."
        return True, f"Запрос на удаление памяти '{key}' обработан."

    if SHOW_RE.match(text):
        data = memory.get_all()
        return True, str(data)

    return False, ""
