from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Listing, UserRole
from app.schemas.admin import (
    AdminUserResponse, AdminUserCreate, AdminUserUpdate, 
    AdminSearchFilters, AdminStats
)
from app.middleware.admin import require_admin
from app.auth.password import get_password_hash
from app.utils.pagination import paginate

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Получение общей статистики"""
    today = datetime.utcnow().date()
    
    stats = {
        "total_users": db.query(func.count(User.id)).scalar(),
        "active_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
        "total_listings": db.query(func.count(Listing.id)).scalar(),
        "active_listings": db.query(func.count(Listing.id)).filter(Listing.is_active == True).scalar(),
        "featured_listings": db.query(func.count(Listing.id)).filter(Listing.is_featured == True).scalar(),
        "users_today": db.query(func.count(User.id)).filter(
            func.date(User.created_at) == today
        ).scalar(),
        "listings_today": db.query(func.count(Listing.id)).filter(
            func.date(Listing.created_at) == today
        ).scalar(),
    }
    
    return AdminStats(**stats)

@router.get("/", response_model=List[AdminUserResponse])
def get_users(
    search: Optional[str] = Query(None, description="Поиск по имени пользователя, email или полному имени"),
    role: Optional[UserRole] = Query(None, description="Фильтр по роли"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    is_verified: Optional[bool] = Query(None, description="Фильтр по верификации"),
    date_from: Optional[datetime] = Query(None, description="Дата создания от"),
    date_to: Optional[datetime] = Query(None, description="Дата создания до"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Порядок сортировки (asc/desc)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Получение списка пользователей с фильтрами и поиском"""
    
    # Базовый запрос с подсчётом объявлений
    query = db.query(
        User,
        func.count(Listing.id).label('listings_count')
    ).outerjoin(Listing).group_by(User.id)
    
    # Применение фильтров
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    if date_from:
        query = query.filter(User.created_at >= date_from)
    
    if date_to:
        query = query.filter(User.created_at <= date_to)
    
    # Сортировка
    if hasattr(User, sort_by):
        order_column = getattr(User, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Пагинация
    total = query.count()
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()
    
    # Формирование ответа
    users_response = []
    for user, listings_count in results:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
            "listings_count": listings_count
        }
        users_response.append(AdminUserResponse(**user_dict))
    
    return users_response

@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Получение информации о пользователе"""
    result = db.query(
        User,
        func.count(Listing.id).label('listings_count')
    ).outerjoin(Listing).filter(User.id == user_id).group_by(User.id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user, listings_count = result
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login,
        "listings_count": listings_count
    }
    
    return AdminUserResponse(**user_dict)

@router.post("/", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Создание нового пользователя"""
    
    # Проверка уникальности
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создание пользователя
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        is_active=user_data.is_active,
        is_verified=user_data.is_verified
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    user_dict = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "phone": db_user.phone,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
        "last_login": db_user.last_login,
        "listings_count": 0
    }
    
    return AdminUserResponse(**user_dict)

@router.put("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Обновление пользователя"""
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверка уникальности при обновлении
    update_data = user_data.dict(exclude_unset=True)
    
    if "username" in update_data:
        existing_user = db.query(User).filter(
            and_(User.username == update_data["username"], User.id != user_id)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )
    
    if "email" in update_data:
        existing_user = db.query(User).filter(
            and_(User.email == update_data["email"], User.id != user_id)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
    
    # Обновление пароля
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Применение обновлений
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    
    # Получение количества объявлений
    listings_count = db.query(func.count(Listing.id)).filter(Listing.owner_id == user_id).scalar()
    
    user_dict = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "phone": db_user.phone,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
        "last_login": db_user.last_login,
        "listings_count": listings_count
    }
    
    return AdminUserResponse(**user_dict)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Удаление пользователя"""
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Нельзя удалить самого себя
    if db_user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    
    db.delete(db_user)
    db.commit()

@router.patch("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Переключение активности пользователя"""
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    if db_user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить свой статус активности"
        )
    
    db_user.is_active = not db_user.is_active
    db_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Пользователь {'активирован' if db_user.is_active else 'деактивирован'}"}