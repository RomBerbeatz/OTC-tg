from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole

# Пользователи
class AdminUserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = None

class AdminUserResponse(AdminUserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    listings_count: int

    class Config:
        from_attributes = True

# Объявления
class AdminListingBase(BaseModel):
    title: str
    description: str
    price: int
    category_id: int
    location: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    is_featured: bool

class AdminListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    category_id: Optional[int] = None
    location: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    owner_id: Optional[int] = None

class AdminListingResponse(AdminListingBase):
    id: int
    owner_id: int
    views_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    owner_username: str
    category_name: str

    class Config:
        from_attributes = True

# Категории
class AdminCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool

class AdminCategoryCreate(AdminCategoryBase):
    pass

class AdminCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AdminCategoryResponse(AdminCategoryBase):
    id: int
    created_at: datetime
    listings_count: int

    class Config:
        from_attributes = True

# Статистика
class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_listings: int
    active_listings: int
    featured_listings: int
    total_categories: int
    users_today: int
    listings_today: int

# Поиск и фильтры
class AdminSearchFilters(BaseModel):
    search: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    page: int = 1
    per_page: int = 20