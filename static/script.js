const API_URL = "https://asscatcher.onrender.com"; // Адрес вашего сервера
let currentUser = null;

// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;

// Функция для отправки данных пользователя на сервер
async function sendUserDataToServer(userData) {
    try {
        const response = await fetch(`${API_URL}/auth`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(userData),
        });

        if (!response.ok) {
            throw new Error("Ошибка при регистрации игрока");
        }

        const data = await response.json();
        alert(data.message);
        fetchGameState();
    } catch (error) {
        console.error("Ошибка:", error);
    }
}

// Функция для получения состояния игры
async function fetchGameState() {
    const response = await fetch(`${API_URL}/game_state`);
    const data = await response.json();
    renderGame(data);
}

// Функция для периодического опроса состояния игры
function pollGameState() {
    setInterval(async () => {
        await fetchGameState();
    }, 5000); // Опрос каждые 5 секунд
}

// Функция для отображения игры
function renderGame(data) {
    const gameDiv = document.getElementById("game");
    gameDiv.innerHTML = "";

    // Показываем рейтинг
    gameDiv.innerHTML += "<h2>Рейтинг:</h2>";
    const rating = data.players.sort((a, b) => b.wins - a.wins);
    rating.forEach(player => {
        const avatarUrl = `https://robohash.org/${player.username}.png`; // Генерируем аватарку через Robohash

        gameDiv.innerHTML += `
            <div class="player ${player.has_jopka ? 'winner' : ''}">
                <img src="${avatarUrl}" alt="${player.username}">
                <div class="player-name">${player.username}</div>
                <div class="player-wins">Побед: ${player.wins}</div>
            </div>
        `;
    });

    // Добавляем кнопку для броска вызова
    if (currentUser && data.players.length > 1) {
        const isDisabled = currentUser.id === data.game_state.jopka_owner;

        gameDiv.innerHTML += `
            <button 
                onclick="${!isDisabled ? 'challenge()' : ''}" 
                ${isDisabled ? 'disabled' : ''}
            >
                ${isDisabled ? 'У вас уже есть жопка!' : 'Бросить вызов!'}
            </button>
        `;
    }
}

// Функция для броска вызова
async function challenge() {
    const response = await fetch(`${API_URL}/auto_challenge/${currentUser.id}`, { method: "POST" });
    if (!response.ok) {
        const errorData = await response.json();
        alert(`Ошибка: ${errorData.detail}`);
        return;
    }
    const result = await response.json();
    alert(result.message);
    fetchGameState(); // Обновляем интерфейс после вызова
}

// Инициализация приложения
function initTelegramAuth() {
    tg.ready(); // Уведомляем Telegram, что приложение готово

    // Получаем данные пользователя из Telegram WebApp
    const userData = {
        id: String(tg.initDataUnsafe.user.id), // Приводим ID к строке
        username: tg.initDataUnsafe.user.username || `${tg.initDataUnsafe.user.first_name} ${tg.initDataUnsafe.user.last_name || ""}`,
        photo_url: tg.initDataUnsafe.user.photo_url || null,
    };

    // Сохраняем текущего пользователя
    currentUser = userData;

    // Отправляем данные на сервер
    sendUserDataToServer(userData);

    // Скрываем кнопку входа
    document.getElementById("login").style.display = "none";

    // Запускаем опрос состояния игры
    pollGameState();
}

// Проверяем, есть ли данные пользователя
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    initTelegramAuth();
} else {
    // Если пользователь не авторизован, показываем кнопку входа
    document.getElementById("login").style.display = "block";
}

// Загружаем состояние игры
fetchGameState();