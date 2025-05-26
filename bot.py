import os
import json
import asyncio
import instaloader
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

# === НАСТРОЙКИ ===
TOKEN = '7688474197:AAHMyh4T9-h2nj1dooZodBFpbYX_a-jlXI4'

INSTAGRAM_USERNAME = 'vasiakushv'
INSTAGRAM_PASSWORD = 'kmskmskms'
PROXY = "http://markkukiko:La7gwGRdgQ@104.219.171.140:50100"
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')

INSTAGRAM_FILE = 'instagram_accounts.json'
TIKTOK_FILE = 'tiktok_accounts.json'

# Создаем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= UTILS ==================

def load_accounts(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_accounts(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============== INSTAGRAM ================

async def instagram_check(username):
    L = instaloader.Instaloader()
    if PROXY:
        for i in PROXY:
            L.context.proxy = i
    L.context.user_agent = USER_AGENT

    try:
        L.load_session_from_file(INSTAGRAM_USERNAME)
    except Exception:
        try:
            L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            L.save_session_to_file()
        except Exception as e:
            print(f"[❌] Ошибка входа Instagram: {e}")
            return None

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        status = "ПРИВАТНЫЙ" if profile.is_private else "ОТКРЫТЫЙ"
        return status
    except Exception as e:
        print(f"[❌] Ошибка получения профиля Instagram @{username}: {e}")
        return None

# =============== TIKTOK ==================

async def tiktok_check(username):
    # Пример упрощенной проверки приватности через публичный профиль TikTok
    # Метод: получить страницу https://www.tiktok.com/@username и проверить текст "This account is private" или подобное

    url = f'https://www.tiktok.com/@{username}'
    headers = {
        'User-Agent': USER_AGENT,
        'Accept-Language': 'en-US,en;q=0.9',
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    print(f"[❌] TikTok @{username} недоступен (код {resp.status})")
                    return None
                text = await resp.text()
                if "This account is private" in text or "Account is private" in text:
                    return "ПРИВАТНЫЙ"
                else:
                    return "ОТКРЫТЫЙ"
        except Exception as e:
            print(f"[❌] Ошибка при проверке TikTok @{username}: {e}")
            return None

# =============== КОМАНДЫ ================
@dp.message(Command('menu'))
@dp.message(Command('start'))
async def cmd_start(message: Message):
    print('start')
    text = ("Привет! Я могу отслеживать статус аккаунтов Instagram и TikTok.\n\n"
            "Используй команды:\n"
            "/info — проверка статуса\n"
            "/inst — добавить Instagram аккаунт для отслеживания\n"
            "/tiktok — добавить TikTok аккаунт для отслеживания\n"
            "<code>/tt_delete &lt;@никнейм&gt;</code> — удалить аккаунт TikTok.\n"
            "<code>/ins_delete &lt;@никнейм&gt;</code> — удалить аккаунт Instagram.\n\n"
            "После ввода команды отправь никнейм аккаунта.")
    await message.answer(text, parse_mode="HTML")


@dp.message(Command('tt_delete'))
async def tt_delete(message: Message):
    command_parts = message.text.split()
    accounts = load_accounts(TIKTOK_FILE)  # Загружаем JSON в виде словаря

    username_to_delete = command_parts[1]

    if username_to_delete in accounts:
        del accounts[username_to_delete]  # Удаляем аккаунт
        save_accounts(TIKTOK_FILE, accounts)  # Сохраняем обратно
        await message.answer(f"✅ Аккаунт {username_to_delete} удалён.")
    else:
        await message.answer(f"⚠️ Аккаунт {username_to_delete} не найден.")


@dp.message(Command('ins_delete'))
async def tt_delete(message: Message):
    command_parts = message.text.split()
    accounts = load_accounts(INSTAGRAM_FILE)
    username_to_delete = command_parts[1].lstrip('@')
    if username_to_delete in accounts:
        del accounts[username_to_delete]
        save_accounts(INSTAGRAM_FILE, accounts)
        await message.answer(f"✅ Аккаунт {username_to_delete} удалён.")
    else:
        await message.answer(f"⚠️ Аккаунт {username_to_delete} не найден.")


@dp.message(Command('inst'))
async def cmd_inst(message: Message):
    await message.answer("Введи ник Instagram аккаунта для отслеживания:")
    dp.message.register(instagram_receive_username, F.text)



@dp.message(Command('tiktok'))
async def cmd_tiktok(message: Message):
    await message.answer("Введи ник TikTok аккаунта для отслеживания.Пример:@name")
    dp.message.register(tiktok_receive_username, F.text)

# =========== ОБРАБОТЧИКИ ВВОДА НИКОВ ============

async def instagram_receive_username(message: Message):
    username = message.text.strip().lstrip('@').lower()
    accounts = load_accounts(INSTAGRAM_FILE)
    if username in accounts:
        await message.answer(f"Instagram аккаунт @{username} уже в списке отслеживания.")
    else:
        # Проверяем сразу статус перед добавлением
        status = await instagram_check(username)
        if status:
            accounts[username] = {
                'status': status,
                'chat_id': message.chat.id
            }
            save_accounts(INSTAGRAM_FILE, accounts)
            await message.answer(f"Instagram аккаунт @{username} добавлен для отслеживания.\nТекущий статус: {status}")
        else:
            await message.answer(f"Не удалось получить информацию по Instagram аккаунту @{username}. Попробуйте позже.")

async def tiktok_receive_username(message: Message):
    username = message.text.strip().lstrip('@').lower()
    accounts = load_accounts(TIKTOK_FILE)
    if username in accounts:
        await message.answer(f"TikTok аккаунт @{username} уже в списке отслеживания.")
    else:
        status = await tiktok_check(username)
        if status:
            accounts[username] = {
                'status': status,
                'chat_id': message.chat.id
            }
            save_accounts(TIKTOK_FILE, accounts)
            await message.answer(f"TikTok аккаунт @{username} добавлен для отслеживания.\nТекущий статус: {status}")
        else:
            await message.answer(f"Не удалось получить информацию по TikTok аккаунту @{username}. Попробуйте позже.")

# =============== ФОНОВАЯ ПРОВЕРКА ===============

async def periodic_instagram_check():
    while True:
        accounts = load_accounts(INSTAGRAM_FILE)
        for username, info in accounts.items():
            current_status = await instagram_check(username)
            if current_status and current_status != info['status']:
                chat_id = info['chat_id']
                await bot.send_message(chat_id,
                    f"🔔 Изменился статус Instagram аккаунта @{username}:\n"
                    f"Было: {info['status']}\n"
                    f"Стало: {current_status}")
                accounts[username]['status'] = current_status
                save_accounts(INSTAGRAM_FILE, accounts)
        await asyncio.sleep(10 * 60 * 60)  # 10 часов

async def periodic_tiktok_check():
    await asyncio.sleep(10 * 60)  # задержка 10 минут для смещения от Instagram
    while True:
        accounts = load_accounts(TIKTOK_FILE)
        for username, info in accounts.items():
            current_status = await tiktok_check(username)
            if current_status and current_status != info['status']:
                chat_id = info['chat_id']
                await bot.send_message(chat_id,
                    f"🔔 Изменился статус TikTok аккаунта @{username}:\n"
                    f"Было: {info['status']}\n"
                    f"Стало: {current_status}")
                accounts[username]['status'] = current_status
                save_accounts(TIKTOK_FILE, accounts)
        await asyncio.sleep(10 * 60 * 60)  # 10 часов


@dp.message(Command('info'))
async def info(message:Message):
    accounts = load_accounts(INSTAGRAM_FILE)
    for username, info in accounts.items():
        await message.answer(f"Instagram аккаунт @{username}.\nТекущий статус: {info['status']}")

    accounts = load_accounts(TIKTOK_FILE)
    for username, info in accounts.items():
        await message.answer(f"TikTok аккаунт @{username}.\nТекущий статус: {info['status']}")

# =============== ЗАПУСК БОТА ===============

async def main():
    dp.message.register(instagram_receive_username, F.text, lambda m: False)  # чтобы избежать дубли регистрации

    asyncio.create_task(periodic_instagram_check())
    asyncio.create_task(periodic_tiktok_check())

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
