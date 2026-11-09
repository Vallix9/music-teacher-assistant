from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models import Schedule, SchoolClass, User, Role
from app.utils.access import accessible_classes, parent_class_ids
from app.utils.decorators import staff_required

schedule_bp = Blueprint('schedule', __name__)

DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


@schedule_bp.route('/schedule')
@login_required
def schedule_list():
    classes = accessible_classes()
    class_id = request.args.get('class_id', type=int)
    selected_class = db.session.get(SchoolClass, class_id) if class_id else None
    if selected_class and selected_class.id not in [c.id for c in classes]:
        selected_class = None

    items = Schedule.query.filter_by(year='2025/2026')
    if current_user.is_parent and not selected_class:
        items = items.filter(Schedule.class_id.in_(parent_class_ids()))
    if selected_class:
        items = items.filter_by(class_id=selected_class.id)
    items = items.order_by(Schedule.day_of_week, Schedule.lesson_number).all()

    grouped = {}
    for item in items:
        grouped.setdefault(item.day_of_week, []).append(item)

    return render_template('schedule/schedule.html', grouped=grouped, classes=classes,
                           selected_class=selected_class, days=DAYS)


@schedule_bp.route('/schedule/create', methods=['GET', 'POST'])
@staff_required
def schedule_create():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    teachers = User.query.filter(User.role.in_([Role.ADMIN, Role.TEACHER])).order_by(User.full_name).all()

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        day = request.form.get('day_of_week')
        number = request.form.get('lesson_number')
        start = request.form.get('start_time', '')
        end = request.form.get('end_time', '')

        if not all([class_id, day, number, start, end]):
            flash('Заполните все обязательные поля', 'danger')
        elif not _valid_time(start) or not _valid_time(end):
            flash('Время должно быть в формате ЧЧ:ММ', 'danger')
        else:
            teacher_id = request.form.get('teacher_id') or current_user.id
            db.session.add(Schedule(
                class_id=int(class_id),
                teacher_id=int(teacher_id),
                subject=request.form.get('subject', 'Музыка').strip() or 'Музыка',
                day_of_week=int(day),
                lesson_number=int(number),
                start_time=start,
                end_time=end,
                room=request.form.get('room', '').strip() or None,
                year=request.form.get('year', '2025/2026').strip(),
            ))
            db.session.commit()
            flash('Урок добавлен в расписание', 'success')
            return redirect(url_for('schedule.schedule_list', class_id=int(class_id)))

    return render_template('schedule/schedule_form.html', item=None, classes=classes,
                           teachers=teachers, days=DAYS)


@schedule_bp.route('/schedule/<int:item_id>/edit', methods=['GET', 'POST'])
@staff_required
def schedule_edit(item_id):
    item = db.session.get(Schedule, item_id)
    if item is None:
        flash('Запись расписания не найдена', 'danger')
        return redirect(url_for('schedule.schedule_list'))

    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    teachers = User.query.filter(User.role.in_([Role.ADMIN, Role.TEACHER])).order_by(User.full_name).all()

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        start = request.form.get('start_time', '')
        end = request.form.get('end_time', '')
        if not all([class_id, request.form.get('day_of_week'), request.form.get('lesson_number'), start, end]):
            flash('Заполните все обязательные поля', 'danger')
        elif not _valid_time(start) or not _valid_time(end):
            flash('Время должно быть в формате ЧЧ:ММ', 'danger')
        else:
            item.class_id = int(class_id)
            item.day_of_week = int(request.form['day_of_week'])
            item.lesson_number = int(request.form['lesson_number'])
            item.start_time = start
            item.end_time = end
            item.subject = request.form.get('subject', 'Музыка').strip() or 'Музыка'
            item.room = request.form.get('room', '').strip() or None
            item.year = request.form.get('year', item.year).strip()
            teacher_id = request.form.get('teacher_id')
            if teacher_id:
                item.teacher_id = int(teacher_id)
            db.session.commit()
            flash('Запись расписания обновлена', 'success')
            return redirect(url_for('schedule.schedule_list', class_id=item.class_id))

    return render_template('schedule/schedule_form.html', item=item, classes=classes,
                           teachers=teachers, days=DAYS)


@schedule_bp.route('/schedule/<int:item_id>/delete', methods=['POST'])
@staff_required
def schedule_delete(item_id):
    item = db.session.get(Schedule, item_id)
    if item is None:
        flash('Запись расписания не найдена', 'danger')
    else:
        class_id = item.class_id
        db.session.delete(item)
        db.session.commit()
        flash('Урок удалён из расписания', 'success')
        return redirect(url_for('schedule.schedule_list', class_id=class_id))
    return redirect(url_for('schedule.schedule_list'))


def _valid_time(value):
    try:
        hours, minutes = value.split(':')
        return 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59
    except (ValueError, AttributeError):
        return False
