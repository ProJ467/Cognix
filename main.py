"""COGNIX entry point with memory command integration."""

import json

import memory
import memory_commands
import main_core as core
from main_core import *  # noqa: F401,F403


# Keep the original security boundary correct after splitting the core out of main.py.
core.PROTECTED_FILES = {
    core.WORKSPACE / "main.py",
    core.WORKSPACE / "main_core.py",
    core.WORKSPACE / ".env",
}


def ask_ai(question: str) -> str:
    """Send the question to the original AI with current memory attached."""
    try:
        memory_data = memory.get_all()
    except Exception:
        memory_data = {"live": {}, "time": {}}

    memory_text = json.dumps(
        memory_data,
        ensure_ascii=False,
        indent=2,
    )

    prompt = (
        "Use the following Cognix memory as context when it is relevant. "
        "Do not claim to remember anything that is not present here.\n\n"
        f"COGNIX MEMORY:\n{memory_text}\n\n"
        f"USER QUESTION:\n{question}"
    )

    return core.ask_ai(prompt)


def main():
    speak(f"{customization.get_name()} запущен.")

    while True:
        question = listen()

        if not question:
            continue

        if is_exit_command(question):
            speak("До встречи.")
            break

        if handle_customization(question):
            continue

        handled, response = memory_commands.handle_memory_command(question)
        if handled:
            speak(response)
            continue

        speak(ask_ai(question))


if __name__ == "__main__":
    main()
