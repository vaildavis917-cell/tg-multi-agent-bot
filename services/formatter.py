"""
Пост-процессинг ответов LLM для красивого отображения в Telegram.
Исправляет Markdown, добавляет структуру, обрабатывает спецсимволы.
"""
import re
import logging

logger = logging.getLogger(__name__)


def format_response(text: str) -> str:
    """
    Форматирует ответ LLM для Telegram Markdown.
    Исправляет типичные проблемы и улучшает читаемость.
    """
    if not text:
        return text

    # 1. Убираем markdown-заголовки (# ## ###) — заменяем на жирный текст с эмодзи
    text = re.sub(r'^#{1,3}\s+(.+)$', r'*\1*', text, flags=re.MULTILINE)

    # 2. Убираем горизонтальные линии (---, ***)
    text = re.sub(r'^[\-\*_]{3,}\s*$', '━━━━━━━━━━━━━━━', text, flags=re.MULTILINE)

    # 3. Исправляем markdown-таблицы → выровненные списки
    text = _fix_tables(text)

    # 4. Исправляем незакрытые markdown-символы
    text = _fix_markdown(text)

    # 5. Убираем множественные пустые строки (максимум 2)
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # 6. Убираем пробелы в конце строк
    text = re.sub(r' +$', '', text, flags=re.MULTILINE)

    return text.strip()


def _fix_tables(text: str) -> str:
    """Конвертирует markdown-таблицы в читаемые списки."""
    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Определяем строку-разделитель таблицы (|---|---|)
        if re.match(r'^\|[\s\-:]+\|', line):
            i += 1
            continue

        # Строка таблицы (| col1 | col2 |)
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            cells = [c for c in cells if c]

            if len(cells) >= 2:
                # Первая строка таблицы (заголовки) — жирным
                if i > 0 and not re.match(r'^\|', lines[i-1].strip()):
                    formatted = ' • '.join(f'*{c}*' for c in cells)
                    result.append(formatted)
                else:
                    # Данные — обычным текстом с разделителем
                    formatted = ' │ '.join(cells)
                    result.append(f'  {formatted}')
            else:
                result.append(line)
        else:
            result.append(line)

        i += 1

    return '\n'.join(result)


def _fix_markdown(text: str) -> str:
    """Исправляет незакрытые markdown-символы для Telegram."""
    # Подсчитываем и исправляем незакрытые * (жирный)
    # Считаем только одиночные * (не внутри кодовых блоков)
    segments = text.split('`')
    for idx in range(0, len(segments), 2):  # Только вне кодовых блоков
        seg = segments[idx]
        # Считаем одиночные * (не **)
        single_stars = len(re.findall(r'(?<!\*)\*(?!\*)', seg))
        if single_stars % 2 != 0:
            # Убираем последний незакрытый *
            pos = seg.rfind('*')
            if pos >= 0:
                segments[idx] = seg[:pos] + seg[pos+1:]

    text = '`'.join(segments)

    # Проверяем незакрытые ` (кодовые блоки)
    backtick_count = text.count('`')
    if backtick_count % 2 != 0:
        # Убираем последний незакрытый `
        pos = text.rfind('`')
        if pos >= 0:
            text = text[:pos] + text[pos+1:]

    # Проверяем незакрытые _ (курсив)
    segments = text.split('`')
    for idx in range(0, len(segments), 2):
        seg = segments[idx]
        underscore_count = len(re.findall(r'(?<!\w)_(?!\w)|(?<=\w)_(?!\w)|(?<!\w)_(?=\w)', seg))
        if underscore_count % 2 != 0:
            pos = seg.rfind('_')
            if pos >= 0:
                segments[idx] = seg[:pos] + seg[pos+1:]

    text = '`'.join(segments)

    return text


def to_html(text: str) -> str:
    """
    Конвертирует Markdown-ответ в Telegram HTML как fallback.
    Используется если Markdown не парсится.
    """
    if not text:
        return text

    # Сначала обрабатываем кодовые блоки (```)
    text = re.sub(r'```(\w*)\n(.*?)```', r'<pre>\2</pre>', text, flags=re.DOTALL)

    # Инлайн код
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Жирный (**text** или *text*)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<b>\1</b>', text)

    # Курсив (_text_)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<i>\1</i>', text)

    # Зачёркнутый (~~text~~)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)

    # Ссылки [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    return text


def try_parse_mode(text: str) -> tuple[str, str]:
    """
    Определяет лучший parse_mode для текста.
    Возвращает (обработанный_текст, parse_mode).
    """
    formatted = format_response(text)

    # Пробуем Markdown
    # Если текст содержит сложное форматирование, лучше использовать HTML
    has_complex = bool(re.search(r'```|<[a-z]+>', formatted))

    if has_complex:
        return to_html(formatted), "HTML"

    return formatted, "Markdown"
