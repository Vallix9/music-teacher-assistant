from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import (Attendance, Event, Grade, LessonPlan, Material,
                        Repertoire, Schedule, SchoolClass, Student)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()

    today_number = date.today().isoweekday()
    today_lessons = (Schedule.query
                     .filter_by(day_of_week=today_number)
                     .order_by(Schedule.lesson_number).all())
    if not today_lessons:
        today_lessons = Schedule.query.order_by(
            Schedule.day_of_week, Schedule.lesson_number).limit(6).all()

    recent_repertoire = Repertoire.query.order_by(Repertoire.id.desc()).limit(4).all()
    recent_grades = Grade.query.order_by(Grade.id.desc()).limit(6).all()
    upcoming = (Event.query.filter(Event.status == 'Запланировано')
                .order_by(Event.event_date).limit(4).all())

    total_students = Student.query.count()
    total_grades = Grade.query.count()
    avg_grade = None
    if total_grades:
        avg_grade = round(sum(g.value for g in Grade.query.all()) / total_grades, 2)

    return render_template(
        'main/index.html',
        classes=classes,
        today_lessons=today_lessons,
        today_number=today_number,
        recent_repertoire=recent_repertoire,
        recent_grades=recent_grades,
        upcoming=upcoming,
        total_students=total_students,
        total_classes=len(classes),
        total_lessons=Schedule.query.count(),
        total_materials=Material.query.count(),
        total_repertoire=Repertoire.query.count(),
        total_plans=LessonPlan.query.count(),
        avg_grade=avg_grade,
        total_attendance=Attendance.query.count(),
    )
