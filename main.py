import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from openai import OpenAI

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


# ============================================================
# COGNIX 0.03V
# Windows AI agent with explicit approval gates
# ============================================================

MODEL = os.getenv("COGNIX_MODEL", "gpt-5.6")
ALLOW_POWERSHELL = False
POWERSHELL_ALWAYS_CONFIRM = True
ALLOW_WINDOWS_UPDATE_INSTALL = True

WORKSPACE = Path(__file__).resolve().parent
PROTECTED_FILES = {
    Path(__file__).resolve(),
    WORKSPACE / ".env",
}

MAX_WRITE_SIZE = 1_000_000
MAX_READ_SIZE = 2_000_000

client = OpenAI()

# Optional voice support
recognizer = sr.Recognizer() if sr else None

tts = None
if pyttsx3:
    try:
        tts = pyttsx3.init()
        tts.setProperty("rate", 175)
    except Exception:
        tts = None


# ============================================================
# UI / VOICE
# ============================================================

def speak(text: str) -> None:
    print(f"\nCOGNIX: {text}")

    if tts is None:
        return

    try:
        tts.say(text)
        tts.runAndWait()
    except Exception as error:
        print(f"TTS error: {error}")


def listen() -> str:
    if recognizer is None or sr is None:
        return input("\nТы: ").strip()

    try:
        with sr.Microphone() as source:
            print("\n🎤 Говори...")
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)

        text = recognizer.recognize_google(audio, language="ru-RU")
        print(f"Ты: {text}")
        return text.strip()

    except Exception as error:
        print(f"STT: {error}")
        return ""


# ============================================================
# SECURITY
# ============================================================

def ask_permission(action: str, reason: str = "", dangerous: bool = False) -> bool:
    print("\n" + "=" * 64)
    print("🚨 HIGH-RISK SECURITY" if dangerous else "🔐 COGNIX SECURITY")
    print("=" * 64)
    print(f"Действие: {action}")
    if reason:
        print(f"Причина:  {reason}")
    print("=" * 64)

    while True:
        answer = input("Разрешить? [д/н]: ").strip().lower()
        if answer in {"д", "да", "y", "yes"}:
            print("✅ Разрешено.")
            return True
        if answer in {"н", "нет", "n", "no"}:
            print("🛑 Отклонено.")
            return False
        print("Введите д или н.")


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def path_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def is_safe_path(path: str | Path, strict_workspace: bool = True) -> tuple[bool, Path | None, str]:
    try:
        target = resolve_path(path)
    except Exception as error:
        return False, None, f"Невалидный путь: {error}"

    if target in PROTECTED_FILES:
        return False, target, "Файл защищён от изменения."

    if strict_workspace and not path_inside(target, WORKSPACE):
        return False, target, f"Путь должен находиться внутри workspace: {WORKSPACE}"

    return True, target, "OK"


def result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    return {"success": ok, "message": message, **extra}


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


# ============================================================
# WINDOWS TOOLS
# ============================================================

def open_application(app: str) -> dict[str, Any]:
    known = {
        "калькулятор": "calc.exe",
        "calculator": "calc.exe",
        "блокнот": "notepad.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "рисование": "mspaint.exe",
        "консоль": "cmd.exe",
        "cmd": "cmd.exe",
    }

    command = known.get(app.lower().strip())
    if not command:
        return result(False, "Неизвестное приложение. Разрешены только приложения из списка.")

    try:
        subprocess.Popen(command)
        return result(True, f"Запущено: {app}")
    except Exception as error:
        return result(False, f"Ошибка запуска: {error}")


