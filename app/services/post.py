"""Post service."""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.post import Post
from app.repositories.post import PostRepository
from app.core.exceptions import NotFoundException, AuthorizationException


class PostService:
    """Service for admin post/announcement management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.post_repo = PostRepository(db)
    
    def create_post(self, current_user: Admin, title: str, body: str,
                   target_kindergarten_id: Optional[str] = None) -> Post:
        """Create admin post (admin only)."""
        post_id = str(uuid.uuid4())
        return self.post_repo.create_post(
            post_id=post_id,
            created_by_admin_id=current_user.admin_id,
            title=title,
            body=body,
            target_kindergarten_id=target_kindergarten_id
        )
    
    def get_post(self, post_id: str) -> Post:
        """Get post by ID."""
        post = self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundException("Post not found")
        return post
    
    def list_all_posts(self, skip: int = 0, limit: int = 20) -> Tuple[List[Post], int]:
        """List all posts (admin view)."""
        return self.post_repo.get_all_posts(skip=skip, limit=limit)
    
    def list_posts_for_kindergarten(self, kindergarten_id: str, skip: int = 0,
                                    limit: int = 20) -> Tuple[List[Post], int]:
        """List posts for a kindergarten."""
        return self.post_repo.get_posts_for_kindergarten(kindergarten_id, skip=skip, limit=limit)
    
    def delete_post(self, current_user: Admin, post_id: str) -> bool:
        """Delete post (admin only)."""
        post = self.get_post(post_id)
        
        # Only original creator can delete
        if post.created_by_admin_id != current_user.admin_id:
            raise AuthorizationException("You do not have permission to delete this post")
        
        self.db.delete(post)
        self.db.commit()
        return True
