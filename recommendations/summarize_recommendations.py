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


def run_mr(input_doc,MAP_PROMPT,REDUCE_PROMPT):

    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    map_llm_chain = LLMChain(llm=llm, prompt=MAP_PROMPT)

    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    reduce_llm_chain = LLMChain(llm=llm, prompt=REDUCE_PROMPT)

    # Берет список документов и объединяет их в одну строку
    combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_llm_chain,
            document_variable_name="text_summaries")

    # Объединяет и итеративно сокращает отображаемые документы
    reduce_documents_chain = ReduceDocumentsChain(
        # Это финальная цепочка, которая вызывается.
        combine_documents_chain=combine_documents_chain,
        # Если документы превышают контекст для `combine_documents_chain`
        collapse_documents_chain=combine_documents_chain,
        # Максимальное количество токенов для группировки документов.
        token_max=120000)

    # Объединяет документы, отображая цепочку по ним, а затем объединяя результаты
    combine_documents = MapReduceDocumentsChain(
        # Цепочка отображения
        llm_chain=map_llm_chain,
        # Цепочка сокращения
        reduce_documents_chain=reduce_documents_chain,
        # Имя переменной в llm_chain для размещения документов
        document_variable_name="text",
        # Возвращает результаты шагов отображения в выводе
        ### Ошибка: это в настоящее время не работает ###
        return_intermediate_steps=False)

    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=120000 ,
    chunk_overlap=0,
    separator="\n\n"
  )

    # Определяет Map=Reduce
    map_reduce = MapReduceChain(
        # Цепочка для объединения документов
        combine_documents_chain=combine_documents,
        # Разделитель для начального разделения
        text_splitter=text_splitter)

    return map_reduce.run(input_text=input_doc)
