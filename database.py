from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

# Указываем путь к базе данных. SQLite создаст файл reviews.db прямо в папке проекта
SQLALCHEMY_DATABASE_URL = "sqlite:///./reviews.db"

# Создаем движок (engine) для подключения к БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем фабрику сессий (через них мы будем читать и писать данные)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для наших таблиц
Base = declarative_base()


# --- НАШИ ТАБЛИЦЫ ---

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)      # Имя автора
    text = Column(Text)                         # Текст отзыва
    rating = Column(Integer)                    # Оценка (1-5)
    is_buyer = Column(Boolean, default=False)   # Наша фича: реальный ли покупатель
    status = Column(String, default="pending")  # Статус: pending (ожидает), approved (одобрен), rejected (отклонен)


class Moderator(Base):
    __tablename__ = "moderators"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True) # ID модератора в Телеграм
    is_receiving = Column(Boolean, default=True)              # Готов ли получать отзывы