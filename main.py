import logging
import sys
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from keyboard import *

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from database import DataBase

# Проверка версии Python
print(f"Python version: {sys.version}")

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)
db = DataBase('db_base.db')

# ---------- КОМАНДЫ БОТА ----------
async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота")
    ])
# ---------- СОСТОЯНИЯ ----------
class Send_Message(StatesGroup):
    text = State()

class AdminStates(StatesGroup):
    add_channel_id = State()
    add_channel_url = State()
    add_channel_name = State()
    remove_channel_id = State()
    add_admin_id = State()
    remove_admin_id = State()
    broadcast_text = State()

# ---------- ПРОВЕРКА ПОДПИСКИ ----------
async def check_subscription(user_id, channel_id):
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return False

async def check_all_subscriptions(user_id):
    """Проверяет подписку на все активные каналы"""
    channels = db.get_active_channels()
    for channel in channels:
        channel_id = channel[0]
        if not await check_subscription(user_id, channel_id):
            return False, channel_id
    return True, None

async def require_subscription(message: types.Message):
    """Требует подписки на все каналы"""
    channels = db.get_active_channels()
    if not channels:
        # Если каналов нет, пропускаем проверку
        return True
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        channel_id, channel_url, channel_name = channel
        keyboard.add(InlineKeyboardButton(f"📢 Подписаться на {channel_name}", url=channel_url))
    keyboard.add(InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
    
    await message.answer(
        "⚠️ <b>Для использования бота необходимо подписаться на наши каналы!</b>\n\n"
        "Нажмите кнопки ниже, чтобы подписаться, а затем проверьте подписку.",
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    return False

@dp.callback_query_handler(text='check_sub')
async def check_sub_callback(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    is_subscribed, _ = await check_all_subscriptions(user_id)
    if is_subscribed:
        await callback.message.delete()
        await cmd_start(callback.message, None)
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)
        channels = db.get_active_channels()
        for channel in channels:
            c_id, c_url, c_name = channel
            keyboard.add(InlineKeyboardButton(f"📢 Подписаться на {c_name}", url=c_url))
        keyboard.add(InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
        
        await callback.message.answer(
            "❌ Вы ещё не подписались на все каналы!\n"
            "Подпишитесь и нажмите 'Проверить подписку' снова.",
            reply_markup=keyboard
        )
# ---------- КОМАНДА /start ----------
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    db.db_start()
    
    # Проверяем подписку на все каналы
    is_subscribed, _ = await check_all_subscriptions(message.from_user.id)
    if not is_subscribed:
        await require_subscription(message)
        return
    
    # Если админ - показываем админ-панель
    if db.is_admin(message.from_user.id):
        await message.answer(
            f"👋 Привет, админ {message.from_user.first_name}!\n\n"
            "Выберите действие:",
            reply_markup=admin_keyboard()
        )
        return
    
    if message.from_user.username is None:
        return await message.answer('Установите @username и пропишите /start')
    
    if not db.user_exists(message.from_user.id):
        start_cmd = message.text
        referi_id = str(start_cmd[7:])
        if str(referi_id) != '':
            if str(referi_id) != str(message.from_user.id):
                username_referi = db.username_referi(referi_id)
                
                db.add_user_referi(
                    user_id=message.from_user.id, 
                    username=message.from_user.username, 
                    refere_id=referi_id, 
                    username_referi=username_referi[0] if username_referi else 'Unknown'
                )
                await message.answer(
                    'Напиши сообщение человеку, который опубликовал эту ссылку\n\n'
                    'Напиши своё сообщение:', 
                    reply_markup=kb_back
                )
                await Send_Message.text.set()
                await state.update_data(name=referi_id)
            else:
                db.add_user_no_referi(message.from_user.id, message.from_user.username, 0)
                await bot.send_message(message.from_user.id, "Нельзя отправлять вопросы самому себе!")
        else:
            db.add_user_no_referi(message.from_user.id, message.from_user.username, 0)
            await message.answer(
                'Вот твоя личная ссылка:\n\n'
                f't.me/{NICNAME_BOT}?start={message.from_user.id}\n\n'
                'Опубликуй её и получай анонимные сообщения'
            )
    else:
        if message.text[7:] != '':
            await message.answer(
                'Напиши сообщение человеку, который опубликовал эту ссылку\n\n'
                'Напиши своё сообщение:', 
                reply_markup=kb_back
            )
            await Send_Message.text.set()
            await state.update_data(name=message.text[7:])
        else:
            await message.answer(
                'Вот твоя личная ссылка:\n\n'
                f't.me/{NICNAME_BOT}?start={message.from_user.id}\n\n'
                'Опубликуй её и получай анонимные сообщения'
            )
# ---------- ОТМЕНА ----------
@dp.message_handler(text='Отмена ❌', state='*')
async def back(message: types.Message, state: FSMContext):
    await message.answer("Вы отменили действие!", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

@dp.message_handler(text='🔙 Выйти из админки', state='*')
async def exit_admin(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Вы вышли из админ-панели",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await cmd_start(message, state)

# ---------- ОТПРАВКА СООБЩЕНИЙ ----------
@dp.message_handler(state=Send_Message.text)
async def state_message(message: types.Message, state: FSMContext):
    is_subscribed, _ = await check_all_subscriptions(message.from_user.id)
    if not is_subscribed:
        await require_subscription(message)
        await state.finish()
        return
    
    data = await state.get_data()
    user = data['name']
    text = message.text

    await bot.send_message(
        chat_id=user, 
        text=f'<b>Получено новое сообщение</b>\n\n{text}', 
        reply_markup=send_message(user_id=message.from_user.id)
    )

    await message.answer(
        '<b>Ваш ответ был отправлен</b>\n\nВот твоя личная ссылка:\n\n'
        f't.me/{NICNAME_BOT}?start={message.from_user.id}\n\n'
        'Опубликуй её и получай анонимные сообщения'
    )
    await state.finish()

@dp.callback_query_handler(text_startswith='send')
async def reply_messages(callback: types.CallbackQuery, state: FSMContext):
    is_subscribed, _ = await check_all_subscriptions(callback.from_user.id)
    if not is_subscribed:
        await callback.answer("Вы не подписаны на все каналы!", show_alert=True)
        await require_subscription(callback.message)
        return
    
    await Send_Message.text.set()
    user = callback.data.split('|')[1]
    await state.update_data(name=user)
    await callback.message.delete()
    await callback.message.answer(
        'Напиши сообщение человеку, который отправил тебе сообщение\n\n'
        'Напиши своё сообщение:', 
        reply_markup=kb_back
    )
# ---------- АДМИН-ПАНЕЛЬ ----------
@dp.message_handler(text='📊 Статистика')
async def admin_stats(message: types.Message):
    if not db.is_admin(message.from_user.id):
        return
    
    users = db.cur.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    admins = db.cur.execute('SELECT COUNT(*) FROM admins').fetchone()[0]
    channels = db.cur.execute('SELECT COUNT(*) FROM channels WHERE is_active = 1').fetchone()[0]
    
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👤 Пользователей: {users}\n"
        f"👥 Администраторов: {admins}\n"
        f"📢 Активных каналов: {channels}\n"
        f"🤖 Бот: @{NICNAME_BOT}",
        parse_mode='HTML'
    )

# ---------- УПРАВЛЕНИЕ КАНАЛАМИ ----------
@dp.message_handler(text='📢 Управление каналами')
async def admin_channels(message: types.Message):
    if not db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📢 <b>Управление каналами</b>\n\n"
        "Выберите действие:",
        reply_markup=channels_keyboard(),
        parse_mode='HTML'
    )

@dp.callback_query_handler(text='add_channel')
async def add_channel_start(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    await callback.answer()
    await callback.message.answer(
        "➕ <b>Добавление канала</b>\n\n"
        "Отправьте ID канала (например: -1001234567890)\n\n"
        "ID можно получить у бота @getmyid_bot",
        parse_mode='HTML'
    )
    await AdminStates.add_channel_id.set()

@dp.message_handler(state=AdminStates.add_channel_id)
async def add_channel_id(message: types.Message, state: FSMContext):
    try:
        channel_id = int(message.text)
        await state.update_data(channel_id=channel_id)
        await message.answer(
            "📎 Отправьте ссылку на канал (например: https://t.me/канал)"
        )
        await AdminStates.add_channel_url.set()
    except:
        await message.answer("❌ Неверный ID. Отправьте число (например: -1001234567890)")

@dp.message_handler(state=AdminStates.add_channel_url)
async def add_channel_url(message: types.Message, state: FSMContext):
    if not message.text.startswith('https://t.me/'):
        await message.answer("❌ Неверная ссылка. Ссылка должна начинаться с https://t.me/")
        return
    
    await state.update_data(channel_url=message.text)
    await message.answer(
        "📝 Отправьте название канала (как оно будет отображаться у пользователей)"
    )
    await AdminStates.add_channel_name.set()

@dp.message_handler(state=AdminStates.add_channel_name)
async def add_channel_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data['channel_id']
    channel_url = data['channel_url']
    channel_name = message.text
    
    if db.add_channel(channel_id, channel_url, channel_name, message.from_user.id):
        await message.answer(
            f"✅ Канал <b>{channel_name}</b> успешно добавлен!\n\n"
            f"ID: {channel_id}\n"
            f"Ссылка: {channel_url}",
            parse_mode='HTML'
        )
    else:
        await message.answer("❌ Ошибка! Возможно, такой канал уже существует.")
    
    await state.finish()
# ---------- СПИСОК КАНАЛОВ ----------
@dp.callback_query_handler(text='list_channels')
async def list_channels(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    await callback.answer()
    channels = db.get_all_channels()
    
    if not channels:
        await callback.message.answer("📢 Каналы не добавлены.")
        return
    
    text = "📋 <b>Список каналов:</b>\n\n"
    for channel in channels:
        channel_id, channel_url, channel_name, is_active = channel
        status = "✅ Активен" if is_active else "❌ Неактивен"
        text += f"<b>{channel_name}</b>\n"
        text += f"ID: {channel_id}\n"
        text += f"Ссылка: {channel_url}\n"
        text += f"Статус: {status}\n\n"
    
    await callback.message.answer(text, parse_mode='HTML')

@dp.callback_query_handler(text='remove_channel')
async def remove_channel_start(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    await callback.answer()
    channels = db.get_all_channels()
    
    if not channels:
        await callback.message.answer("📢 Каналы не добавлены.")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        channel_id, channel_url, channel_name, is_active = channel
        keyboard.add(
            InlineKeyboardButton(f"❌ {channel_name}", callback_data=f"del_ch_{channel_id}")
        )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    await callback.message.answer(
        "Выберите канал для удаления:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(text_startswith='del_ch_')
async def remove_channel(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    channel_id = int(callback.data.split('_')[2])
    db.remove_channel(channel_id)
    await callback.answer("✅ Канал удалён!")
    await callback.message.delete()
# ---------- УПРАВЛЕНИЕ АДМИНАМИ ----------
@dp.message_handler(text='👥 Управление админами')
async def admin_admins(message: types.Message):
    if not db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👥 <b>Управление администраторами</b>\n\n"
        "Выберите действие:",
        reply_markup=admins_keyboard(),
        parse_mode='HTML'
    )

@dp.callback_query_handler(text='add_admin')
async def add_admin_start(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    await callback.answer()
    await callback.message.answer(
        "➕ <b>Добавление администратора</b>\n\n"
        "Отправьте ID пользователя (можно получить у @getmyid_bot)"
    )
    await AdminStates.add_admin_id.set()

@dp.message_handler(state=AdminStates.add_admin_id)
async def add_admin_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        
        # Проверяем, есть ли уже такой админ
        if db.is_admin(user_id):
            await message.answer("❌ Этот пользователь уже является администратором!")
            await state.finish()
            return
        
        # Добавляем админа
        if db.add_admin(user_id, "Unknown", message.from_user.id):
            await message.answer(f"✅ Пользователь с ID {user_id} теперь администратор!")
        else:
            await message.answer("❌ Ошибка при добавлении администратора!")
        
        await state.finish()
    except:
        await message.answer("❌ Неверный ID. Отправьте число.")

@dp.callback_query_handler(text='list_admins')
async def list_admins(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    await callback.answer()
    admins = db.get_all_admins()
    
    if not admins:
        await callback.message.answer("👥 Администраторы не добавлены.")
        return
    
    text = "👥 <b>Список администраторов:</b>\n\n"
    for admin in admins:
        user_id, username = admin
        text += f"ID: {user_id} | @{username}\n"
    
    await callback.message.answer(text, parse_mode='HTML')

@dp.callback_query_handler(text='remove_admin')
async def remove_admin_start(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    await callback.answer()
    admins = db.get_all_admins()
    
    if not admins:
        await callback.message.answer("👥 Администраторы не добавлены.")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for admin in admins:
        user_id, username = admin
        if user_id != MAIN_ADMIN_ID:  # Нельзя удалить главного админа
            keyboard.add(
                InlineKeyboardButton(f"❌ {username}", callback_data=f"del_adm_{user_id}")
            )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    await callback.message.answer(
        "Выберите администратора для удаления:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(text_startswith='del_adm_')
async def remove_admin(callback: types.CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    user_id = int(callback.data.split('_')[2])
    if user_id == MAIN_ADMIN_ID:
        await callback.answer("❌ Нельзя удалить главного администратора!", show_alert=True)
        return
    
    db.remove_admin(user_id)
    await callback.answer("✅ Администратор удалён!")
    await callback.message.delete()
# ---------- РАССЫЛКА ----------
@dp.message_handler(text='📨 Рассылка')
async def admin_broadcast(message: types.Message):
    if not db.is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📨 <b>Рассылка сообщений</b>\n\n"
        "Отправьте текст для рассылки всем пользователям:",
        parse_mode='HTML'
    )
    await AdminStates.broadcast_text.set()

@dp.message_handler(state=AdminStates.broadcast_text)
async def broadcast_send(message: types.Message, state: FSMContext):
    text = message.text
    users = db.cur.execute('SELECT user_id FROM users').fetchall()
    
    await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")
    
    success = 0
    fail = 0
    
    for user in users:
        try:
            await bot.send_message(user[0], f"📨 <b>Рассылка</b>\n\n{text}", parse_mode='HTML')
            success += 1
        except:
            fail += 1
    
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Доставлено: {success}\n"
        f"Не доставлено: {fail}",
        parse_mode='HTML'
    )
    await state.finish()

# ---------- НАЗАД В АДМИНКУ ----------
@dp.callback_query_handler(text='admin_back')
async def admin_back(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "👋 Выберите действие:",
        reply_markup=admin_keyboard()
    )

# ---------- ПРОВЕРКА АДМИНА ПРИ ЗАПУСКЕ ----------
@dp.message_handler()
async def handle_all_messages(message: types.Message):
    if db.is_admin(message.from_user.id):
        await message.answer(
            "Используйте кнопки для навигации:",
            reply_markup=admin_keyboard()
        )
    else:
        await message.answer(
            "Используйте /start для начала работы с ботом"
        )

# ---------- ЗАПУСК ----------
async def on_startup(_):
    db.db_start()
    
    # Добавляем главного админа при запуске
    if not db.is_admin(MAIN_ADMIN_ID):
        db.add_admin(MAIN_ADMIN_ID, "main_admin", MAIN_ADMIN_ID)
        print(f"✅ Главный админ добавлен: {MAIN_ADMIN_ID}")
    
    await bot.delete_webhook()
    await set_default_commands(dp)
    print('Bot started successfully! 🚀')
    print(f'Bot: @{NICNAME_BOT}')
    print(f'Main admin: {MAIN_ADMIN_ID}')

async def on_shutdown(_):
    print('Bot stopped!')
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == '__main__':
    executor.start_polling(
        dp, 
        skip_updates=True, 
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )