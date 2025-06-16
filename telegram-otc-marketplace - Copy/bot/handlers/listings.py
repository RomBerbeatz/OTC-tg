from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "my_listings")
async def my_listings(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 <b>Мои объявления</b>\n\n"
        "Функция в разработке...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ])
    )