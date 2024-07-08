
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain_openai import ChatOpenAI
from langchain import LLMChain
from langchain.chains.mapreduce import MapReduceChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import (
    StuffDocumentsChain,
    LLMChain,
    ReduceDocumentsChain,
    MapReduceDocumentsChain,
)
import os
from langchain.prompts import PromptTemplate

# Запросы
map_prompt = """Приведен текст части книги:
{text}
Тебе необходимо написать подробный пересказ объемов от 10% до 20% от исходного текста
Ответ должен быть на русском языке.
Ответ:
"""
reduce_prompt = """Перед тобой список пересказов частей текста книги:
{text_summaries}
Тебе необходимо объединить их в единый пересказ книги
Ответ должен быть на русском языке.
Ответ:
"""

prompt_full_book = """Напиши подробное изложение книги на русском языке.
Пожалуйста, убедись, что ответ будет на русском языке.
Объем изложения должен быть от 10% до 20% объема книги.
Проанализировать нужно всю книгу целиком.
Вот текст: {text}"""

MAP_PROMPT = PromptTemplate(input_variables=["text"], template=map_prompt)
REDUCE_PROMPT = PromptTemplate(input_variables=["text_summaries"], template=reduce_prompt)
PROMPT_FULL_BOOK = PromptTemplate.from_template(prompt_full_book)

def run_mr(input_doc, MAP_PROMPT, REDUCE_PROMPT):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    map_llm_chain = LLMChain(llm=llm, prompt=MAP_PROMPT)

    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    reduce_llm_chain = LLMChain(llm=llm, prompt=REDUCE_PROMPT)

    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_llm_chain,
        document_variable_name="text_summaries"
    )

    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
        collapse_documents_chain=combine_documents_chain,
        token_max=120000
    )

    combine_documents = MapReduceDocumentsChain(
        llm_chain=map_llm_chain,
        reduce_documents_chain=reduce_documents_chain,
        document_variable_name="text",
        return_intermediate_steps=False
    )

    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=120000,
        chunk_overlap=0,
        separator="\n\n"
    )

    map_reduce = MapReduceChain(
        combine_documents_chain=combine_documents,
        text_splitter=text_splitter
    )

    return map_reduce.run(input_text=input_doc)

def full_book(book, prompt):
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
    return stuff_chain.run(book)