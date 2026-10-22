from datetime import date

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models import (Attendance, Grade, Schedule, SchoolClass, Student)
from app.utils.decorators import staff_required

journal_bp = Blueprint('journal', __name__)


def _classes_for_current_user():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        classes = [c for c in classes if c.id in child_class_ids]
    return classes


@journal_bp.route('/journal')
@login_required
def journal():
    classes = _classes_for_current_user()
    class_id = request.args.get('class_id', type=int)
    lesson_date = request.args.get('date', '').strip()
    schedule_id = request.args.get('schedule_id', type=int)

    if not class_id and classes:
        class_id = classes[0].id
    if not lesson_date:
        lesson_date = date.today().isoformat()

    school_class = db.session.get(SchoolClass, class_id) if class_id else None
    lesson = db.session.get(Schedule, schedule_id) if schedule_id else None

    students = []
    attendance_map = {}
    grades_map = {}

    if school_class:
        if current_user.is_parent:
            students = [s for s in school_class.students if s.parent_id == current_user.id]
        else:
            students = sorted(school_class.students, key=lambda s: s.full_name)

        day = _parse_date(lesson_date)
        if day:
            student_ids = [s.id for s in students]
            if lesson:
                rows = Attendance.query.filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.schedule_id == lesson.id,
                    Attendance.lesson_date == day).all()
            else:
                rows = Attendance.query.filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.lesson_date == day).all()
            attendance_map = {row.student_id: row for row in rows}

            grade_query = Grade.query.filter(
                Grade.student_id.in_(student_ids),
                Grade.lesson_date == day)
            if lesson:
                grade_query = grade_query.filter(Grade.schedule_id == lesson.id)
            for g in grade_query.all():
                grades_map.setdefault(g.student_id, []).append(g)

    lessons = []
    if class_id:
        lessons = Schedule.query.filter_by(class_id=class_id).order_by(
            Schedule.day_of_week, Schedule.lesson_number).all()

    return render_template('journal/journal.html', classes=classes, school_class=school_class,
                           students=students, lesson_date=lesson_date, lesson=lesson, lessons=lessons,
                           attendance_map=attendance_map, grades_map=grades_map,
                           statuses=Attendance.STATUSES, categories=Grade.CATEGORIES)


@journal_bp.route('/journal/save', methods=['POST'])
@staff_required
def journal_save():
    class_id = request.form.get('class_id', type=int)
    lesson_date = _parse_date(request.form.get('lesson_date'))
    schedule_id = request.form.get('schedule_id', type=int)

    if not class_id or not lesson_date:
        flash('Не удалось определить класс или дату урока', 'danger')
        return redirect(url_for('journal.journal', class_id=class_id))

    school_class = db.session.get(SchoolClass, class_id)
    if school_class is None:
        flash('Класс не найден', 'danger')
        return redirect(url_for('journal.journal'))

    saved_attendance = 0
    saved_grades = 0

    for student in school_class.students:
        status = request.form.get(f'att_{student.id}')
        if status:
            row = Attendance.query.filter_by(student_id=student.id,
                                             schedule_id=schedule_id,
                                             lesson_date=lesson_date).first()
            if row is None:
                row = Attendance(student_id=student.id, schedule_id=schedule_id,
                                 lesson_date=lesson_date, teacher_id=current_user.id)
                db.session.add(row)
            row.status = status
            row.note = request.form.get(f'note_{student.id}', '').strip() or None
            saved_attendance += 1

        value = request.form.get(f'grade_{student.id}', '').strip()
        category = request.form.get(f'category_{student.id}', 'За урок').strip() or 'За урок'
        if value.isdigit() and 1 <= int(value) <= 5:
            grade = Grade.query.filter_by(student_id=student.id, schedule_id=schedule_id,
                                          lesson_date=lesson_date, category=category).first()
            if grade is None:
                grade = Grade(student_id=student.id, schedule_id=schedule_id,
                              lesson_date=lesson_date, category=category,
                              teacher_id=current_user.id)
                db.session.add(grade)
            grade.value = int(value)
            grade.comment = request.form.get(f'gcomment_{student.id}', '').strip() or None
            saved_grades += 1

    db.session.commit()
    flash(f'Журнал сохранён: посещаемость — {saved_attendance}, оценки — {saved_grades}', 'success')

    return redirect(url_for('journal.journal', class_id=class_id, date=lesson_date.isoformat(),
                            schedule_id=schedule_id or None))


@journal_bp.route('/journal/student/<int:student_id>')
@login_required
def student_journal(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash('Ученик не найден', 'danger')
        return redirect(url_for('journal.journal'))

    if current_user.is_parent and student.parent_id != current_user.id:
        from flask import abort
        abort(403)

    attendance = Attendance.query.filter_by(student_id=student.id).order_by(
        Attendance.lesson_date.desc()).all()
    grades = Grade.query.filter_by(student_id=student.id).order_by(Grade.lesson_date.desc()).all()

    avg = round(sum(g.value for g in grades) / len(grades), 2) if grades else None
    total = len(attendance)
    absent = sum(1 for a in attendance if a.is_absent)
    percent = round((total - absent) / total * 100, 1) if total else None

    return render_template('journal/student_journal.html', student=student,
                           attendance=attendance, grades=grades, avg_grade=avg,
                           attendance_percent=percent, total_lessons=total)


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None
