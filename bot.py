from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from config import TOKEN
from aiogram import F # Магический фильтр aiogram для удобного поиска
from database import SessionLocal, Review, Moderator
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
BOT_TOKEN = TOKEN

# Инициализируем бота и диспетчер (обработчик событий)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Создаем постоянную клавиатуру с одной кнопкой
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏸ Остановить отзывы")]],
        resize_keyboard=True
    )

    await message.answer(
        f"Привет! Система модерации отзывов.\n"
        f"Твой Telegram ID: {message.from_user.id}\n\n"
        f"Используй кнопку ниже, чтобы управлять потоком отзывов.",
        reply_markup=kb
    )

# Ловим любое нажатие кнопки, data которой начинается на "approve_" или "reject_"
@dp.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def process_review_moderation(callback: types.CallbackQuery):
    # Разделяем строку, например "approve_1" -> action = "approve", review_id = "1"
    action, review_id_str = callback.data.split("_")
    review_id = int(review_id_str)

    # Открываем сессию базы данных
    db = SessionLocal()
    try:
        # Ищем отзыв в базе по ID
        review = db.query(Review).filter(Review.id == review_id).first()

        if not review:
            await callback.answer("Ошибка: Отзыв не найден в базе!", show_alert=True)
            return

        # Меняем статус в зависимости от нажатой кнопки
        if action == "approve":
            review.status = "approved"
            result_text = "✅ <b>ОДОБРЕН</b>"
        else:
            review.status = "rejected"
            result_text = "❌ <b>ОТКЛОНЕН</b>"

        # Сохраняем изменения в базу
        db.commit()

        # Уведомляем Телеграм, что мы обработали нажатие (чтобы часики на кнопке пропали)
        await callback.answer(f"Отзыв {review_id} обработан!")

        # Изменяем исходное сообщение: берем старый текст (с сохранением HTML) и дописываем вердикт
        # Важно: мы не передаем reply_markup, поэтому кнопки исчезнут!
        new_text = f"{callback.message.html_text}\n\n➖➖➖➖➖➖\n{result_text}"
        await callback.message.edit_text(text=new_text, parse_mode="HTML")

    finally:
        # Обязательно закрываем соединение с БД
        db.close()


# Ловим сообщения с текстом наших кнопок
@dp.message(F.text.in_({"⏸ Остановить отзывы", "▶️ Возобновить отзывы"}))
async def toggle_receiving(message: types.Message):
    db = SessionLocal()
    try:
        # Ищем модератора в базе
        mod = db.query(Moderator).filter(Moderator.telegram_id == message.from_user.id).first()

        if not mod:
            await message.answer("Ошибка: Твой ID не найден в таблице модераторов!")
            return

        # Инвертируем статус: если был True, станет False, и наоборот
        mod.is_receiving = not mod.is_receiving
        db.commit()

        # Меняем текст кнопки и сообщение в зависимости от нового статуса
        if mod.is_receiving:
            btn_text = "⏸ Остановить отзывы"
            status_msg = "✅ Прием отзывов <b>ВОЗОБНОВЛЕН</b>. Ты снова в игре!"
        else:
            btn_text = "▶️ Возобновить отзывы"
            status_msg = "⛔️ Прием отзывов <b>ОСТАНОВЛЕН</b>. Отдыхай!"

        # Обновляем клавиатуру у пользователя
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn_text)]],
            resize_keyboard=True
        )
        await message.answer(status_msg, reply_markup=kb, parse_mode="HTML")

    finally:
        db.close()
