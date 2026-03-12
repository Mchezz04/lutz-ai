# app.py — Веб-интерфейс для Lutz AI
import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# ============================================================================
# 🎨 Настройки страницы
# ============================================================================
st.set_page_config(
    page_title="Lutz AI — Помощник для изучения Python",
    page_icon="🐍",
    layout="wide"
)

# ============================================================================
# 🔑 Загрузка конфигурации
# ============================================================================
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("❌ API-ключ не найден! Проверь файл `.env`")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# ============================================================================
# 🧠 Промпты (твои, из Qwen)
# ============================================================================
SYSTEM_PROMPT = """
Ты — персональный ментор по Python для начинающего аналитика данных. Твоя задача — помогать мне изучать учебник Марка Лутца "Изучаем Python", фильтруя информацию через призму Data Analytics.

Объясняй теорию кратко, структурно и с примерами.
Если тема не критична для аналитика (например, глубокое управление памятью или специфический GUI), помечай это как "Опционально" или "Пропустить".
Добавляй контекст: как эта тема используется в pandas, numpy или SQL.
Код должен быть чистым, с комментариями и соответствовать PEP 8.

🎨 Форматирование для Obsidian:
- Используй callout-блоки для важных заметок:
  > [!IMPORTANT] Ключевой принцип
  > Текст заметки...
  
  > [!WARNING] Частая ошибка
  > Описание проблемы...
  
  > [!TIP] Совет для аналитика
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
- Используй callout-блоки: > [!IMPORTANT], > [!WARNING], > [!TIP]
- В конце добавь Frontmatter для Obsidian с тегами

Текст главы для анализа:
{text_chunk}
"""

# ============================================================================
# ⚙️ Функции
# ============================================================================
def process_text(text_chunk, chapter_name, focus_topic, model_choice):
    """Отправляет запрос к API и возвращает ответ"""
    
    full_prompt = USER_TEMPLATE.format(
        chapter_name=chapter_name,
        focus_topic=focus_topic,
        text_chunk=text_chunk
    )
    
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': full_prompt}
    ]

    # Настройки модели + лимит токенов
    model_configs = {
        "Qwen Turbo (быстро)": ("qwen/qwen-turbo", 4000),
        "Qwen 2.5 72B (качественно)": ("qwen/qwen-2.5-72b-instruct", 4000),
        "Claude 3.5 Sonnet (лучшая структура)": ("anthropic/claude-3.5-sonnet", 1000),
        "Llama 3 (бесплатно)": ("meta-llama/llama-3-8b-instruct:free", 3000)
    }
    
    model_name, max_tokens_limit = model_configs.get(model_choice, ("qwen/qwen-turbo", 4000))
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            timeout=120,
            temperature=0.7,
            max_tokens=max_tokens_limit
        )
        return response.choices[0].message.content
    except Exception as e:
        # Более понятная ошибка для пользователя
        if "402" in str(e) or "credits" in str(e).lower():
            raise Exception("⚠️ Недостаточно кредитов для этой модели. Попробуй 'Qwen Turbo' или 'Llama 3 (бесплатно)'.")
        raise e

def add_frontmatter(content):
    """Добавляет Obsidian frontmatter к контенту"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    frontmatter = f"""---
created: {timestamp}
tags: [python, lutz, analytics]
status: изучаю
---

"""
    return frontmatter + content

# ============================================================================
# 🖥️ Интерфейс Streamlit
# ============================================================================
def main():
    st.title("🐍 Lutz AI")
    st.subheader("ИИ-помощник для изучения учебника Марка Лутца")
    st.markdown("---")
    
    # Боковая панель с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        chapter_name = st.text_input(
            "Название главы",
            value="Глава 8: Списки и словари",
            help="Как называется глава в учебнике"
        )
        
        focus_topic = st.text_input(
            "На чём сделать акцент",
            value="ключевые методы и применение в анализе данных",
            help="Например: кортежи, работа с файлами, словари"
        )
        
        model_choice = st.selectbox(
            "Модель ИИ",
            options=[
                "Qwen Turbo (быстро)",
                "Qwen 2.5 72B (качественно)",
                "Claude 3.5 Sonnet (лучшая структура)",
                "Llama 3 (бесплатно)"
            ],
            index=1,
            help="Более умные модели могут быть медленнее"
        )
        
        st.info("💡 Совет: начни с небольшого фрагмента текста для теста")
    
    # Основная область
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Загрузи текст главы")
        
        uploaded_file = st.file_uploader(
            "Выбери файл .txt",
            type=["txt"],
            help="Загрузи главу из учебника в формате .txt"
        )
        
        if uploaded_file:
            text_content = uploaded_file.read().decode("utf-8")
            st.success(f"✅ Загружено: {uploaded_file.name}")
            st.text_area("Предпросмотр текста", text_content[:500] + "...", height=150, disabled=True)
        else:
            text_content = None
            st.warning("⚠️ Загрузи файл, чтобы начать")
    
    with col2:
        st.header("⚡ Обработка")
        
        process_btn = st.button("🚀 Обработать главу", type="primary", disabled=not text_content)
        
        if process_btn and text_content:
            with st.spinner("🤖 ИИ анализирует текст... (20-60 сек)"):
                # Берём первые 10000 символов для стабильности
                chunk = text_content[:10000]
                
                try:
                    result = process_text(chunk, chapter_name, focus_topic, model_choice)
                    result_with_frontmatter = add_frontmatter(result)
                    
                    # Сохраняем в сессию для скачивания
                    st.session_state['result'] = result_with_frontmatter
                    st.session_state['filename'] = f"{chapter_name.replace(':', '-')}.md"
                    
                    st.success("✅ Готово!")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")
                    st.exception(e)
    
    # Отображение результата
    if 'result' in st.session_state:
        st.markdown("---")
        st.header("📝 Результат")
        
        # Кнопки действий
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            st.download_button(
                label="📥 Скачать .md для Obsidian",
                data=st.session_state['result'],
                file_name=st.session_state.get('filename', 'output.md'),
                mime="text/markdown",
                type="primary"
            )
        
        with col_btn2:
            if st.button("📋 Скопировать в буфер"):
                st.code(st.session_state['result'], language="markdown")
                st.success("✅ Скопировано! (выдели текст выше и нажми Ctrl+C)")
        
        # Предпросмотр результата
        with st.expander("👁️ Предпросмотр Markdown", expanded=False):
            st.markdown(st.session_state['result'])
    
    # Футер
    st.markdown("---")
    st.caption(
        "Lutz AI • Инструмент для изучения Python • "
        "Сделано с ❤️ для аналитиков данных"
    )

# ============================================================================
# 🚀 Запуск
# ============================================================================
if __name__ == "__main__":
    main()