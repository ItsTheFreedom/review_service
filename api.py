import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import RedirectResponse
from database import engine, Base, SessionLocal, Review, Moderator
import schemas

# ‼️ ИМПОРТИРУЕМ ГОТОВОГО БОТА ИЗ bot.py ‼️
from bot import bot, dp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

Base.metadata.create_all(bind=engine)

# Эта магия запускает опрос Телеграма параллельно с работой сервера API
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🤖 Бот просыпается и подключается к Telegram...")
    bot_task = asyncio.create_task(dp.start_polling(bot))
    yield
    print("🛑 Сервер выключается, останавливаем бота...")
    bot_task.cancel()

app = FastAPI(
    title="Система модерации отзывов",
    description="Микросервис для сбора отзывов и их проверки модераторами через Telegram.",
    lifespan=lifespan # Подключаем нашу магию сюда
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Перенаправление с корня прямо в документацию
@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")

# 1. Метод на отправку отзыва
@app.post("/reviews/", response_model=schemas.ReviewResponse, tags=["Отзывы"], summary="Отправить новый отзыв")
async def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    db_review = Review(
        user_name=review.user_name,
        text=review.text,
        rating=review.rating,
        is_buyer=review.is_buyer
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    moderators = db.query(Moderator).filter(Moderator.is_receiving == True).all()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{db_review.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{db_review.id}")
        ]
    ])

    text_msg = (
        f"📝 <b>Новый отзыв на модерацию!</b>\n\n"
        f"👤 Автор: {db_review.user_name}\n"
        f"⭐ Оценка: {db_review.rating}/5\n"
        f"🛒 Подтвержденный покупатель: {'Да' if db_review.is_buyer else 'Нет'}\n\n"
        f"💬 Текст: {db_review.text}"
    )

    for mod in moderators:
        try:
            await bot.send_message(
                chat_id=mod.telegram_id,
                text=text_msg,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение модератору {mod.telegram_id}: {e}")

    return db_review

# 2. Метод на вывод списка всех одобренных отзывов
@app.get("/reviews/approved", response_model=List[schemas.ReviewResponse], tags=["Отзывы"], summary="Получить список одобренных отзывов")
def get_approved_reviews(db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.status == "approved").all()

# 3. Метод на вывод детальной информации по отзыву
@app.get("/reviews/{review_id}", response_model=schemas.ReviewResponse, tags=["Отзывы"], summary="Получить детали отзыва")
def get_review_details(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return review

# 4. Метод получения списка модераторов
@app.get("/moderators/", response_model=List[schemas.ModeratorResponse], tags=["Модераторы"], summary="Список всех модераторов")
def get_moderators(db: Session = Depends(get_db)):
    return db.query(Moderator).all()

# 5. Метод добавления модератора
@app.post("/moderators/", response_model=schemas.ModeratorResponse, tags=["Модераторы"], summary="Добавить нового модератора")
def create_moderator(mod: schemas.ModeratorCreate, db: Session = Depends(get_db)):
    db_mod = Moderator(telegram_id=mod.telegram_id, is_receiving=mod.is_receiving)
    db.add(db_mod)
    db.commit()
    db.refresh(db_mod)
    return db_mod