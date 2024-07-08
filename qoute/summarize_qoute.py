
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain_openai import ChatOpenAI
from langchain import LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import (
    StuffDocumentsChain,
    LLMChain,
    ReduceDocumentsChain,
    MapReduceDocumentsChain,
)
from langchain.prompts import PromptTemplate


quote_full = """Извлеки шаг за шагом самые яркие цитаты в порядке появления их в книге. Вот пример цитат: 
"Я мыслю, следовательно, я существую" (Cogito, ergo sum) - эта фраза принадлежит философу Рене Декарту. Она означает, что акт мышления подтверждает существование самого мыслящего индивидуума. Декарт использовал эту фразу как основу для установления своего собственного существования и, таким образом, основания для философской уверенности.
"Будьте изменением, которое вы хотите видеть в мире" - приписывается Махатме Ганди. Эта цитата призывает каждого человека начинать изменения с самого себя, чтобы привнести положительные изменения в окружающий мир.
"Знание - сила" (Knowledge is power) - эта фраза, которую часто ассоциируют с английским философом Фрэнсисом Бэконом, подчеркивает важность знаний и образования в достижении успеха и влияния.
"Всё, что я знаю, это то, что я ничего не знаю" - это выражение, которое приписывается Сократу. Оно отражает его скромное признание того, что истинное знание несовершенно и всегда требует глубокого размышления и исследования.
"Будьте добры, потому что каждый, с кем вы встречаетесь, ведет тяжелую битву" - эта фраза напоминает о том, что каждый человек, с которым мы взаимодействуем, может переживать свои собственные трудности и проблемы, и поэтому важно относиться к ним с пониманием и состраданием.
Проверяй на орфографические и смысловые ошибки, если слово переносится на другую строку через '-' необходимо объединить. 
Если цитата повторяется её не нужно добавлять.
Вот текст книги: {text}
Ответ должен быть в следующем формате:
Формат цитат: Цитата: "____" Объяснение: "____"(страница __)
После списка цитат ничего не добавляй
Ответ:
"""

quote_map = """Извлеки шаг за шагом самые яркие цитаты из текста в порядке появления их. Вот пример цитат: 
"Я мыслю, следовательно, я существую" (Cogito, ergo sum) - эта фраза принадлежит философу Рене Декарту. Она означает, что акт мышления подтверждает существование самого мыслящего индивидуума. Декарт использовал эту фразу как основу для установления своего собственного существования и, таким образом, основания для философской уверенности.
"Будьте изменением, которое вы хотите видеть в мире" - приписывается Махатме Ганди. Эта цитата призывает каждого человека начинать изменения с самого себя, чтобы привнести положительные изменения в окружающий мир.
"Знание - сила" (Knowledge is power) - эта фраза, которую часто ассоциируют с английским философом Фрэнсисом Бэконом, подчеркивает важность знаний и образования в достижении успеха и влияния.
"Всё, что я знаю, это то, что я ничего не знаю" - это выражение, которое приписывается Сократу. Оно отражает его скромное признание того, что истинное знание несовершенно и всегда требует глубокого размышления и исследования.
"Будьте добры, потому что каждый, с кем вы встречаетесь, ведет тяжелую битву" - эта фраза напоминает о том, что каждый человек, с которым мы взаимодействуем, может переживать свои собственные трудности и проблемы, и поэтому важно относиться к ним с пониманием и состраданием.
Проверяй на орфографические и смысловые ошибки, если слово переносится на другую строку через '-' необходимо объединить.  
Если цитата повторяется её не нужно добавлять.
Вот текст: {text}
Ответ должен быть в следующем формате:
Формат цитат: Цитата: "____" Объяснение: "____"(страница __)
После списка цитат ничего не добавляй
Ответ:
"""

quote_full_prompt = PromptTemplate.from_template(quote_full)
quote_map_prompt = PromptTemplate(input_variables=["text"], template=quote_map)

def full_book(book, prompt):
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
    return stuff_chain.run(book)

def quote_chain(text, prompt):
    quote_list = []
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4o",
        chunk_size=120000,
        chunk_overlap=100,
    )
    for chunk in text_splitter.create_documents([text]):
        quote_list.append(full_book([chunk], prompt))
    return "\n".join(quote_list)