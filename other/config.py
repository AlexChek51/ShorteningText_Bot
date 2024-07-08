import os
from aiogram import Bot, Dispatcher

bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher()
