
from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env
load_dotenv()


import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
import tiktoken
from qoute.summarize_qoute import full_book, quote_chain, quote_full_prompt, quote_map_prompt

def extract_quotes(file_path, openai_api_key):
    with open(file_path, 'rb') as f:
        # Создаем временный файл и записываем в него содержимое файла
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(f.read())

    loader = PyPDFLoader(tmp_file.name)
    book = loader.load()

    os.remove(tmp_file.name)

    os.environ["OPENAI_API_KEY"] = openai_api_key.strip()

    text = "\n\n".join(page.page_content +"страница " +str(int(page.metadata['page'])+1) for page in book)

    encoding = tiktoken.encoding_for_model('gpt-4')
    num_tokens = len(encoding.encode(text))
    if num_tokens > 120_000:
        quotes = quote_chain(text, quote_map_prompt)
    else:
        quotes = full_book(book, quote_full_prompt)
    return quotes
