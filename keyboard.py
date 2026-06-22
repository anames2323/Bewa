from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

kb_back = ReplyKeyboardMarkup(resize_keyboard=True)
kb1 = KeyboardButton('Отмена ❌')
kb_back.add(kb1)

def send_message(user_id):
    ikb_send_message = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Ответить 📩', callback_data=f'send|{user_id}')]
    ])
    return ikb_send_message