from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User
from bot.keyboards.inline import get_main_menu_keyboard, get_web_app_keyboard

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    db = next(get_db())
    
    # Проверяем, есть ли пользователь в БД
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    
    if not user:
        # Создаем нового пользователя
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        db.add(user)
        db.commit()
        
        welcome_text = (
            "🎉 <b>Добро пожаловать в OTC Marketplace!</b>\n\n"
            "Здесь вы можете:\n"
            "🔹 Покупать и продавать аккаунты\n"
            "🔹 Торговать каналами\n"
            "🔹 Обмениваться подарками\n\n"
            "Выберите действие из меню ниже:"
        )
    else:
        welcome_text = (
            f"👋 С возвращением, <b>{user.first_name}!</b>\n\n"
            "Что будем делать сегодня?"
        )
    
    db.close()
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "open_marketplace")
async def open_marketplace(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌐 <b>Веб-интерфейс торговой площадки</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть полный интерфейс торговой площадки:",
        reply_markup=get_web_app_keyboard()
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )
    )