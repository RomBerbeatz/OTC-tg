# Telegram OTC Marketplace Bot

Telegram бот с веб-интерфейсом для торговой площадки ОТС (Over-The-Counter) между пользователями.

## Возможности

### Telegram Bot
- 🤖 Интуитивный интерфейс с инлайн-кнопками
- 📝 Создание и управление объявлениями
- 💬 Система личных сообщений между пользователями
- 👤 Профили пользователей с рейтингом
- 📱 Интеграция с веб-интерфейсом

### Веб-интерфейс
- 🌐 Современный адаптивный дизайн
- 🔍 Поиск и фильтрация объявлений
- 📂 Категоризация (аккаунты, каналы, другое)
- 💬 Быстрая связь с продавцами
- 📱 Telegram WebApp интеграция

## Установка и настройка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd telegram-otc-marketplace
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env`:
```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///marketplace.db
SECRET_KEY=your-secret-key-here
WEB_APP_URL=https://your-domain.com
ADMIN_IDS=123456789,987654321
```

### 4. Запуск бота
```bash
python bot/main.py
```

### 5. Запуск веб-сервера
```bash
python web/app.py
```

## Структура проекта

```
telegram-otc-marketplace/
├── bot/                    # Telegram бот
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/         # Клавиатуры
│   └── utils/            # Утилиты
├── web/                   # Веб-интерфейс
│   ├── static/           # Статические файлы
│   └── templates/        # HTML шаблоны
├── database/              # Модели БД
└── config.py             # Конфигурация
```

## API Endpoints

### `/api/listings`
- **GET** - Получение списка объявлений
- Параметры: `category`, `search`, `page`, `per_page`

### `/api/contact_seller`
- **POST** - Отправка сообщения продавцу
- Тело: `listing_id`, `message`, `user_id`

## Деплой

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot/main.py"]
```

### Nginx конфигурация для веб-интерфейса
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Безопасность

- ✅ Валидация данных пользователей
- ✅ Защита от SQL-инъекций (SQLAlchemy ORM)
- ✅ Ограничение доступа к админ-функциям
- ✅ Санитизация пользовательского контента

## Лицензия

MIT License