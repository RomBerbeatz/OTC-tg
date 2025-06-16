from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.message.edit_text(
        "👤 <b>Ваш профиль</b>\n\n"
        f"Имя: {callback.from_user.first_name}\n"
        f"Username: @{callback.from_user.username or 'не указан'}\n"
        f"ID: {callback.from_user.id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ])
    )