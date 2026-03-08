"""Post repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.post import Post
from app.repositories.base import BaseRepository


class PostRepository(BaseRepository):
    """Repository for Post model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Post)
    
    def get_by_id(self, post_id: str) -> Optional[Post]:
        """Get post by post_id."""
        return self.get_by_id_field('post_id', post_id)
    
    def get_all_posts(self, skip: int = 0, limit: int = 20) -> tuple[List[Post], int]:
        """Get all posts (broadcasts and targeted)."""
        total = self.db.query(func.count(Post.post_id)).scalar()
        records = self.db.query(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
        return records, total
    
    def get_posts_for_kindergarten(self, kindergarten_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Post], int]:
        """Get posts for a kindergarten (broadcasts + targeted)."""
        from sqlalchemy import or_
        
        total = self.db.query(func.count(Post.post_id)).filter(
            or_(
                Post.target_kindergarten_id == kindergarten_id,
                Post.target_kindergarten_id == None
            )
        ).scalar()
        
        records = self.db.query(Post).filter(
            or_(
                Post.target_kindergarten_id == kindergarten_id,
                Post.target_kindergarten_id == None
            )
        ).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
        
        return records, total
    
    def create_post(self, post_id: str, created_by_admin_user_id: str, title: str,
                   body: str, target_kindergarten_id: Optional[str] = None) -> Post:
        """Create a new post."""
        post = Post(
            post_id=post_id,
            created_by_admin_user_id=created_by_admin_user_id,
            title=title,
            body=body,
            target_kindergarten_id=target_kindergarten_id
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post
