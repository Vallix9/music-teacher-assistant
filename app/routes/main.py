from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Event, Material, Repertoire, Schedule, SchoolClass, Student

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    upcoming = Event.query.filter(Event.status == 'Запланировано').order_by(Event.event_date).limit(5).all()
    total_students = Student.query.count()
    return render_template(
        'main/index.html',
        classes=classes,
        upcoming=upcoming,
        total_students=total_students,
        total_classes=len(classes),
        total_lessons=Schedule.query.count(),
        total_materials=Material.query.count(),
        total_repertoire=Repertoire.query.count(),
    )
