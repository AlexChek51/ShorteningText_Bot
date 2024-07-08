from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Загрузить книгу'),
            KeyboardButton(text='Удалить книгу'),
        ],
        [
            KeyboardButton(text='Провести суммаризацию'),
            KeyboardButton(text='Получить основные цитаты'),
        ],
        [
            KeyboardButton(text='Получить рекомендации'),
            KeyboardButton(text='Техническая поддержка'),
        ],
        [
            KeyboardButton(text='Завершение работы'),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder='Что Вас интересует?'
)

del_kbd = ReplyKeyboardRemove()