from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import Config

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть торговую площадку", callback_data="open_marketplace")],
        [InlineKeyboardButton(text="📋 Мои объявления", callback_data="my_listings")],
        [InlineKeyboardButton(text="💬 Сообщения", callback_data="messages")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

def get_web_app_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🌐 Открыть веб-интерфейс",
            web_app=WebAppInfo(url=Config.WEB_APP_URL)
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def get_listings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать объявление", callback_data="create_listing")],
        [InlineKeyboardButton(text="👀 Просмотреть все", callback_data="view_all_listings")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])