def close_application(app: str) -> dict[str, Any]:
    if not ask_permission(f"закрыть приложение '{app}'", "Закрытие процесса может привести к потере несохранённых данных."):
        return result(False, "Пользователь отменил действие.")

    process_map = {
        "стим": "steam.exe",
        "steam": "steam.exe",
        "блокнот": "notepad.exe",
        "notepad": "notepad.exe",
        "калькулятор": "CalculatorApp.exe",
        "calculator": "CalculatorApp.exe",
    }

    process = process_map.get(app.lower().strip())
    if not process:
        return result(False, "Это приложение отсутствует в безопасном списке.")

    try:
        subprocess.run(["taskkill", "/IM", process, "/T"], check=False, capture_output=True, text=True)
        return result(True, f"Команда закрытия отправлена для {app}.")
    except Exception as error:
        return result(False, f"Ошибка: {error}")


def open_website(url: str) -> dict[str, Any]:
    if not (url.startswith("https://") or url.startswith("http://")):
        return result(False, "Разрешены только http:// и https:// сайты.")

    try:
        webbrowser.open(url)
        return result(True, f"Открыт сайт: {url}")
    except Exception as error:
        return result(False, f"Ошибка браузера: {error}")


def play_music(path: str) -> dict[str, Any]:
    safe, target, message = is_safe_path(path)
    if not safe or target is None:
        return result(False, message)
    if not target.exists() or not target.is_file():
        return result(False, "Музыкальный файл не найден.")

    try:
        os.startfile(str(target))
        return result(True, f"Открыт музыкальный файл: {target.name}")
    except Exception as error:
        return result(False, f"Ошибка воспроизведения: {error}")


def media_key(key: str) -> dict[str, Any]:
    # Uses PowerShell only for the Windows media-key action.
    # It is NOT arbitrary PowerShell execution.
    keys = {
        "play_pause": "0xB3",
        "stop": "0xB2",
        "next": "0xB0",
        "previous": "0xB1",
    }
    value = keys.get(key)
    if not value:
        return result(False, "Неизвестная медиа-команда.")

    script = f"$w=Add-Type -MemberDefinition '[DllImport(\"user32.dll\")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);' -Name K -Namespace C -PassThru; [C.K]::keybd_event({value},0,0,[UIntPtr]::Zero); [C.K]::keybd_event({value},0,2,[UIntPtr]::Zero)"
    try:
        subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        return result(True, f"Media action: {key}")
    except Exception as error:
        return result(False, f"Ошибка медиа-команды: {error}")


def show_message_box(title: str, message: str) -> dict[str, Any]:
    if not ask_permission("показать системное окно Windows", message):
        return result(False, "Пользователь отменил действие.")

    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
        return result(True, "Окно показано.")
    except Exception as error:
        return result(False, f"Ошибка MessageBox: {error}")


def get_running_apps() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        return result(True, "Список процессов получен.", processes=lines[:150])
    except Exception as error:
        return result(False, f"Ошибка tasklist: {error}")


# ============================================================
# FILE TOOLS
# ============================================================

def read_file(path: str) -> dict[str, Any]:
    safe, target, message = is_safe_path(path)
    if not safe or target is None:
        return result(False, message)
    if not target.exists() or not target.is_file():
        return result(False, "Файл не найден.")
    if target.stat().st_size > MAX_READ_SIZE:
        return result(False, "Файл слишком большой для безопасного чтения.")

    try:
        return result(True, "Файл прочитан.", path=str(target), content=target.read_text(encoding="utf-8"))
    except Exception as error:
        return result(False, f"Ошибка чтения: {error}")


def write_file(path: str, content: str) -> dict[str, Any]:
    safe, target, message = is_safe_path(path)
    if not safe or target is None:
        return result(False, message)

    if len(content.encode("utf-8")) > MAX_WRITE_SIZE:
        return result(False, "Файл слишком большой.")

    suffix = target.suffix.lower()
    dangerous_script = suffix in {".ps1", ".bat", ".cmd", ".vbs", ".js", ".exe", ".dll"}

    if not ask_permission(
        f"{'создать' if not target.exists() else 'изменить'} файл '{target.name}'",
        f"Тип файла: {suffix or 'без расширения'}",
        dangerous=dangerous_script,
    ):
        return result(False, "Пользователь отменил запись.")

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".cognix_tmp")
        temp.write_text(content, encoding="utf-8")
        os.replace(temp, target)
        return result(True, f"Файл записан: {target}")
    except Exception as error:
        return result(False, f"Ошибка записи: {error}")


