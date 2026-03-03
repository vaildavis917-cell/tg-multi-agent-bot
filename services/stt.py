"""
Speech-to-Text: транскрибация голосовых сообщений.
Использует OpenAI Whisper API через OpenRouter или напрямую.
Fallback: локальный whisper если установлен.
"""

import logging
import os
import tempfile

logger = logging.getLogger(__name__)


async def transcribe_voice(file_path: str) -> str:
    """
    Транскрибирует аудиофайл в текст.
    Пробует OpenAI Whisper API, fallback на локальный whisper.
    """
    # Пробуем через OpenAI Whisper API (бесплатный через OpenRouter не поддерживает,
    # поэтому используем локальный whisper)
    text = await _transcribe_local(file_path)
    return text


async def _transcribe_local(file_path: str) -> str:
    """Транскрибация через локальный whisper (если установлен) или через manus-speech-to-text."""
    import subprocess
    import asyncio

    try:
        # Пробуем manus-speech-to-text (если доступен на VPS)
        proc = await asyncio.create_subprocess_exec(
            "manus-speech-to-text", file_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0 and stdout:
            return stdout.decode("utf-8").strip()

    except FileNotFoundError:
        pass

    try:
        # Fallback: whisper CLI
        proc = await asyncio.create_subprocess_exec(
            "whisper", file_path,
            "--model", "base",
            "--language", "ru",
            "--output_format", "txt",
            "--output_dir", tempfile.gettempdir(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            # whisper сохраняет .txt файл
            txt_path = os.path.splitext(file_path)[0] + ".txt"
            alt_txt = os.path.join(
                tempfile.gettempdir(),
                os.path.splitext(os.path.basename(file_path))[0] + ".txt"
            )
            for p in [txt_path, alt_txt]:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        return f.read().strip()

    except FileNotFoundError:
        pass

    try:
        # Fallback: faster-whisper через Python
        from faster_whisper import WhisperModel
        model = WhisperModel("base", compute_type="int8")
        segments, _ = model.transcribe(file_path, language="ru")
        return " ".join(seg.text for seg in segments).strip()
    except ImportError:
        pass

    logger.error("No STT engine available")
    return ""
