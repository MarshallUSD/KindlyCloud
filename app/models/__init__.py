"""Import all models so SQLAlchemy can resolve string relationships."""

from app.models.admin import Admin
from app.models.attendance import Attendance
from app.models.child import Child, ParentChildLink
from app.models.enrollment import Enrollment
from app.models.feedback import Feedback
from app.models.group import Group
from app.models.kindergarten import Kindergarten, KindergartenUser
from app.models.menu import GroupMenu, Menu, MenuItem
from app.models.notification import Notification
from app.models.parent import Parent, ParentUser
from app.models.payment import Payment
from app.models.pedagogue import Pedagogue
from app.models.post import Post
from app.models.user import User
