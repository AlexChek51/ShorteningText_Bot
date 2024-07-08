from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env
load_dotenv()

import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
import tiktoken
from recommendations.summarize_recommendations import run_mr

# Запрос для прохода по частям книги
map_prompt = """Тебе необходимо выделить бизнес рекомендации на основе текста части книги для компании {company_name}.
{about_company}.
Текст:\n{text}
Приведи практические примеры случаев из текста адаптированной для компании.
Ответ должен быть на русском языке.
Ответ:
"""
# Результирующий запрос
reduce_prompt = """Перед тобой список бизнес рекомендаци для компании c практическими примерами. 
\n{text_summaries}
Изучи весть текст и напиши до 5 рекомендаций на основе списка рекомендаций.
С практическими примерами случаев из текста адаптированной для компании.
Ответ должен быть на русском языке.
Ответ:
"""
prompt_full_book = """Напиши бизснес рекомендации для компании {company_name}.
{about_company}.
Изучи весть текст и напиши до 5 рекомендаций на основе текста.
Приведи практические примеры случаев из текста адаптированной для компании.
Ответ должен быть на русском языке.
Вот текст: {text}"""



def extract_recommendations(file_path, openai_api_key, company_name, about_company):
    with open(file_path, 'rb') as f:
        # Создаем временный файл и записываем в него содержимое файла
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(f.read())

    loader = PyPDFLoader(tmp_file.name)
    book = loader.load()

    os.remove(tmp_file.name)

    os.environ["OPENAI_API_KEY"] = openai_api_key.strip()

    text = "\n\n".join(page.page_content +"страница " +str(int(page.metadata['page'])+1) for page in book)


    encoding = tiktoken.encoding_for_model('gpt-4o-')
    num_tokens = len(encoding.encode(text))

    prompt = PromptTemplate.from_template(prompt_full_book.format(company_name=company_name, about_company = about_company, text='{text}'))
    MAP_PROMPT = PromptTemplate(input_variables=["text"], template=map_prompt.format(company_name=company_name, about_company = about_company, text='{text}'))
    REDUCE_PROMPT = PromptTemplate(input_variables=["text_summaries"], template=reduce_prompt.format(company_name=company_name, about_company = about_company, text_summaries='{text_summaries}'))

    if num_tokens >120_000:

        summary = run_mr(text, MAP_PROMPT,REDUCE_PROMPT)

    return summary

