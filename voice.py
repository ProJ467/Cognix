"""COGNIX voice module: Speech-to-Text + Text-to-Speech for Windows."""

from __future__ import annotations

import speech_recognition as sr
import pyttsx3


class Voice:
    def __init__(self, language: str = "ru-RU", rate: int = 175) -> None:
        self.language = language
        self.recognizer = sr.Recognizer()
        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", rate)

    def speak(self, text: str) -> None:
        print(f"COGNIX: {text}")
        try:
            self.tts.say(text)
            self.tts.runAndWait()
        except Exception as error:
            print(f"TTS error: {error}")

    def listen(self, timeout: int = 10, phrase_time_limit: int = 20) -> str:
        try:
            with sr.Microphone() as source:
                print("🎤 Говори...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            text = self.recognizer.recognize_google(
                audio,
                language=self.language,
            )
            print(f"Ты: {text}")
            return text.strip()

        except sr.WaitTimeoutError:
            print("STT: время ожидания истекло.")
        except sr.UnknownValueError:
            print("STT: речь не распознана.")
        except sr.RequestError as error:
            print(f"STT: сервис распознавания недоступен: {error}")
        except Exception as error:
            print(f"STT error: {error}")

        return ""
