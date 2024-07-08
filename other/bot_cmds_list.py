
from aiogram.types import BotCommand

private = [BotCommand(command='start', description='Приветствие'),
           BotCommand(command='download', description='Загрузить книгу'),
           BotCommand(command='delete', description='Удалить книгу'),
           BotCommand(command='summarize', description='Провести суммаризацию'),
           BotCommand(command='quotes', description='Получить основные цитаты'),
           BotCommand(command='recommendations', description='Получить рекомендации'),
           BotCommand(command='help', description='Техническая поддержка'),
           BotCommand(command='end', description='Завершение работы')
           ]