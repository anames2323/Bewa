from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Кнопка "Отмена"
kb_back = ReplyKeyboardMarkup(resize_keyboard=True)
kb1 = KeyboardButton('Отмена ❌')
kb_back.add(kb1)

# Главная клавиатура для админа
def admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('📊 Статистика'),
        KeyboardButton('📢 Управление каналами')
    )
    keyboard.add(
        KeyboardButton('👥 Управление админами'),
        KeyboardButton('📨 Рассылка')
    )
    keyboard.add(
        KeyboardButton('🔙 Выйти из админки')
    )
    return keyboard

# Клавиатура управления каналами
def channels_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton('➕ Добавить канал', callback_data='add_channel'),
        InlineKeyboardButton('📋 Список каналов', callback_data='list_channels'),
        InlineKeyboardButton('❌ Удалить канал', callback_data='remove_channel'),
        InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    )
    return keyboard

# Клавиатура управления админами
def admins_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton('➕ Добавить админа', callback_data='add_admin'),
        InlineKeyboardButton('📋 Список админов', callback_data='list_admins'),
        InlineKeyboardButton('❌ Удалить админа', callback_data='remove_admin'),
        InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    )
    return keyboard

# Кнопка для ответа на сообщение
def send_message(user_id):
    ikb_send_message = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Ответить 📩', callback_data=f'send|{user_id}')]
    ])
    return ikb_send_message
