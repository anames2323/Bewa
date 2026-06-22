import logging
import sys
from aiogram import Bot, types, Dispatcher, executor
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

async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота")
    ])

@dp.message_handler(text='Отмена ❌', state='*')
async def back(message: types.Message, state: FSMContext):
    await message.answer("Вы отменили отправку сообщения!", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

class Send_Message(StatesGroup):
    text = State()

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    db.db_start()
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

@dp.message_handler(state=Send_Message.text)
async def state_message(message: types.Message, state: FSMContext):
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
    await Send_Message.text.set()
    user = callback.data.split('|')[1]
    await state.update_data(name=user)
    await callback.message.delete()
    await callback.message.answer(
        'Напиши сообщение человеку, который отправил тебе сообщение\n\n'
        'Напиши своё сообщение:', 
        reply_markup=kb_back
    )

async def on_startup(_):
    await set_default_commands(dp)
    print('Bot started successfully! 🚀')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)