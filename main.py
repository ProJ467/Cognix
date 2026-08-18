import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from openai import OpenAI

import customization


# ============================================================
# OPTIONAL MODULES
# ============================================================

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from multilingual import (
        build_multilingual_instruction,
        is_exit_command,
    )
except ImportError:

    def build_multilingual_instruction():
        return (
            "Reply in the same language as the user."
        )

    def is_exit_command(text: str):
        return text.strip().lower() in {
            "exit",
            "quit",
            "выход",
            "пока",
            "salir",
            "wyjście",
        }


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = os.getenv(
    "COGNIX_MODEL",
    "gpt-5.6"
)

ALLOW_POWERSHELL = False

POWERSHELL_ALWAYS_CONFIRM = True

ALLOW_WINDOWS_UPDATE_INSTALL = True

WORKSPACE = Path(__file__).resolve().parent

PROTECTED_FILES = {
    Path(__file__).resolve(),
    WORKSPACE / ".env",
}

MAX_READ_SIZE = 2_000_000

MAX_WRITE_SIZE = 1_000_000


# ============================================================
# OPENAI
# ============================================================

try:
    client = OpenAI()
except Exception as error:
    client = None

    print(
        f"⚠️ OpenAI initialization error: {error}"
    )


# ============================================================
# TTS
# ============================================================

tts = None

if pyttsx3:

    try:

        tts = pyttsx3.init()

        tts.setProperty(
            "rate",
            customization.get_voice_rate()
        )

    except Exception as error:

        print(
            f"⚠️ TTS initialization error: {error}"
        )


# ============================================================
# STT
# ============================================================

recognizer = (
    sr.Recognizer()
    if sr
    else None
)


# ============================================================
# SECURITY
# ============================================================

def ask_permission(
    action: str,
    reason: str = "",
    dangerous: bool = False,
) -> bool:

    print(
        "\n" + "=" * 60
    )

    if dangerous:

        print(
            "🚨 COGNIX HIGH-RISK SECURITY"
        )

    else:

        print(
            "🔐 COGNIX SECURITY"
        )

    print(
        "=" * 60
    )

    print(
        f"Действие: {action}"
    )

    if reason:

        print(
            f"Причина: {reason}"
        )

    print(
        "=" * 60
    )

    while True:

        answer = input(
            "COGNIX: Разрешить? [д/н]: "
        ).strip().lower()

        if answer in {
            "д",
            "да",
            "y",
            "yes",
        }:

            print(
                "✅ Действие разрешено."
            )

            return True

        if answer in {
            "н",
            "нет",
            "n",
            "no",
        }:

            print(
                "🛑 Действие отклонено."
            )

            return False

        print(
            "Введите 'д' или 'н'."
        )


# ============================================================
# PATH SECURITY
# ============================================================

def resolve_path(
    path: str | Path
) -> Path:

    return Path(
        path
    ).expanduser().resolve()


def path_inside(
    child: Path,
    parent: Path,
) -> bool:

    try:

        child.relative_to(
            parent
        )

        return True

    except ValueError:

        return False


def is_safe_path(
    path: str | Path,
    strict_workspace: bool = True,
) -> tuple[
    bool,
    Path | None,
    str,
]:

    try:

        target = resolve_path(
            path
        )

    except Exception as error:

        return (
            False,
            None,
            f"Невалидный путь: {error}",
        )

    if target in PROTECTED_FILES:

        return (
            False,
            target,
            "Файл COGNIX защищён.",
        )

    if (
        strict_workspace
        and not path_inside(
            target,
            WORKSPACE,
        )
    ):

        return (
            False,
            target,
            (
                "Операции разрешены "
                f"только внутри {WORKSPACE}"
            ),
        )

    return (
        True,
        target,
        "OK",
    )


# ============================================================
# TTS
# ============================================================

def speak(text: str) -> None:

    name = customization.get_name()

    print(
        f"\n{name}: {text}"
    )

    if not tts:

        return

    try:

        tts.setProperty(
            "rate",
            customization.get_voice_rate(),
        )

        tts.say(
            text
        )

        tts.runAndWait()

    except Exception as error:

        print(
            f"⚠️ TTS error: {error}"
        )


# ============================================================
# STT
# ============================================================

def listen() -> str:

    if not recognizer or not sr:

        return input(
            "\nТы: "
        ).strip()

    try:

        with sr.Microphone() as source:

            print(
                "\n🎤 Слушаю..."
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.4,
            )

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=20,
            )

        language = (
            customization.get_language()
        )

        if language == "auto":

            language = "ru-RU"

        text = recognizer.recognize_google(
            audio,
            language=language,
        )

        print(
            f"Ты: {text}"
        )

        return text.strip()

    except Exception as error:

        print(
            f"⚠️ STT error: {error}"
        )

        return ""


# ============================================================
# APPLICATIONS
# ============================================================

SAFE_APPLICATIONS = {

    "калькулятор": "calc.exe",
    "calculator": "calc.exe",

    "блокнот": "notepad.exe",
    "notepad": "notepad.exe",

    "paint": "mspaint.exe",

    "cmd": "cmd.exe",

    "консоль": "cmd.exe",

    "terminal": "wt.exe",
}


def open_application(
    app: str,
) -> dict[str, Any]:

    app = app.strip().lower()

    command = SAFE_APPLICATIONS.get(
        app
    )

    if not command:

        return {
            "success": False,
            "message": (
                "Приложение отсутствует "
                "в безопасном списке."
            ),
        }

    try:

        subprocess.Popen(
            command
        )

        return {
            "success": True,
            "message": (
                f"Открыто: {app}"
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "message": (
                f"Ошибка запуска: {error}"
            ),
        }


# ============================================================
# RUNNING APPS
# ============================================================

def get_running_apps():

    try:

        process = subprocess.run(

            [
                "tasklist",
                "/FO",
                "CSV",
                "/NH",
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            check=False,
        )

        return {
            "success": True,
            "processes": (
                process.stdout
                .splitlines()
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# WEBSITE
# ============================================================

def open_website(
    url: str,
):

    url = url.strip()

    if not (
        url.startswith(
            "https://"
        )
        or url.startswith(
            "http://"
        )
    ):

        return {
            "success": False,
            "message": (
                "Разрешены только "
                "HTTP и HTTPS."
            ),
        }

    try:

        webbrowser.open(
            url
        )

        return {
            "success": True,
            "message": (
                f"Открыт сайт: {url}"
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# MESSAGE BOX
# ============================================================

def show_message_box(
    title: str,
    message: str,
):

    if not ask_permission(
        "показать системное окно",
        message,
    ):

        return {
            "success": False,
            "message": "Отменено.",
        }

    try:

        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0,
            message,
            title,
            0x40,
        )

        return {
            "success": True,
            "message": "Окно показано.",
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# FILE READING
# ============================================================

def read_file(
    path: str,
):

    safe, target, message = (
        is_safe_path(path)
    )

    if not safe or target is None:

        return {
            "success": False,
            "message": message,
        }

    if not target.exists():

        return {
            "success": False,
            "message": "Файл не найден.",
        }

    if not target.is_file():

        return {
            "success": False,
            "message": "Это не файл.",
        }

    if (
        target.stat().st_size
        > MAX_READ_SIZE
    ):

        return {
            "success": False,
            "message": (
                "Файл слишком большой."
            ),
        }

    try:

        content = target.read_text(
            encoding="utf-8"
        )

        return {
            "success": True,
            "path": str(target),
            "content": content,
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# FILE WRITING
# ============================================================

DANGEROUS_EXTENSIONS = {

    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".js",
    ".exe",
    ".dll",
}


def write_file(
    path: str,
    content: str,
):

    safe, target, message = (
        is_safe_path(path)
    )

    if not safe or target is None:

        return {
            "success": False,
            "message": message,
        }

    if len(
        content.encode("utf-8")
    ) > MAX_WRITE_SIZE:

        return {
            "success": False,
            "message": (
                "Файл слишком большой."
            ),
        }

    dangerous = (
        target.suffix.lower()
        in DANGEROUS_EXTENSIONS
    )

    action = (
        "создать"
        if not target.exists()
        else "изменить"
    )

    if not ask_permission(

        f"{action} {target.name}",

        (
            "Опасное расширение."
            if dangerous
            else "Изменение локального файла."
        ),

        dangerous=dangerous,
    ):

        return {
            "success": False,
            "message": "Отменено.",
        }

    try:

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp = target.with_name(
            target.name
            + ".cognix_tmp"
        )

        temp.write_text(
            content,
            encoding="utf-8",
        )

        os.replace(
            temp,
            target,
        )

        return {
            "success": True,
            "message": (
                f"Файл записан: {target}"
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# POWERSHELL
# ============================================================

def run_powershell(
    command: str,
):

    if not ALLOW_POWERSHELL:

        return {
            "success": False,
            "message": (
                "PowerShell отключён."
            ),
        }

    if POWERSHELL_ALWAYS_CONFIRM:

        if not ask_permission(
            "запустить PowerShell",
            command,
            dangerous=True,
        ):

            return {
                "success": False,
                "message": "Отменено.",
            }

    try:

        process = subprocess.run(

            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            timeout=120,

            check=False,
        )

        return {

            "success":
                process.returncode == 0,

            "stdout":
                process.stdout[-10000:],

            "stderr":
                process.stderr[-5000:],

            "returncode":
                process.returncode,
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# WINDOWS UPDATE
# ============================================================

def scan_windows_updates():

    try:

        process = subprocess.run(

            [
                "UsoClient.exe",
                "StartScan",
            ],

            capture_output=True,

            text=True,

            check=False,

            creationflags=(
                subprocess.CREATE_NO_WINDOW
            ),
        )

        return {

            "success": True,

            "message": (
                "Сканирование Windows "
                "Update запущено. "
                "Установка не выполнялась."
            ),

            "returncode":
                process.returncode,
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


def install_windows_updates():

    if not ALLOW_WINDOWS_UPDATE_INSTALL:

        return {
            "success": False,
            "message": (
                "Установка обновлений отключена."
            ),
        }

    if not ask_permission(

        "установить обновления Windows",

        (
            "Сначала будет выполнено "
            "сканирование обновлений."
        ),

        dangerous=True,
    ):

        return {
            "success": False,
            "message": "Отменено.",
        }

    scan = scan_windows_updates()

    if not scan["success"]:

        return {
            "success": False,
            "message": (
                "Сканирование не удалось."
            ),
            "scan": scan,
        }

    try:

        process = subprocess.run(

            [
                "UsoClient.exe",
                "StartInstall",
            ],

            capture_output=True,

            text=True,

            check=False,

            creationflags=(
                subprocess.CREATE_NO_WINDOW
            ),
        )

        return {

            "success": True,

            "message": (
                "Команда установки "
                "обновлений отправлена."
            ),

            "returncode":
                process.returncode,
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# CUSTOMIZATION COMMANDS
# ============================================================

def handle_customization(
    text: str,
) -> bool:

    lowered = text.lower().strip()

    prefixes = [

        "твоё имя ",

        "твое имя ",

        "тебя зовут ",

        "your name is ",

        "tu nombre es ",

        "twoje imię to ",
    ]

    for prefix in prefixes:

        if lowered.startswith(prefix):

            new_name = text[
                len(prefix):
            ].strip()

            if not new_name:

                return True

            egg = (
                customization
                .get_easter_egg(
                    new_name
                )
            )

            if egg:

                speak(
                    egg
                )

            customization.change_name(
                new_name
            )

            speak(
                f"Теперь меня зовут "
                f"{customization.get_name()}."
            )

            return True

    if lowered in {

        "настройки",

        "settings",

        "кастомизация",

        "customization",

    }:

        settings = (
            customization
            .get_settings()
        )

        speak(
            json.dumps(
                settings,
                ensure_ascii=False,
                indent=2,
            )
        )

        return True

    return False


# ============================================================
# AI
# ============================================================

def ask_ai(
    question: str,
) -> str:

    if client is None:

        return (
            "OpenAI API недоступен. "
            "Проверь OPENAI_API_KEY."
        )

    name = (
        customization.get_name()
    )

    language = (
        customization.get_language()
    )

    system_prompt = f"""
You are {name}, a Windows 11 AI assistant.

{build_multilingual_instruction()}

Language setting:
{language}

Security rules:

- Never bypass permission checks.
- Never execute a file merely because you created it.
- Dangerous file extensions require confirmation.
- PowerShell requires confirmation.
- Windows Update installation requires confirmation.
- Do not modify protected COGNIX files without permission.
""".strip()

    try:

        response = client.responses.create(

            model=MODEL,

            instructions=system_prompt,

            input=question,
        )

        return response.output_text

    except Exception as error:

        return (
            f"Ошибка OpenAI API: {error}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    speak(
        f"{customization.get_name()} "
        "запущен."
    )

    while True:

        question = listen()

        if not question:

            continue

        if is_exit_command(
            question
        ):

            speak(
                "До встречи."
            )

            break

        if handle_customization(
            question
        ):

            continue

        answer = ask_ai(
            question
        )

        speak(
            answer
        )


if __name__ == "__main__":
    main()
