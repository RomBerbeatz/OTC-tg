from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import Category, Listing, User
from app.schemas.admin import (
    AdminCategoryResponse, AdminCategoryCreate, AdminCategoryUpdate
)
from app.middleware.admin import require_admin

router = APIRouter(prefix="/admin/categories", tags=["Admin - Categories"])

@router.get("/", response_model=List[AdminCategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Получение списка всех категорий"""
    
    categories = db.query(
        Category,
        func.count(Listing.id).label('listings_count')
    ).outerjoin(Listing).group_by(Category.id).order_by(Category.name).all()
    
    categories_response = []
    for category, listings_count in categories:
        category_dict = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "is_active": category.is_active,
            "created_at": category.created_at,
            "listings_count": listings_count
        }
        categories_response.append(AdminCategoryResponse(**category_dict))
    
    return categories_response

@router.get("/{category_id}", response_model=AdminCategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Получение информации о категории"""
    
    result = db.query(
        Category,
        func.count(Listing.id).label('listings_count')
    ).outerjoin(Listing).filter(Category.id == category_id).group_by(Category.id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    category, listings_count = result
    category_dict = {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "listings_count": listings_count
    }
    
    return AdminCategoryResponse(**category_dict)

@router.post("/", response_model=AdminCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: AdminCategoryCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Создание новой категории"""
    
    # Проверка уникальности названия
    if db.query(Category).filter(Category.name == category_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким названием уже существует"
        )
    
    db_category = Category(
        name=category_data.name,
        description=category_data.description,
        is_active=category_data.is_active
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    category_dict = {
        "id": db_category.id,
        "name": db_category.name,
        "description": db_category.description,
        "is_active": db_category.is_active,
        "created_at": db_category.created_at,
        "listings_count": 0
    }
    
    return AdminCategoryResponse(**category_dict)

@router.put("/{category_id}", response_model=AdminCategoryResponse)
def update_category(
    category_id: int,
    category_data: AdminCategoryUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Обновление категории"""
    
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверка уникальности названия при обновлении
    update_data = category_data.dict(exclude_unset=True)
    
    if "name" in update_data:
        existing_category = db.query(Category).filter(
            Category.name == update_data["name"],
            Category.id != category_id
        ).first()
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Категория с таким названием уже существует"
            )
    
    # Применение обновлений
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    
    # Получение количества объявлений
    listings_count = db.query(func.count(Listing.id)).filter(
        Listing.category_id == category_id
    ).scalar()
    
    category_dict = {
        "id": db_category.id,
        "name": db_category.name,
        "description": db_category.description,
        "is_active": db_category.is_active,
        "created_at": db_category.created_at,
        "listings_count": listings_count
    }
    
    return AdminCategoryResponse(**category_dict)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Удаление категории"""
    
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверка наличия объявлений в категории
    listings_count = db.query(func.count(Listing.id)).filter(
        Listing.category_id == category_id
    ).scalar()
    
    if listings_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя удалить категорию, в которой есть объявления ({listings_count})"
        )
    
    db.delete(db_category)
    db.commit()