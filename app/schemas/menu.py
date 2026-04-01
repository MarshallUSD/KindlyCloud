"""Menu schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from pydantic import ConfigDict

from app.models.menu import Meal, MenuStatus


class MenuItemCreateRequest(BaseModel):
    """Create menu item request."""
    meal: Meal
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    calories: Optional[int] = Field(None, ge=0)


class MenuItemResponse(BaseModel):
    """Menu item response schema."""
    model_config = ConfigDict(from_attributes=True)

    menu_item_id: str
    meal: Meal
    title: str
    description: Optional[str]
    calories: Optional[int]
    created_at: datetime


class MenuCreateRequest(BaseModel):
    """Create menu request."""
    menu_date: date
    items: List[MenuItemCreateRequest]
    group_ids: Optional[List[str]] = None  # IDs of groups to assign menu
    status: MenuStatus = MenuStatus.PUBLISHED
    notes: Optional[str] = None


class MenuResponse(BaseModel):
    """Menu response schema."""
    model_config = ConfigDict(from_attributes=True)

    menu_id: str
    kindergarten_id: str
    menu_date: date
    created_by_user_id: str
    status: MenuStatus
    published_at: Optional[datetime]
    notes: Optional[str]
    items: List[MenuItemResponse]
    created_at: datetime
    updated_at: datetime
