import nest_asyncio
nest_asyncio.apply()
import asyncio
from aiogram import types
from aiogram.types import BotCommandScopeAllPrivateChats
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from other.config import bot, dp
from other.bot_cmds_list import private
from handlers.user_private_handlers import user_private_router  


# Запуск процесса поллинга новых апдейтов
async def main():
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    dp.include_router(user_private_router)
    await dp.start_polling(bot)

# Запустите бота
if __name__ == "__main__":
    asyncio.run(main())