from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "messages")
async def messages(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 <b>Сообщения</b>\n\n"
        "У вас пока нет сообщений.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ])
    )