from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models import Event, SchoolClass
from app.utils.decorators import staff_required

events_bp = Blueprint('events', __name__)


@events_bp.route('/events')
@login_required
def events_list():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    status = request.args.get('status', '').strip()

    query = Event.query
    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        query = query.filter(Event.class_id.in_(child_class_ids) | (Event.class_id.is_(None)))
    if status:
        query = query.filter_by(status=status)

    items = query.order_by(Event.event_date, Event.event_time).all()
    return render_template('events/events.html', items=items, classes=classes,
                           selected_status=status, statuses=Event.STATUSES)


@events_bp.route('/events/create', methods=['GET', 'POST'])
@staff_required
def event_create():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        event_date = _parse_date(request.form.get('event_date'))
        if not title or not event_date:
            flash('Заполните название и дату мероприятия', 'danger')
        else:
            class_id = request.form.get('class_id')
            db.session.add(Event(
                title=title,
                description=request.form.get('description', '').strip() or None,
                event_date=event_date,
                event_time=request.form.get('event_time', '').strip() or None,
                place=request.form.get('place', '').strip() or None,
                class_id=int(class_id) if class_id else None,
                teacher_id=current_user.id,
                status=request.form.get('status', 'Запланировано'),
            ))
            db.session.commit()
            flash(f'Мероприятие «{title}» добавлено', 'success')
            return redirect(url_for('events.events_list'))

    return render_template('events/event_form.html', item=None, classes=classes)


@events_bp.route('/events/<int:item_id>/edit', methods=['GET', 'POST'])
@staff_required
def event_edit(item_id):
    item = db.session.get(Event, item_id)
    if item is None:
        flash('Мероприятие не найдено', 'danger')
        return redirect(url_for('events.events_list'))

    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        event_date = _parse_date(request.form.get('event_date'))
        if not title or not event_date:
            flash('Заполните название и дату мероприятия', 'danger')
        else:
            item.title = title
            item.description = request.form.get('description', '').strip() or None
            item.event_date = event_date
            item.event_time = request.form.get('event_time', '').strip() or None
            item.place = request.form.get('place', '').strip() or None
            class_id = request.form.get('class_id')
            item.class_id = int(class_id) if class_id else None
            item.status = request.form.get('status', item.status)
            db.session.commit()
            flash('Мероприятие обновлено', 'success')
            return redirect(url_for('events.events_list'))

    return render_template('events/event_form.html', item=item, classes=classes)


@events_bp.route('/events/<int:item_id>/delete', methods=['POST'])
@staff_required
def event_delete(item_id):
    item = db.session.get(Event, item_id)
    if item is None:
        flash('Мероприятие не найдено', 'danger')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('Мероприятие удалено', 'success')
    return redirect(url_for('events.events_list'))


def _parse_date(value):
    from datetime import datetime
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
