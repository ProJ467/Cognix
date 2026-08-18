"""COGNIX entry point with memory command integration."""

import memory_commands

# Keep the complete original Cognix implementation in main_core.py.
from main_core import *  # noqa: F401,F403


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

        answer = ask_ai(question)
        speak(answer)


if __name__ == "__main__":
    main()
