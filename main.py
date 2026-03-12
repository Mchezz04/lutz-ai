import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# 1. Загружаем ключ из .env файла
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# 🔍 Отладка: покажем ключ (первые 10 символов)
if api_key:
    print(f"✅ Ключ загружен: {api_key[:15]}...")
else:
    print("❌ Ключ НЕ загружен! Проверь файл .env")
    exit()

# 2. Инициализируем клиент OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# 3. ТВОИ ПРОМПТЫ (из Qwen)
# ============================================================================

SYSTEM_PROMPT = """
Ты — персональный ментор по Python для начинающего аналитика данных. Твоя задача — помогать мне изучать учебник Марка Лутца "Изучаем Python", фильтруя информацию через призму Data Analytics.

Объясняй теорию кратко, структурно и с примерами.
Если тема не критична для аналитика (например, глубокое управление памятью или специфический GUI), помечай это как "Опционально" или "Пропустить".
Добавляй контекст: как эта тема используется в pandas, numpy или SQL.
Код должен быть чистым, с комментариями и соответствовать PEP 8.

Формат ответа: Markdown-заметка для Obsidian с заголовками H1-H3, таблицами, блоками кода и wikilinks.
Форматирование для Obsidian:
- Используй callout-блоки для важных заметок:
  > [!IMPORTANT] Ключевой принцип
  > Текст заметки...
  
  > [!WARNING] Частая ошибка
  > Описание проблемы...
  
  > [!TIP] Совет
  > Полезная рекомендация...
  
- Для примеров кода используй блоки ```python
- Для таблиц используй markdown-таблицы
- В конце добавь Frontmatter с тегами
"""

USER_TEMPLATE = """
Разбери главу: {chapter_name}

Сделай следующее:

📌 **Саммари**: Основные тезисы главы (bullet points). Распиши их подробно с описанием и заметками из книги. Остановись подробнее всего на {focus_topic}.

🎯 **Фильтр аналитика**: Что из этого нужно знать обязательно, а что можно гуглить по мере необходимости?

🔗 **Связь с DS/DA**: Приведи пример, как этот механизм используется в анализе данных (pandas, numpy, SQL).

⚠️ **Подводные камни**: Частые ошибки новичков в этой теме.

💻 **Примеры кода**: Дай 2-3 рабочих примера с комментариями (в формате VS Code).

📚 **Ссылки**: Добавь раздел для внутренних связей Obsidian (wikilinks [[...]]).

---
Требования к оформлению:
- Используй заголовки H1-H3
- Добавляй таблицы где уместно
- Блоки кода с подсветкой синтаксиса python
- Эмодзи для визуальной навигации
- В конце добавь Frontmatter для Obsidian с тегами

Текст главы для анализа:
{text_chunk}
"""

# ============================================================================

# 4. Функция для чтения текста книги
def load_chapter(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Файл {file_path} не найден!")
        return None

# 5. Функция запроса к API (обновлённая)
def get_ai_summary(text_chunk, chapter_name="Текущая глава", focus_topic="ключевые темы"):
    print("⏳ Обрабатываю текст нейросетью... (это может занять 20-40 сек)")
    
    full_prompt = USER_TEMPLATE.format(
        chapter_name=chapter_name,
        focus_topic=focus_topic,
        text_chunk=text_chunk
    )
    
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': full_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-72b-instruct",  # Более умная модель для качественного вывода
            messages=messages,
            timeout=120,  # Увеличили таймаут для длинных ответов
            temperature=0.7,  # Баланс креативности и точности
            max_tokens=4000  # Достаточно для развёрнутого ответа
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка API: {type(e).__name__}")
        print(f"   Детали: {str(e)}")
        return None

# 6. Функция сохранения в Markdown
def save_to_markdown(content, filename="output.md"):
    # Добавляем timestamp в начало файла
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    frontmatter = f"""---
created: {timestamp}
tags: [python, lutz, analytics]
status: изучаю
---

"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content)
    print(f"✅ Готово! Файл сохранён как {filename}")

# 7. Основная логика
if __name__ == "__main__":
    # Настройки для обработки
    book_file = "chapter_1.txt"
    chapter_name = "ГЛАВА 8 Списки и словари"  # <-- Меняй под главу
    focus_topic = "словари"  # <-- На чём сделать акцент
    
    text = load_chapter(book_file)
    
    if text:
        # Берём больше текста для качественного анализа (10000 символов)
        test_text = text[:10000] 
        
        result = get_ai_summary(test_text, chapter_name, focus_topic)
        
        if result:
            save_to_markdown(result)
            print("\n🎉 Успешно! Открой output.md в Obsidian")
        else:
            print("\n❌ Не удалось получить ответ от API")