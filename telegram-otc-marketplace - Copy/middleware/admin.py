from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models import User

def require_admin(current_user: User = Depends(get_current_user)):
    """Проверка прав администратора"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Требуются права администратора."
        )
    return current_user

def require_moderator(current_user: User = Depends(get_current_user)):
    """Проверка прав модератора или администратора"""
    if not current_user.is_moderator():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Требуются права модератора."
        )
    return current_user