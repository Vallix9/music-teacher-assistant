from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import (Attendance, Event, Grade, LessonPlan, Material,
                        Repertoire, Schedule, SchoolClass, Student)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    is_parent = current_user.is_parent
    child_ids = [s.id for s in current_user.students] if is_parent else []
    child_class_ids = sorted({s.class_id for s in current_user.students}) if is_parent else []

    # --- классы ---
    classes_query = SchoolClass.query
    if is_parent:
        classes_query = classes_query.filter(SchoolClass.id.in_(child_class_ids))
    classes = classes_query.order_by(SchoolClass.grade, SchoolClass.name).all()

    # --- расписание ---
    schedule_query = Schedule.query
    if is_parent:
        schedule_query = schedule_query.filter(Schedule.class_id.in_(child_class_ids))

    today_number = date.today().isoweekday()
    today_lessons = (schedule_query
                     .filter_by(day_of_week=today_number)
                     .order_by(Schedule.lesson_number).all())
    if not today_lessons:
        today_lessons = schedule_query.order_by(
            Schedule.day_of_week, Schedule.lesson_number).limit(6).all()

    # --- репертуар ---
    repertoire_query = Repertoire.query
    if is_parent:
        repertoire_query = repertoire_query.filter(
            or_(Repertoire.class_id.in_(child_class_ids), Repertoire.class_id.is_(None)))
    recent_repertoire = repertoire_query.order_by(Repertoire.id.desc()).limit(4).all()

    # --- оценки ---
    grades_query = Grade.query
    if is_parent:
        grades_query = grades_query.filter(Grade.student_id.in_(child_ids))
    recent_grades = grades_query.order_by(Grade.id.desc()).limit(6).all()

    total_grades = grades_query.count()
    avg_grade = None
    if total_grades:
        avg_grade = round(sum(g.value for g in grades_query.all()) / total_grades, 2)

    # --- мероприятия ---
    events_query = Event.query.filter(Event.status == 'Запланировано')
    if is_parent:
        events_query = events_query.filter(
            or_(Event.class_id.in_(child_class_ids), Event.class_id.is_(None)))
    upcoming = events_query.order_by(Event.event_date).limit(4).all()

    # --- материалы и конспекты ---
    materials_query = Material.query
    plans_query = LessonPlan.query
    if is_parent:
        materials_query = materials_query.filter(
            or_(Material.class_id.in_(child_class_ids), Material.class_id.is_(None)))
        plans_query = plans_query.filter(
            or_(LessonPlan.class_id.in_(child_class_ids), LessonPlan.class_id.is_(None)))

    # --- посещаемость ---
    attendance_query = Attendance.query
    if is_parent:
        attendance_query = attendance_query.filter(Attendance.student_id.in_(child_ids))

    total_students = len(current_user.students) if is_parent else Student.query.count()

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
        total_lessons=schedule_query.count(),
        total_materials=materials_query.count(),
        total_repertoire=repertoire_query.count(),
        total_plans=plans_query.count(),
        avg_grade=avg_grade,
        total_attendance=attendance_query.count(),
        is_parent=is_parent,
    )
