from pydantic import BaseModel, Field

# Схема для получения данных от пользователя при создании отзыва
class ReviewCreate(BaseModel):
    user_name: str
    text: str
    rating: int = Field(ge=1, le=5)  # Оценка строго от 1 до 5
    is_buyer: bool = False

# Схема для отправки ответа (возвращаем данные с ID и статусом)
class ReviewResponse(ReviewCreate):
    id: int
    status: str

    model_config = {"from_attributes": True}

class ModeratorCreate(BaseModel):
    telegram_id: int
    is_receiving: bool = True

class ModeratorResponse(ModeratorCreate):
    id: int
    model_config = {"from_attributes": True}