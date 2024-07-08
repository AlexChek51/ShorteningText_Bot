from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

import os
from pathlib import Path
import logging
from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramForbiddenError
import other.reply as reply
from other.config import bot
from book.app_book import summarize_book
from qoute.app_qoute import extract_quotes
from other.functions import get_books_list, save_to_pdf
from settings import UPLOAD_DIR
from recommendations.app_recommendations import extract_recommendations 
from aiogram.types.input_file import FSInputFile

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


user_private_router = Router()

class BookStates(StatesGroup):
    WAITING_FOR_DELETION = State()
    WAITING_FOR_SUMMARIZE = State()
    WAITING_FOR_QUOTES = State()
    WAITING_FOR_RECOMMENDATION = State()
    WAITING_FOR_COMPANY_NAME = State()  
    WAITING_FOR_COMPANY_DESCRIPTION = State()

# Хэндлер на команду /start
@user_private_router.message(CommandStart())
async def cmd_start(message: types.Message):
    greeting = (
        "Привет!👋 Я ваш помощник🤖 для анализа книг и создания кратких содержаний.\n\n"
        "Основные возможности:\n"
        "1️⃣ - Загрузка книги\n"
        "2️⃣ - Удаление книги\n"
        "3️⃣ - Проведение суммаризации\n"
        "4️⃣ - Поиск основных цитат\n"
        "5️⃣ - Общие рекомендации\n"
        "6️⃣ - Практические рекомендации\n"
        "7️⃣ - Техническая поддержка\n"
        "8️⃣ - Завершение работы\n"
    )
    try:
        await message.answer(greeting, reply_markup=reply.start_kb)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

# Обработчик команды /download
@user_private_router.message(or_f(Command("download"), (F.text.lower() == 'загрузить книгу')))
async def cmd_download(message: types.Message):
    try:
        await message.reply("Пожалуйста, загрузите книгу для анализа. Это должен быть файл формата .pdf.")
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

# Обработчик для документов
@user_private_router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    if message.document.mime_type not in ["application/pdf"]:
        try:
            await message.reply("Пожалуйста, загрузите файл формата .pdf.")
        except TelegramForbiddenError:
            logger.warning(f"Bot was blocked by the user: {message.from_user.id}")
        return

    file_info = await bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)
    destination = UPLOAD_DIR / message.document.file_name
    with open(destination, 'wb') as f:
        f.write(file.read())

    try:
        await message.reply(f"Спасибо! Книга '{message.document.file_name}' успешно загружена для анализа.\n"
                            "Теперь вы можете провести суммаризацию или поиск основных цитат.\n")
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

# Хэндлер на команду /delete
@user_private_router.message(or_f(Command("delete"), (F.text.lower() == 'удалить книгу')))
async def cmd_delete(message: types.Message, state: FSMContext):
    books = get_books_list()
    if not books:
        try:
            await message.answer("В директории нет доступных книг для удаления.")
        except TelegramForbiddenError:
            logger.warning(f"Bot was blocked by the user: {message.from_user.id}")
        return

    text = "Укажите номер книги которую хотите удалить:\n"
    for i, book in enumerate(books, start=1):
        text += f"{i}. {book}\n"

    await state.set_state(BookStates.WAITING_FOR_DELETION)
    try:
        await message.answer(text)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

# Функция обработки выбора книги
@user_private_router.message(F.text.regexp(r'^\d+$'))
async def handle_book_selection(message: types.Message, state: FSMContext):
    books = get_books_list()
    try:
        book_index = int(message.text) - 1
        if 0 <= book_index < len(books):
            selected_book = books[book_index]
            current_state = await state.get_state()

            if current_state == BookStates.WAITING_FOR_DELETION.state:
                os.remove(UPLOAD_DIR / selected_book)
                try:
                    await message.reply(f"Книга '{selected_book}' успешно удалена.")
                except TelegramForbiddenError:
                    logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
                await state.clear()

            elif current_state in [BookStates.WAITING_FOR_SUMMARIZE.state,
                                   BookStates.WAITING_FOR_QUOTES.state,
                                   BookStates.WAITING_FOR_RECOMMENDATION.state]:
                await state.update_data(selected_book=selected_book)
                if current_state == BookStates.WAITING_FOR_RECOMMENDATION.state:
                    await ask_company_name(message, state)
                else:
                    try:
                        await message.reply(f"Вы выбрали книгу '{selected_book}'.")
                    except TelegramForbiddenError:
                        logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
                    await handle_amount(message, state)

        else:
            try:
                await message.reply("Неверный номер книги. Пожалуйста, выберите правильный номер.")
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
    except ValueError:
        try:
            await message.reply("Пожалуйста, введите номер книги.")
        except TelegramForbiddenError:
            logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")


