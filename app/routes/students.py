from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import SchoolClass, Student, User, Role, Schedule
from app.utils.access import accessible_classes, class_is_accessible
from app.utils.decorators import staff_required

students_bp = Blueprint('students', __name__)


def _can_manage():
    return current_user.is_admin or current_user.is_teacher


@students_bp.route('/classes')
@login_required
def classes_list():
    classes = accessible_classes()
    return render_template('students/classes.html', classes=classes)


@students_bp.route('/classes/create', methods=['GET', 'POST'])
@staff_required
def class_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        grade = request.form.get('grade', '').strip()
        if not name or not grade:
            flash('Заполните название класса и номер', 'danger')
        elif SchoolClass.query.filter_by(name=name).first():
            flash('Класс с таким названием уже существует', 'danger')
        else:
            teacher_id = request.form.get('teacher_id') or None
            db.session.add(SchoolClass(
                name=name,
                grade=int(grade),
                year=request.form.get('year', '2025/2026').strip(),
                teacher_id=int(teacher_id) if teacher_id else None,
            ))
            db.session.commit()
            flash(f'Класс {name} добавлен', 'success')
            return redirect(url_for('students.classes_list'))

    teachers = User.query.filter(User.role.in_([Role.ADMIN, Role.TEACHER])).order_by(User.full_name).all()
    return render_template('students/class_form.html', school_class=None, teachers=teachers)


@students_bp.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@staff_required
def class_edit(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if school_class is None:
        flash('Класс не найден', 'danger')
        return redirect(url_for('students.classes_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        grade = request.form.get('grade', '').strip()
        if not name or not grade:
            flash('Заполните название класса и номер', 'danger')
        else:
            school_class.name = name
            school_class.grade = int(grade)
            school_class.year = request.form.get('year', school_class.year).strip()
            teacher_id = request.form.get('teacher_id') or None
            school_class.teacher_id = int(teacher_id) if teacher_id else None
            db.session.commit()
            flash('Данные класса обновлены', 'success')
            return redirect(url_for('students.classes_list'))

    teachers = User.query.filter(User.role.in_([Role.ADMIN, Role.TEACHER])).order_by(User.full_name).all()
    return render_template('students/class_form.html', school_class=school_class, teachers=teachers)


@students_bp.route('/classes/<int:class_id>/delete', methods=['POST'])
@staff_required
def class_delete(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if school_class is None:
        flash('Класс не найден', 'danger')
    else:
        db.session.delete(school_class)
        db.session.commit()
        flash(f'Класс {school_class.name} удалён', 'success')
    return redirect(url_for('students.classes_list'))


@students_bp.route('/classes/<int:class_id>/students')
@login_required
def class_students(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if school_class is None:
        flash('Класс не найден', 'danger')
        return redirect(url_for('students.classes_list'))
    if not class_is_accessible(class_id):
        abort(403)

    if current_user.is_parent:
        students = [s for s in school_class.students if s.parent_id == current_user.id]
    else:
        students = school_class.students

    return render_template('students/class_students.html', school_class=school_class, students=students)


@students_bp.route('/students/create', methods=['GET', 'POST'])
@staff_required
def student_create():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if not classes:
        flash('Сначала создайте хотя бы один класс', 'warning')
        return redirect(url_for('students.classes_list'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        class_id = request.form.get('class_id')
        if not full_name or not class_id:
            flash('Заполните ФИО ученика и выберите класс', 'danger')
        else:
            db.session.add(Student(
                full_name=full_name,
                class_id=int(class_id),
                parent_id=int(request.form['parent_id']) if request.form.get('parent_id') else None,
                birth_date=_parse_date(request.form.get('birth_date')),
                phone=request.form.get('phone', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
            ))
            db.session.commit()
            flash(f'Ученик {full_name} добавлен', 'success')
            return redirect(url_for('students.class_students', class_id=int(class_id)))

    parents = User.query.filter_by(role=Role.PARENT).order_by(User.full_name).all()
    return render_template('students/student_form.html', student=None, classes=classes, parents=parents)


@students_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@staff_required
def student_edit(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash('Ученик не найден', 'danger')
        return redirect(url_for('students.classes_list'))

    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        class_id = request.form.get('class_id')
        if not full_name or not class_id:
            flash('Заполните ФИО ученика и выберите класс', 'danger')
        else:
            student.full_name = full_name
            student.class_id = int(class_id)
            student.parent_id = int(request.form['parent_id']) if request.form.get('parent_id') else None
            student.birth_date = _parse_date(request.form.get('birth_date'))
            student.phone = request.form.get('phone', '').strip() or None
            student.notes = request.form.get('notes', '').strip() or None
            db.session.commit()
            flash('Данные ученика обновлены', 'success')
            return redirect(url_for('students.class_students', class_id=student.class_id))

    parents = User.query.filter_by(role=Role.PARENT).order_by(User.full_name).all()
    return render_template('students/student_form.html', student=student, classes=classes, parents=parents)


@students_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@staff_required
def student_delete(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash('Ученик не найден', 'danger')
        return redirect(url_for('students.classes_list'))
    class_id = student.class_id
    db.session.delete(student)
    db.session.commit()
    flash('Ученик удалён', 'success')
    return redirect(url_for('students.class_students', class_id=class_id))


def _parse_date(value):
    from datetime import datetime
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
