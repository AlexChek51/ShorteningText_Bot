
from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env
load_dotenv()

import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
import tiktoken
from book.summarize_book import run_mr, full_book, MAP_PROMPT, REDUCE_PROMPT, PROMPT_FULL_BOOK

def summarize_book(file_path: str, openai_api_key: str):
    with open(file_path, 'rb') as f:
        # Создаем временный файл и записываем в него содержимое файла
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(f.read())

        # Загружаем книгу из временного файла
        loader = PyPDFLoader(tmp_file.name)
        book = loader.load()

        # Удаляем временный файл
        os.remove(tmp_file.name)

    # Устанавливаем API ключ OpenAI
    os.environ["OPENAI_API_KEY"] = openai_api_key.strip()

    # Получаем текст книги
    text = "\n\n".join(page.page_content +"страница " +str(int(page.metadata['page'])+1) for page in book)

    # Определяем метод суммаризации в зависимости от количества токенов
    encoding = tiktoken.encoding_for_model('gpt-4')
    num_tokens = len(encoding.encode(text))
    if num_tokens > 120_000:
        summary = run_mr(text, MAP_PROMPT, REDUCE_PROMPT)
    else:
        summary = full_book(book, PROMPT_FULL_BOOK)

    return summary
