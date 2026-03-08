"""Menu repository."""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.menu import Menu, MenuItem, GroupMenu, Meal
from app.repositories.base import BaseRepository


class MenuRepository(BaseRepository):
    """Repository for Menu model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Menu)
    
    def get_by_id(self, menu_id: str) -> Optional[Menu]:
        """Get menu by menu_id."""
        return self.get_by_id_field('menu_id', menu_id)
    
    def get_by_kindergarten_and_date(self, kindergarten_id: str, menu_date: date) -> Optional[Menu]:
        """Get menu by kindergarten and date."""
        return self.db.query(Menu).filter(
            Menu.kindergarten_id == kindergarten_id,
            Menu.menu_date == menu_date
        ).first()
    
    def get_by_kindergarten(self, kindergarten_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Menu], int]:
        """Get menus by kindergarten."""
        total = self.db.query(func.count(Menu.menu_id)).filter(
            Menu.kindergarten_id == kindergarten_id
        ).scalar()
        records = self.db.query(Menu).filter(
            Menu.kindergarten_id == kindergarten_id
        ).offset(skip).limit(limit).order_by(Menu.menu_date.desc()).all()
        return records, total
    
    def create_menu(self, menu_id: str, kindergarten_id: str, menu_date: date,
                   created_by_user_id: str) -> Menu:
        """Create a new menu."""
        menu = Menu(
            menu_id=menu_id,
            kindergarten_id=kindergarten_id,
            menu_date=menu_date,
            created_by_user_id=created_by_user_id
        )
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)
        return menu
    
    def add_menu_item(self, menu_item_id: str, menu_id: str, meal: Meal,
                     title: str, description: Optional[str] = None,
                     calories: Optional[int] = None) -> MenuItem:
        """Add item to menu."""
        item = MenuItem(
            menu_item_id=menu_item_id,
            menu_id=menu_id,
            meal=meal,
            title=title,
            description=description,
            calories=calories
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def assign_menu_to_group(self, group_menu_id: str, group_id: str, menu_id: str) -> GroupMenu:
        """Assign menu to group."""
        group_menu = GroupMenu(
            group_menu_id=group_menu_id,
            group_id=group_id,
            menu_id=menu_id
        )
        self.db.add(group_menu)
        self.db.commit()
        self.db.refresh(group_menu)
        return group_menu
    
    def get_menu_for_group(self, group_id: str, menu_date: date) -> Optional[Menu]:
        """Get menu for a specific group on a date."""
        return self.db.query(Menu).join(
            GroupMenu, GroupMenu.menu_id == Menu.menu_id
        ).filter(
            GroupMenu.group_id == group_id,
            Menu.menu_date == menu_date
        ).first()