# ============================================================
# POWERSHELL
# ============================================================

def run_powershell(command: str) -> dict[str, Any]:
    if not ALLOW_POWERSHELL:
        return result(False, "PowerShell-инструмент отключён настройкой ALLOW_POWERSHELL=False.")

    if POWERSHELL_ALWAYS_CONFIRM and not ask_permission(
        "выполнить PowerShell",
        command,
        dangerous=True,
    ):
        return result(False, "PowerShell отклонён пользователем.")

    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        return result(
            completed.returncode == 0,
            "PowerShell выполнен." if completed.returncode == 0 else "PowerShell завершился с ошибкой.",
            stdout=completed.stdout[-10000:],
            stderr=completed.stderr[-5000:],
            returncode=completed.returncode,
        )
    except subprocess.TimeoutExpired:
        return result(False, "PowerShell превысил лимит времени.")
    except Exception as error:
        return result(False, f"Ошибка PowerShell: {error}")


# ============================================================
# WINDOWS UPDATE
# ============================================================

def scan_windows_updates() -> dict[str, Any]:
    """Only starts Windows Update scanning. It does not install anything."""
    try:
        completed = subprocess.run(
            ["UsoClient.exe", "StartScan"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result(
            True,
            "Сканирование Windows Update запущено. Установка не выполнялась.",
            returncode=completed.returncode,
        )
    except FileNotFoundError:
        return result(False, "UsoClient.exe не найден. Это должно выполняться на Windows 10/11.")
    except Exception as error:
        return result(False, f"Ошибка сканирования обновлений: {error}")


def install_windows_updates() -> dict[str, Any]:
    if not ALLOW_WINDOWS_UPDATE_INSTALL:
        return result(False, "Установка Windows Update отключена настройкой безопасности.")

    if not ask_permission(
        "установить обновления Windows",
        "Перед установкой COGNIX должен сначала выполнить сканирование.",
        dangerous=True,
    ):
        return result(False, "Установка обновлений отменена.")

    scan = scan_windows_updates()
    if not scan["success"]:
        return result(False, "Не удалось запустить предварительное сканирование.", scan=scan)

    # Встроенный клиент Windows Update запускает установку найденных обновлений.
    try:
        completed = subprocess.run(
            ["UsoClient.exe", "StartInstall"],
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result(
            True,
            "Команда установки Windows Update отправлена. Windows может запросить перезагрузку.",
            returncode=completed.returncode,
        )
    except Exception as error:
        return result(False, f"Ошибка установки обновлений: {error}")


# ============================================================
# AGENT TOOLS
# ============================================================

TOOLS = [
    {
        "type": "function",
        "name": "open_application",
        "description": "Открывает безопасное приложение Windows из списка.",
        "parameters": {"type": "object", "properties": {"app": {"type": "string"}}, "required": ["app"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "close_application",
        "description": "Закрывает известное приложение Windows после подтверждения пользователя.",
        "parameters": {"type": "object", "properties": {"app": {"type": "string"}}, "required": ["app"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_running_apps",
        "description": "Получает список запущенных процессов Windows.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "play_music",
        "description": "Открывает локальный музыкальный файл внутри workspace.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "media_key",
        "description": "Управляет воспроизведением: play_pause, stop, next или previous.",
        "parameters": {"type": "object", "properties": {"key": {"type": "string", "enum": ["play_pause", "stop", "next", "previous"]}}, "required": ["key"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "open_website",
        "description": "Открывает HTTP или HTTPS сайт в браузере.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "show_message_box",
        "description": "Показывает системное окно Windows после подтверждения.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}}, "required": ["title", "message"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Читает UTF-8 текстовый файл только внутри Cognix workspace.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Создаёт или изменяет файл внутри Cognix workspace. Опасные расширения требуют подтверждения.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "run_powershell",
        "description": "Выполняет PowerShell только если ALLOW_POWERSHELL=True и пользователь подтвердил действие.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "scan_windows_updates",
        "description": "Запускает сканирование Windows Update без установки обновлений.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "install_windows_updates",
        "description": "Запрашивает подтверждение, запускает предварительное сканирование и затем просит Windows начать установку обновлений.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
]

TOOL_FUNCTIONS = {
    "open_application": open_application,
    "close_application": close_application,
    "get_running_apps": get_running_apps,
    "play_music": play_music,
    "media_key": media_key,
    "open_website": open_website,
    "show_message_box": show_message_box,
    "read_file": read_file,
    "write_file": write_file,
    "run_powershell": run_powershell,
    "scan_windows_updates": scan_windows_updates,
    "install_windows_updates": install_windows_updates,
}


SYSTEM_PROMPT = """
Ты COGNIX, локальный Windows AI-агент.
Отвечай по-русски, кратко и понятно.
Ты можешь выполнять действия только через предоставленные tools.
Никогда не притворяйся, что действие выполнено, если tool вернул ошибку.
Не выполняй PowerShell без соответствующего tool и его защитных проверок.
Для изменения Windows, запуска программ, закрытия приложений и опасных действий уважай подтверждения Python.
Если пользователь просит создать .ps1, это разрешено через write_file, но Python всё равно покажет подтверждение.
Создание файла и выполнение файла являются разными действиями.
Не проси пользователя раскрывать API-ключ.
""".strip()


# ============================================================
# AGENT LOOP
# ============================================================

def run_agent(user_text: str) -> str:
    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_text,
        tools=TOOLS,
    )

    # Agent loop: model can call several tools in sequence.
    for _ in range(8):
        calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]

        if not calls:
            return response.output_text or "Я не получил текстового ответа."

        outputs = []

        for call in calls:
            name = call.name
            arguments = json.loads(call.arguments or "{}")

            print("\n🧠 [COGNIX AGENT]")
            print(f"  Action: {name}")
            print(f"  Arguments: {json_text(arguments)}")

            function = TOOL_FUNCTIONS.get(name)
            if function is None:
                tool_result = result(False, f"Неизвестный tool: {name}")
            else:
                try:
                    tool_result = function(**arguments)
                except Exception as error:
                    tool_result = result(False, f"Ошибка tool '{name}': {error}")

            print(f"  Result: {json_text(tool_result)[:3000]}")

            outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json_text(tool_result),
            })

        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            previous_response_id=response.id,
            input=outputs,
            tools=TOOLS,
        )

    return "Я остановил цепочку действий: достигнут безопасный лимит шагов."


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Не найдена переменная OPENAI_API_KEY.")
        print("Установи API-ключ в переменную окружения и запусти программу снова.")
        return

    print("=" * 64)
    print("🤖 COGNIX 0.03V")
    print(f"🧠 Model: {MODEL}")
    print("🔐 PowerShell:", "ON + confirmation" if ALLOW_POWERSHELL else "OFF")
    print("📁 Workspace:", WORKSPACE)
    print("=" * 64)

    speak("COGNIX запущен.")

    while True:
        try:
            user_text = listen()
            if not user_text:
                continue

            if user_text.lower() in {"выход", "выйди", "закройся", "пока"}:
                speak("До встречи.")
                break

            answer = run_agent(user_text)
            speak(answer)

        except KeyboardInterrupt:
            print("\nCOGNIX остановлен.")
            break
        except Exception as error:
            print(f"\n❌ Ошибка агента: {error}")


if __name__ == "__main__":
    main()
