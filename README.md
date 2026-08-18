# 🤖 COGNIX

**COGNIX** is an AI-powered personal assistant for **Windows 11**, designed as a modern alternative to Cortana.

> 🧠 Your AI. Your Windows. Your rules.

## ✨ What is COGNIX?

COGNIX is a Python-based AI agent that can understand requests and use Windows tools to perform actions on your computer.

The goal is simple: build a personal Windows assistant that can do more than just answer questions.

## 🚀 Features

- 🧠 AI-powered conversations
- 🚀 Launch applications
- 🎵 Play, pause and stop music
- 🌐 Open websites
- 💬 Show Windows message boxes
- 📋 Get running applications/processes
- 📂 Read local files
- ✏️ Write and update files
- 📜 Create scripts with permission checks
- ⚡ PowerShell integration
- 🔄 Scan Windows Update
- 🪟 Install Windows updates with confirmation
- 🗃️ Remember application paths using `app_paths.json`
- 🔐 Permission and security system
- 🎤 Speech-to-Text support planned/in development
- 🔊 Text-to-Speech support planned/in development

## 🛡️ Security

COGNIX separates **AI decisions** from **actual computer actions**.

The AI can request a tool, but the Python security layer decides whether that action can be executed.

Potentially dangerous operations can require explicit user confirmation, including:

- PowerShell commands
- Windows Update installation
- File modification
- Script execution
- Other system-level operations

The idea is that COGNIX should ask before doing something that could significantly affect Windows or your files.

## 📦 Application Registry

COGNIX can remember where applications are installed using `app_paths.json`.

Example:

```json
{
    "steam": "C:\\Program Files (x86)\\Steam\\steam.exe",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
```

This allows commands such as:

```text
Open Steam
Open Chrome
Open VS Code
```

to use the saved application paths instead of hard-coding every application into the main program.

## 🪟 Windows 11

COGNIX is primarily designed for **Windows 11** and uses Windows-compatible tools and commands.

## 🐍 Built With

- Python
- OpenAI API
- Windows subprocess tools
- JSON
- Speech recognition / TTS components

## 🚧 Development

COGNIX is an actively developed project. Features may change as the agent becomes more capable.

The long-term goal is to create a powerful personal AI agent for Windows 11 that can understand natural language, control applications, interact with system tools and safely ask for permission when needed.

## 🎯 Vision

**COGNIX is intended to be a modern, customizable alternative to Cortana for Windows 11.**

Not just a chatbot.

An agent that can actually work with your computer. 🤖🖥️

---

**Made by ProJ467**
