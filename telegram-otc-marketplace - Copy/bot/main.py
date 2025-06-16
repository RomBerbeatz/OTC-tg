from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.database import engine, create_tables
from app.routers import auth, listings, categories, users
from app.routers.admin import users as admin_users, listings as admin_listings, categories as admin_categories

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц при запуске
    create_tables()
    logger.info("Таблицы базы данных созданы")
    yield
    logger.info("Приложение завершает работу")

app = FastAPI(
    title="Доска объявлений API",
    description="API для доски объявлений с административной панелью",
    version="2.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обработчик глобальных исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Глобальная ошибка: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )

# Подключение роутов
app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(categories.router)
app.include_router(users.router)

# Административные роуты
app.include_router(admin_users.router)
app.include_router(admin_listings.router)
app.include_router(admin_categories.router)

@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в API доски объявлений!",
        "version": "2.0.0",
        "docs": "/docs",
        "admin": "Доступ к /admin/* только для администраторов"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-06-16T06:48:41Z"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)