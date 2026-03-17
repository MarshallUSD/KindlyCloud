"""Menu models."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class Meal(str, Enum):
    """Meal type enumeration."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"


class Menu(Base):
    """Daily menu for a kindergarten."""
    __tablename__ = "menus"
    
    menu_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    menu_date = Column(Date, nullable=False, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten = relationship("Kindergarten", back_populates="menus")
    created_by_user = relationship("User", back_populates="menus_created", foreign_keys=[created_by_user_id])
    items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan")
    group_menus = relationship("GroupMenu", back_populates="menu", cascade="all, delete-orphan")


class MenuItem(Base):
    """Individual menu item within a menu."""
    __tablename__ = "menu_items"
    
    menu_item_id = Column(String, primary_key=True, index=True)
    menu_id = Column(String, ForeignKey("menus.menu_id"), nullable=False, index=True)
    meal = Column(SQLEnum(Meal), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    calories = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    menu = relationship("Menu", back_populates="items")


class GroupMenu(Base):
    """Assignment of menu to a group."""
    __tablename__ = "group_menus"
    
    group_menu_id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    menu_id = Column(String, ForeignKey("menus.menu_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="group_menus")
    menu = relationship("Menu", back_populates="group_menus")