# Хэндлер на команду /summarize
@user_private_router.message(or_f(Command("summarize"), (F.text.lower() == 'провести суммаризацию')))
async def cmd_summarize(message: types.Message, state: FSMContext):
    books = get_books_list()
    if not books:
        try:
            await message.answer("В директории нет доступных книг для суммаризации.")
        except TelegramForbiddenError:
            logger.warning(f"Bot was blocked by the user: {message.from_user.id}")
        return

    text = "Выберите номер книги для суммаризации:\n"
    for i, book in enumerate(books, start=1):
        text += f"{i}. {book}\n"

    await state.set_state(BookStates.WAITING_FOR_SUMMARIZE)
    try:
        await message.answer(text)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")


async def handle_amount(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    selected_book = user_data.get('selected_book')
    company_name = user_data.get('company_name')
    company_description = user_data.get('company_description')

    logger.info(f"UPLOAD_DIR: {UPLOAD_DIR}")
    logger.info(f"selected_book: {selected_book}")

    if not selected_book:
        try:
            await message.reply("Произошла ошибка при выборе книги. Пожалуйста, попробуйте снова.")
        except TelegramForbiddenError:
            logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
        await state.clear()
        return

    openai_api_key = os.getenv("openai_api_key")
    if not openai_api_key:
        try:
            await message.reply("API ключ OpenAI не настроен. Пожалуйста, настройте его и попробуйте снова.")
        except TelegramForbiddenError:
            logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
        await state.clear()
        return

    try:
        current_state = await state.get_state()
        full_file_path = UPLOAD_DIR / selected_book  # Формируем полный путь к файлу
        print(f"Current state: {current_state}")  # Временный вывод для отладки

        if current_state == BookStates.WAITING_FOR_SUMMARIZE.state:
            try:
                await message.reply("Начинаем суммаризацию книги. Пожалуйста, подождите...")
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
            summary = summarize_book(full_file_path, openai_api_key)
            base_name = UPLOAD_DIR / Path(selected_book).stem
            save_path = base_name.with_suffix('.summary.pdf')
            save_to_pdf(summary, save_path)
            try:
                await message.reply(f"Файл \"{save_path.name}\" успешно сохранен.")
                document = FSInputFile(save_path)
                await bot.send_document(message.chat.id, document)
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")

        elif current_state == BookStates.WAITING_FOR_QUOTES.state:
            try:
                await message.reply("Начинаем поиск цитат. Пожалуйста, подождите...")
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
            quotes = extract_quotes(full_file_path, openai_api_key)
            base_name = UPLOAD_DIR / Path(selected_book).stem
            save_path = base_name.with_suffix('.quotes.pdf')
            save_to_pdf(quotes, save_path)
            try:
                await message.reply(f"Файл \"{save_path.name}\" успешно сохранен.")
                document = FSInputFile(save_path)
                await bot.send_document(message.chat.id, document)
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")

        elif current_state == BookStates.WAITING_FOR_COMPANY_DESCRIPTION.state:
            try:
                await message.reply("Начинаем генерацию рекомендаций. Пожалуйста, подождите...")
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")

            recommendations = extract_recommendations(full_file_path, openai_api_key, company_name, company_description)
            base_name = UPLOAD_DIR / Path(selected_book).stem
            save_path = base_name.with_suffix('.recommendations.pdf')
            save_to_pdf(recommendations, save_path)
            try:
                await message.reply(f"Файл \"{save_path.name}\" успешно сохранен.")
                document = FSInputFile(save_path)
                await bot.send_document(message.chat.id, document)
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")

    except Exception as e:
        try:
            await message.reply(f"Произошла ошибка: {e}")
        except TelegramForbiddenError:
            logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
    finally:
        await state.clear()

# Хэндлер на команду /quotes
@user_private_router.message(or_f(Command("quotes"), (F.text.lower() == 'получить основные цитаты')))
async def cmd_quotes(message: types.Message, state: FSMContext):
    books = get_books_list()
    if not books:
        try:
            await message.answer("В директории нет доступных книг для поиска цитат.")
        except TelegramForbiddenError:
            logger.warning(f"Bot was blocked by the user: {message.from_user.id}")
        return

    text = "Выберите номер книги для поиска цитат:\n"
    for i, book in enumerate(books, start=1):
        text += f"{i}. {book}\n"

    await state.set_state(BookStates.WAITING_FOR_QUOTES)
    try:
        await message.answer(text)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

# Хэндлер на команду /recommendations
@user_private_router.message(or_f(Command("recommendations"), (F.text.lower() == 'получить рекомендации')))
async def cmd_recommendations(message: types.Message, state: FSMContext):
    books = get_books_list()
    if not books:
        try:
            await message.answer("В директории нет доступных книг для поиска общих рекомендаций.")
        except TelegramForbiddenError:
            logger.warning(f"Bot was blocked by the user: {message.from_user.id}")
        return

    text = "Выберите номер книги для поиска общих рекомендаций:\n"
    for i, book in enumerate(books, start=1):
        text += f"{i}. {book}\n"

    await state.set_state(BookStates.WAITING_FOR_RECOMMENDATION)
    try:
        await message.answer(text)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

@user_private_router.message(BookStates.WAITING_FOR_RECOMMENDATION)
async def ask_company_name(message: types.Message, state: FSMContext):
    books = get_books_list()
    try:
        book_index = int(message.text) - 1
        if 0 <= book_index < len(books):
            selected_book = books[book_index]
            await state.update_data(selected_book=selected_book, recommendation_type="general")
            await state.set_state(BookStates.WAITING_FOR_COMPANY_NAME)
            try:
                await message.reply("Пожалуйста, введите название компании.")
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
        else:
            try:
                await message.reply("Неверный номер книги. Пожалуйста, выберите правильный номер.")
            except TelegramForbiddenError:
                logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")
    except ValueError:
        try:
            await message.reply("Пожалуйста, введите номер книги.")
        except TelegramForbiddenError:
            logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")

@user_private_router.message(BookStates.WAITING_FOR_COMPANY_NAME)
async def capture_company_name(message: types.Message, state: FSMContext):
    await state.update_data(company_name=message.text)
    await state.set_state(BookStates.WAITING_FOR_COMPANY_DESCRIPTION)
    try:
        await message.reply("Пожалуйста, введите краткое описание компании (до 300 символов).")
    except TelegramForbiddenError:
        logger.warning(f"Bot был заблокирован пользователем: {message.from_user.id}")

@user_private_router.message(BookStates.WAITING_FOR_COMPANY_DESCRIPTION)
async def capture_company_description(message: types.Message, state: FSMContext):
    await state.update_data(company_description=message.text)
    await handle_amount(message, state)

# Хэндлер на команду /help
@user_private_router.message(or_f(Command("help"), (F.text.lower() == 'техническая поддержка')))
async def cmd_help(message: types.Message):
    help_message = (
        "Если у вас есть вопросы или вам нужна поддержка, вы можете связаться с нами по электронной почте или по телефону горячей линии:\n"
        "1. Почта - support@example.com\n"
        "2. Телефон горячей линии - 8-880-000-00-00"
    )
    try:
        await message.answer(help_message)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")

# Хэндлер на команду /end
@user_private_router.message(or_f(Command("end"), (F.text.lower() == 'завершение работы')))
async def cmd_end(message: types.Message):
    end_message = (
        "Спасибо за использование нашего чат-бота!\n"
        "Если у вас возникнут вопросы или потребуется помощь, пожалуйста, напишите нам на почту или позвоните на горячую линию.\n"
        "Всего доброго!"
    )
    try:
        await message.answer(end_message, reply_markup=reply.del_kbd)
    except TelegramForbiddenError:
        logger.warning(f"Bot was blocked by the user: {message.from_user.id}")
