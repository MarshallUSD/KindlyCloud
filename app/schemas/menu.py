"""Menu schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from app.models.menu import Meal


class MenuItemCreateRequest(BaseModel):
    """Create menu item request."""
    meal: Meal
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    calories: Optional[int] = Field(None, ge=0)


class MenuItemResponse(BaseModel):
    """Menu item response schema."""
    menu_item_id: str
    meal: Meal
    title: str
    description: Optional[str]
    calories: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MenuCreateRequest(BaseModel):
    """Create menu request."""
    menu_date: date
    items: List[MenuItemCreateRequest]
    group_ids: Optional[List[str]] = None  # IDs of groups to assign menu


class MenuResponse(BaseModel):
    """Menu response schema."""
    menu_id: str
    kindergarten_id: str
    menu_date: date
    created_by_user_id: str
    items: List[MenuItemResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True
