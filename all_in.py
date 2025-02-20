from dotenv import load_dotenv
import os
import logging
from aiogram import types, Dispatcher, Bot
from aiogram.filters import Command
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


dp["banned_users"] = set()
dp["users"] = set()


def register_user_handlers(dp: Dispatcher):
    async def start(message: types.Message):
        if message.from_user.id not in dp["users"]:
            dp["users"].add(message.from_user.id)
            logging.info(f"Добавлен новый пользователь: {message.from_user.id}")  # Логируем
            await message.reply(f"Добро пожаловать, {message.from_user.first_name}! Рад видеть вас.")
        else:
            await message.reply(f"Вы уже зарегистрированы, {message.from_user.first_name}!")

    async def help_command(message: types.Message):
        if message.from_user.id == ADMIN_ID:
            await message.reply(
                "Доступные команды:\n/start - начать\n/help - помощь\n/info - Ваша информация\n/check - проверка на заблокированность\n/ban - забанить пользователя\n/unban - разбанить пользователя\n/banned_users - список забаненных\n/broadcast - рассылка\n/admin - панель администратора")
        else:
            await message.reply(
                "Доступные команды:\n/start - начать\n/help - помощь\n/info - Ваша информация\n/check - проверка на заблокированность")

    async def info_command(message: types.Message):
        user = message.from_user
        info = f"""Имя: {user.first_name}\nВаш ID: {user.id}\nЮзернейм: @{user.username if user.username else 'нет'}\n"""
        await message.reply(info)

    async def check_ban(message: types.Message):
        if message.from_user.id in dp["banned_users"]:
            await message.reply("Вы заблокированы и не можете использовать бота.")
        else:
            await message.reply("Вы не заблокированы, добро пожаловать!")

    dp.message.register(start, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(info_command, Command("info"))
    dp.message.register(check_ban, Command("check"))


def register_admin_handlers(dp: Dispatcher):
    async def admin_panel(message: types.Message):
        if message.from_user.id == ADMIN_ID:
            await message.reply(
                "Привет, админ! Вот доступные команды:\n/ban <user_id> <время_в_минутах> - заблокировать пользователя\n/unban <user_id> - разблокировать пользователя\n/banned_users - список заблокированных\n/broadcast <сообщение> - отправить рассылку")
        else:
            await message.reply("У вас нет доступа к этой команде.")

    async def ban_user(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            await message.reply("У вас нет доступа к этой команде.")
            return
        try:
            args = message.text.split()
            user_id = int(args[1])
            ban_time = int(args[2]) if len(args) > 2 else None

            dp["banned_users"].add(user_id)
            await message.reply(f"Пользователь {user_id} заблокирован.")

            if ban_time:
                await asyncio.sleep(ban_time * 60)
                dp["banned_users"].discard(user_id)
                await message.reply(f"Пользователь {user_id} автоматически разблокирован после {ban_time} минут.")
        except (IndexError, ValueError):
            await message.reply("Используйте команду в формате: /ban <user_id> <время_в_минутах>")

    async def unban_user(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            await message.reply("У вас нет доступа к этой команде.")
            return
        try:
            user_id = int(message.text.split()[1])
            dp["banned_users"].discard(user_id)
            await message.reply(f"Пользователь {user_id} разблокирован.")
        except (IndexError, ValueError):
            await message.reply("Используйте команду в формате: /unban <user_id>")


            

    async def banned_users_list(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            await message.reply("У вас нет доступа к этой команде.")
            return
        banned_list = dp["banned_users"]
        if not banned_list:
            await message.reply("Список заблокированных пользователей пуст.")
        else:
            await message.reply(f"Заблокированные пользователи:\n" + "\n".join(map(str, banned_list)))

    dp.message.register(admin_panel, Command("admin"))
    dp.message.register(ban_user, Command("ban"))
    dp.message.register(unban_user, Command("unban"))
    dp.message.register(banned_users_list, Command("banned_users"))


def register_misc_handlers(dp: Dispatcher):
    async def broadcast(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            await message.reply("У вас нет доступа к этой команде.")
            return
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("Используйте команду в формате: /broadcast <сообщение>")
                return
            text_to_broadcast = args[1]

            if not dp["users"]:
                await message.reply("Нет пользователей для рассылки.")
                return

            failed_users = []
            logging.info(f"Рассылка началась. Всего пользователей: {len(dp['users'])}")

            for user_id in dp["users"]:
                if user_id in dp["banned_users"]:
                    continue
                try:
                    await bot.send_message(user_id, text_to_broadcast)
                    logging.info(f"Сообщение отправлено пользователю {user_id}")
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                    failed_users.append(user_id)

            await message.reply(
                f"Сообщение отправлено. "
                f"{'Не удалось отправить следующим пользователям: ' + ', '.join(map(str, failed_users)) if failed_users else ''}"
            )

        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")
            logging.error(f"Ошибка при рассылке: {e}")

    dp.message.register(broadcast, Command("broadcast"))


register_user_handlers(dp)
register_admin_handlers(dp)
register_misc_handlers(dp)


async def main():
    try:
        await dp.start_polling(bot)
    except (asyncio.CancelledError, Exception) as e:
        logging.error(f"Ошибка при запуске бота: {e}")


if __name__ == '__main__':
    asyncio.run(main())