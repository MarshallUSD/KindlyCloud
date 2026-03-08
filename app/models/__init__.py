# app/models/__init__.py

# Model modullarini import qilib registry'ga kiritamiz
from app.models.user import User
from app.models.notification import Notification
from app.models.kindergarten import Kindergarten, KindergartenUser
from app.models.pedagogue import Pedagogue
from app.models.group import Group
from app.models.child import Child
from app.models.enrollment import Enrollment
from app.models.attendance import Attendance
from app.models.feedback import Feedback
# agar bular bo‘lsa qo‘sh:
# from app.models.menu import Menu
# from app.models.payment import Payment
# from app.models.post import Post