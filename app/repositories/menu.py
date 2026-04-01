"""Menu repository."""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.menu import Menu, MenuItem, GroupMenu, Meal, MenuStatus
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
    
    def create_menu(
        self,
        menu_id: str,
        kindergarten_id: str,
        menu_date: date,
        created_by_user_id: str,
        *,
        status: MenuStatus,
        published_at=None,
        notes: Optional[str] = None,
    ) -> Menu:
        """Create a new menu."""
        menu = Menu(
            menu_id=menu_id,
            kindergarten_id=kindergarten_id,
            menu_date=menu_date,
            created_by_user_id=created_by_user_id,
            status=status,
            published_at=published_at,
            notes=notes,
        )
        self.db.add(menu)
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
        return item
    
    def assign_menu_to_group(self, group_menu_id: str, group_id: str, menu_id: str) -> GroupMenu:
        """Assign menu to group."""
        group_menu = GroupMenu(
            group_menu_id=group_menu_id,
            group_id=group_id,
            menu_id=menu_id
        )
        self.db.add(group_menu)
        return group_menu

    def get_menu_for_group(
        self,
        group_id: str,
        menu_date: date,
        *,
        published_only: bool = False,
    ) -> Optional[Menu]:
        """Get menu for a specific group on a date."""
        query = self.db.query(Menu).join(GroupMenu, GroupMenu.menu_id == Menu.menu_id).filter(
            GroupMenu.group_id == group_id,
            Menu.menu_date == menu_date,
        )
        if published_only:
            query = query.filter(Menu.status == MenuStatus.PUBLISHED)
        return query.order_by(Menu.published_at.desc(), Menu.created_at.desc()).first()

    def list_group_menus_by_date(
        self,
        *,
        group_ids: list[str],
        menu_date: date,
        published_only: bool = False,
    ) -> list[tuple[str, Menu]]:
        """List menus for many groups on one date."""
        if not group_ids:
            return []

        query = (
            self.db.query(GroupMenu.group_id, Menu)
            .join(Menu, Menu.menu_id == GroupMenu.menu_id)
            .filter(
                GroupMenu.group_id.in_(group_ids),
                Menu.menu_date == menu_date,
            )
        )
        if published_only:
            query = query.filter(Menu.status == MenuStatus.PUBLISHED)
        return query.order_by(GroupMenu.group_id.asc(), Menu.published_at.desc(), Menu.created_at.desc()).all()

    def group_has_menu_on_date(self, *, group_id: str, menu_date: date) -> bool:
        """Check whether a group already has a menu assigned for the selected day."""
        return (
            self.db.query(GroupMenu)
            .join(Menu, Menu.menu_id == GroupMenu.menu_id)
            .filter(
                GroupMenu.group_id == group_id,
                Menu.menu_date == menu_date,
            )
            .first()
            is not None
        )
