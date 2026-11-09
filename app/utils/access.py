"""Правила доступа к классам для разных ролей."""
from flask_login import current_user

from app.models import SchoolClass


def parent_class_ids():
    """ID классов, в которых учатся дети текущего родителя."""
    return sorted({s.class_id for s in current_user.students})


def accessible_classes():
    """Классы, доступные текущему пользователю (для родителя — только его детей)."""
    query = SchoolClass.query
    if current_user.is_parent:
        query = query.filter(SchoolClass.id.in_(parent_class_ids()))
    return query.order_by(SchoolClass.grade, SchoolClass.name).all()


def class_is_accessible(class_id):
    """Может ли текущий пользователь просматривать указанный класс."""
    if not current_user.is_parent:
        return True
    return class_id in parent_class_ids()
