"""Menu service."""
import uuid
from typing import Optional, List, Tuple
from datetime import UTC, date, datetime
from sqlalchemy.orm import Session

from app.models.menu import Menu, MenuStatus
from app.models.user import User
from app.repositories.menu import MenuRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.group import GroupRepository
from app.core.exceptions import ConflictException, NotFoundException, AuthorizationException


class MenuService:
    """Service for menu management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.menu_repo = MenuRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.group_repo = GroupRepository(db)
    
    def create_menu(
        self,
        current_user: User,
        menu_date: date,
        items: List[dict],
        group_ids: Optional[List[str]] = None,
        *,
        status: MenuStatus = MenuStatus.PUBLISHED,
        notes: Optional[str] = None,
    ) -> Menu:
        """Create menu with items."""
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")

        valid_group_ids: list[str] = []
        if group_ids:
            for group_id in group_ids:
                group = self.group_repo.get_by_id(group_id)
                if not group:
                    raise NotFoundException("Group not found")
                if group.kindergarten_id != kinder.kindergarten_id:
                    raise AuthorizationException("You cannot assign a menu to another kindergarten's group")
                if self.menu_repo.group_has_menu_on_date(group_id=group_id, menu_date=menu_date):
                    raise ConflictException("Menu already exists for this group and date")
                valid_group_ids.append(group_id)

        menu_id = str(uuid.uuid4())
        published_at = datetime.now(UTC).replace(tzinfo=None) if status == MenuStatus.PUBLISHED else None
        menu = self.menu_repo.create_menu(
            menu_id=menu_id,
            kindergarten_id=kinder.kindergarten_id,
            menu_date=menu_date,
            created_by_user_id=current_user.user_id,
            status=status,
            published_at=published_at,
            notes=notes,
        )

        # Add menu items
        for item_data in items:
            menu_item_id = str(uuid.uuid4())
            self.menu_repo.add_menu_item(
                menu_item_id=menu_item_id,
                menu_id=menu_id,
                meal=item_data['meal'],
                title=item_data['title'],
                description=item_data.get('description'),
                calories=item_data.get('calories')
            )
        
        # Assign to groups
        for group_id in valid_group_ids:
            group_menu_id = str(uuid.uuid4())
            self.menu_repo.assign_menu_to_group(group_menu_id, group_id, menu_id)

        self.db.commit()
        self.db.refresh(menu)
        return menu
    
    def get_menu(self, menu_id: str) -> Menu:
        """Get menu by ID."""
        menu = self.menu_repo.get_by_id(menu_id)
        if not menu:
            raise NotFoundException("Menu not found")
        return menu
    
    def list_menus_for_kindergarten(self, current_user: User, skip: int = 0,
                                    limit: int = 20) -> Tuple[List[Menu], int]:
        """List menus for kindergarten."""
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")
        
        return self.menu_repo.get_by_kindergarten(kinder.kindergarten_id, skip=skip, limit=limit)
    
    def get_menu_for_group_today(
        self,
        current_user: User,
        group_id: str,
        *,
        published_only: bool = False,
    ) -> Optional[Menu]:
        """Get today's menu for a group."""
        today = datetime.now().date()
        return self.get_menu_for_group(current_user, group_id, today, published_only=published_only)

    def get_menu_for_group(
        self,
        current_user: User,
        group_id: str,
        menu_date: date,
        *,
        published_only: bool = False,
    ) -> Optional[Menu]:
        """Get a menu for one kindergarten group on a specific date."""
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundException("Group not found")
        if group.kindergarten_id != kinder.kindergarten_id:
            raise AuthorizationException("You cannot access another kindergarten's group")
        return self.menu_repo.get_menu_for_group(group_id, menu_date, published_only=published_only)
