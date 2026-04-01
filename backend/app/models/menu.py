"""Menu models."""
from enum import Enum

from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class Meal(str, Enum):
    """Meal type enumeration."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"


class MenuStatus(str, Enum):
    """Publishing state for a menu."""

    DRAFT = "draft"
    PUBLISHED = "published"


class Menu(Base):
    """Daily menu for a kindergarten."""
    __tablename__ = "menus"
    
    menu_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    menu_date = Column(Date, nullable=False, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum(MenuStatus, name="menu_status", native_enum=False),
        nullable=False,
        default=MenuStatus.PUBLISHED,
    )
    published_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
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
    created_at = Column(DateTime, default=utcnow, nullable=False)
    
    # Relationships
    menu = relationship("Menu", back_populates="items")


class GroupMenu(Base):
    """Assignment of menu to a group."""
    __tablename__ = "group_menus"
    __table_args__ = (
        UniqueConstraint("group_id", "menu_id", name="uq_group_menus_group_menu"),
    )
    
    group_menu_id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    menu_id = Column(String, ForeignKey("menus.menu_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="group_menus")
    menu = relationship("Menu", back_populates="group_menus")
