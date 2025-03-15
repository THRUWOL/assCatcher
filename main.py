import random

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель игрока
class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    has_jopka = Column(Boolean, default=False)
    wins = Column(Integer, default=0)

# Создание таблиц
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def read_root():
    """
    Обрабатывает GET и HEAD запросы на корневой URL.
    """
    return {"message": "Сервер работает! Открывай /static/index.html"}



@app.post("/auth")
async def auth(player_data: dict):
    db = next(get_db())
    existing_player = db.query(Player).filter(Player.id == player_data["id"]).first()
    if existing_player:
        return {"message": "Вы уже зарегистрированы!"}

    new_player = Player(
        id=player_data["id"],
        username=player_data["username"],
        has_jopka=False,
        wins=0
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    # Если это первый игрок, он получает "Жопку КАЛа"
    if db.query(Player).count() == 1:
        new_player.has_jopka = True
        db.commit()

    return {"message": "Игрок добавлен!"}


@app.get("/game_state")
async def get_game_state():
    db = next(get_db())
    players = db.query(Player).all()
    game_state = {
        "players": [
            {
                "id": player.id,
                "username": player.username,
                "has_jopka": player.has_jopka,
                "wins": player.wins
            } for player in players
        ],
        "jopka_owner": next((p.id for p in players if p.has_jopka), None)
    }
    return game_state


@app.post("/auto_challenge/{challenger_id}")
async def auto_challenge(challenger_id: int):
    db = next(get_db())
    challenger = db.query(Player).filter(Player.id == challenger_id).first()
    jopka_owner = db.query(Player).filter(Player.has_jopka == True).first()

    if not challenger or not jopka_owner:
        raise HTTPException(status_code=400, detail="Ошибка в данных игрока")

    if challenger.id == jopka_owner.id:
        raise HTTPException(status_code=400, detail="Вы уже владеете 'Жопкой КАЛа'")

    success = random.random() < 0.5
    if success:
        challenger.has_jopka = True
        jopka_owner.has_jopka = False
        challenger.wins += 1
    else:
        jopka_owner.wins += 1

    db.commit()
    return {"message": "Вызов выполнен", "success": success}

@app.get("/")
async def read_root():
    """
    Корневой эндпоинт для проверки работоспособности сервера.
    """
    return {"message": "Сервер работает! Открывай /static/index.html"}