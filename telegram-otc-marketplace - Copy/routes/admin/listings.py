from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, Listing, Category
from app.schemas.admin import AdminListingResponse, AdminListingUpdate
from app.middleware.admin import require_moderator

router = APIRouter(prefix="/admin/listings", tags=["Admin - Listings"])

@router.get("/", response_model=List[AdminListingResponse])
def get_listings(
    search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    owner_id: Optional[int] = Query(None, description="Фильтр по владельцу"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    is_featured: Optional[bool] = Query(None, description="Фильтр по рекомендуемым"),
    date_from: Optional[datetime] = Query(None, description="Дата создания от"),
    date_to: Optional[datetime] = Query(None, description="Дата создания до"),
    min_price: Optional[int] = Query(None, description="Минимальная цена"),
    max_price: Optional[int] = Query(None, description="Максимальная цена"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Порядок сортировки (asc/desc)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_moderator)
):
    """Получение списка объявлений с фильтрами и поиском"""
    
    # Базовый запрос с JOIN для получения данных владельца и категории
    query = db.query(Listing).options(
        joinedload(Listing.owner),
        joinedload(Listing.category)
    )
    
    # Применение фильтров
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Listing.title.ilike(search_term),
                Listing.description.ilike(search_term),
                Listing.location.ilike(search_term)
            )
        )
    
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    
    if owner_id:
        query = query.filter(Listing.owner_id == owner_id)
    
    if is_active is not None:
        query = query.filter(Listing.is_active == is_active)
    
    if is_featured is not None:
        query = query.filter(Listing.is_featured == is_featured)
    
    if date_from:
        query = query.filter(Listing.created_at >= date_from)
    
    if date_to:
        query = query.filter(Listing.created_at <= date_to)
    
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    
    # Сортировка
    if hasattr(Listing, sort_by):
        order_column = getattr(Listing, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Пагинация
    total = query.count()
    offset = (page - 1) * per_page
    listings = query.offset(offset).limit(per_page).all()
    
    # Формирование ответа
    listings_response = []
    for listing in listings:
        listing_dict = {
            "id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "price": listing.price,
            "category_id": listing.category_id,
            "owner_id": listing.owner_id,
            "location": listing.location,
            "contact_phone": listing.contact_phone,
            "contact_email": listing.contact_email,
            "is_active": listing.is_active,
            "is_featured": listing.is_featured,
            "views_count": listing.views_count,
            "created_at": listing.created_at,
            "updated_at": listing.updated_at,
            "owner_username": listing.owner.username,
            "category_name": listing.category.name
        }
        listings_response.append(AdminListingResponse(**listing_dict))
    
    return listings_response

@router.get("/{listing_id}", response_model=AdminListingResponse)
def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_moderator)
):
    """Получение информации об объявлении"""
    
    listing = db.query(Listing).options(
        joinedload(Listing.owner),
        joinedload(Listing.category)
    ).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )
    
    listing_dict = {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "price": listing.price,
        "category_id": listing.category_id,
        "owner_id": listing.owner_id,
        "location": listing.location,
        "contact_phone": listing.contact_phone,
        "contact_email": listing.contact_email,
        "is_active": listing.is_active,
        "is_featured": listing.is_featured,
        "views_count": listing.views_count,
        "created_at": listing.created_at,
        "updated_at": listing.updated_at,
        "owner_username": listing.owner.username,
        "category_name": listing.category.name
    }
    
    return AdminListingResponse(**listing_dict)

@router.put("/{listing_id}", response_model=AdminListingResponse)
def update_listing(
    listing_id: int,
    listing_data: AdminListingUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_moderator)
):
    """Обновление объявления"""
    
    db_listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not db_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )
    
    # Проверка существования категории и владельца
    update_data = listing_data.dict(exclude_unset=True)
    
    if "category_id" in update_data:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Категория не найдена"
            )
    
    if "owner_id" in update_data:
        owner = db.query(User).filter(User.id == update_data["owner_id"]).first()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Владелец не найден"
            )
    
    # Применение обновлений
    for field, value in update_data.items():
        setattr(db_listing, field, value)
    
    db_listing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_listing)
    
    # Загрузка связанных данных
    db_listing = db.query(Listing).options(
        joinedload(Listing.owner),
        joinedload(Listing.category)
    ).filter(Listing.id == listing_id).first()
    
    listing_dict = {
        "id": db_listing.id,
        "title": db_listing.title,
        "description": db_listing.description,
        "price": db_listing.price,
        "category_id": db_listing.category_id,
        "owner_id": db_listing.owner_id,
        "location": db_listing.location,
        "contact_phone": db_listing.contact_phone,
        "contact_email": db_listing.contact_email,
        "is_active": db_listing.is_active,
        "is_featured": db_listing.is_featured,
        "views_count": db_listing.views_count,
        "created_at": db_listing.created_at,
        "updated_at": db_listing.updated_at,
        "owner_username": db_listing.owner.username,
        "category_name": db_listing.category.name
    }
    
    return AdminListingResponse(**listing_dict)

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_moderator)
):
    """Удаление объявления"""
    
    db_listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not db_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )
    
    db.delete(db_listing)
    db.commit()

@router.patch("/{listing_id}/toggle-active")
def toggle_listing_active(
    listing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_moderator)
):
    """Переключение активности объявления"""
    
    db_listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not db_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )
    
    db_listing.is_active = not db_listing.is_active
    db_listing.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Объявление {'активировано' if db_listing.is_active else 'деактивировано'}"}

@router.patch("/{listing_id}/toggle-featured")
def toggle_listing_featured(
    listing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_moderator)
):
    """Переключение рекомендуемого статуса объявления"""
    
    db_listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not db_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )
    
    db_listing.is_featured = not db_listing.is_featured
    db_listing.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Объявление {'добавлено в рекомендуемые' if db_listing.is_featured else 'убрано из рекомендуемых'}"}