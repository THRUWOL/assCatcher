from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
import json
import os
import random
app = FastAPI()

# Создаем файл data.json, если его нет
if not os.path.exists("data.json"):
    with open("data.json", "w") as f:
        json.dump({"players": [], "game_state": {"jopka_owner": None}}, f)

# Раздаём статику из папки static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/auth")
async def auth(request: Request):
    """
    Обрабатывает данные авторизации из Telegram Mini App.
    """
    try:
        # Получаем данные пользователя
        user_data = await request.json()
        print("Полученные данные:", user_data)  # Логируем данные

        # Сохраняем пользователя в игру
        with open("data.json", "r+") as f:
            data = json.load(f)
            # Проверяем, существует ли игрок уже
            if any(p["id"] == user_data["id"] for p in data["players"]):
                return #{"message": "Вы уже зарегистрированы!"}

            # Добавляем нового игрока
            new_player = {
                "id": user_data["id"],
                "username": user_data["username"],
                "has_jopka": False,
                "wins": 0,
                "photo_url": user_data.get("photo_url")
            }
            data["players"].append(new_player)
            # Если это первый игрок, он получает "Жопку КАЛа"
            if len(data["players"]) == 1:
                new_player["has_jopka"] = True
                data["game_state"]["jopka_owner"] = user_data["id"]
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        return #{"message": "Игрок добавлен!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/game_state")
async def get_game_state():
    """
    Возвращает текущее состояние игры.
    """
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении данных: {str(e)}")


@app.post("/auto_challenge/{challenger_id}")
async def auto_challenge(challenger_id: str):
    """
    Обрабатывает вызов владельцу "Жопки КАЛа".
    """
    print(f"Получен запрос на вызов от игрока {challenger_id}")  # Логируем запрос

    try:
        with open("data.json", "r+") as f:
            data = json.load(f)
            print("Текущие данные игры:", data)  # Логируем данные из файла

            # Проверяем, есть ли игроки в игре
            challenger = next((p for p in data["players"] if str(p["id"]) == challenger_id), None)
            if not challenger:
                raise HTTPException(status_code=400, detail="Игрок не найден")

            jopka_owner_id = data["game_state"]["jopka_owner"]
            if not jopka_owner_id:
                raise HTTPException(status_code=400, detail="Владелец 'Жопки КАЛа' не определён")

            opponent = next((p for p in data["players"] if str(p["id"]) == str(jopka_owner_id)), None)
            if not opponent:
                raise HTTPException(status_code=400, detail="Владелец 'Жопки КАЛа' не найден")
            if not opponent["has_jopka"]:
                raise HTTPException(status_code=400, detail="У противника нет 'Жопки КАЛа'")

            # Проверяем, что вызывающий игрок не является владельцем "Жопки КАЛа"
            if str(challenger_id) == str(jopka_owner_id):
                raise HTTPException(status_code=400, detail="Вы уже владеете 'Жопкой КАЛа' и не можете бросить вызов самому себе")

            # Рандомный шанс отобрать "Жопку КАЛа"
            success = random.random() < 0.5
            if success:
                # Успех
                challenger["has_jopka"] = True
                opponent["has_jopka"] = False
                data["game_state"]["jopka_owner"] = int(challenger_id)  # Сохраняем ID как число
                challenger["wins"] += 1
                message = "Вы завладели 'Жопкой КАЛа'!"
            else:
                # Неудача
                opponent["wins"] += 1
                message = "Вы не смогли завладеть 'Жопкой КАЛа'. Владелец получает победное очко!"

            # Сохраняем обновлённые данные
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

        return {"message": message, "success": success}

    except Exception as e:
        print(f"Ошибка: {str(e)}")  # Логируем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке вызова: {str(e)}")

@app.get("/")
async def read_root():
    """
    Корневой эндпоинт для проверки работоспособности сервера.
    """
    return {"message": "Сервер работает! Открывай /static/index.html"}