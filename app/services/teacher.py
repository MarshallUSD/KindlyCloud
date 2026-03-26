"""Backward-compatible teacher service facade."""

from app.services.staff_service import StaffService


class TeacherService(StaffService):
    """Compatibility facade that exposes the old teacher API."""

    def create_teacher(self, current_user, payload):
        teacher = self.create_staff(current_user, payload)
        if hasattr(payload, "experience_year"):
            teacher.experience_year = payload.experience_year
            self.db.commit()
            self.db.refresh(teacher)
        return teacher

    def list_teachers(self, current_user, skip=0, limit=20, group_id=None, search=None):
        return self.get_staff(current_user, skip=skip, limit=limit, group_id=group_id, search=search)

    def get_teacher(self, current_user, teacher_id):
        return self.get_staff_member(current_user, teacher_id)

    def update_teacher(self, current_user, teacher_id, payload):
        teacher = self.update_staff(current_user, teacher_id, payload)
        if hasattr(payload, "experience_year") and "experience_year" in payload.model_dump(exclude_unset=True):
            teacher.experience_year = payload.experience_year
            self.db.commit()
            self.db.refresh(teacher)
        return teacher

    def delete_teacher(self, current_user, teacher_id):
        return self.delete_staff(current_user, teacher_id)
