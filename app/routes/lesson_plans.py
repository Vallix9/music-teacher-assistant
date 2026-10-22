from datetime import date

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models import LessonPlan, Schedule, SchoolClass
from app.utils.decorators import staff_required

plans_bp = Blueprint('lesson_plans', __name__)


@plans_bp.route('/lesson-plans')
@login_required
def lesson_plans_list():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    class_id = request.args.get('class_id', type=int)

    query = LessonPlan.query
    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        query = query.filter(LessonPlan.class_id.in_(child_class_ids))
    if class_id:
        query = query.filter_by(class_id=class_id)

    items = query.order_by(LessonPlan.lesson_date.desc().nullslast(), LessonPlan.id.desc()).all()
    return render_template('lesson_plans/lesson_plans.html', items=items, classes=classes,
                           selected_class=class_id)


@plans_bp.route('/lesson-plans/<int:item_id>')
@login_required
def lesson_plan_detail(item_id):
    item = db.session.get(LessonPlan, item_id)
    if item is None:
        flash('План-конспект не найден', 'danger')
        return redirect(url_for('lesson_plans.lesson_plans_list'))
    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        if item.class_id is not None and item.class_id not in child_class_ids:
            from flask import abort
            abort(403)
    return render_template('lesson_plans/lesson_plan_detail.html', item=item)


@plans_bp.route('/lesson-plans/create', methods=['GET', 'POST'])
@staff_required
def lesson_plan_create():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Укажите тему урока', 'danger')
        else:
            class_id = request.form.get('class_id')
            schedule_id = request.form.get('schedule_id', type=int)
            db.session.add(LessonPlan(
                title=title,
                topic=request.form.get('topic', '').strip() or None,
                goal=request.form.get('goal', '').strip() or None,
                tasks=request.form.get('tasks', '').strip() or None,
                lesson_type=request.form.get('lesson_type', 'Урок'),
                class_id=int(class_id) if class_id else None,
                schedule_id=schedule_id,
                lesson_date=_parse_date(request.form.get('lesson_date')),
                duration=request.form.get('duration', '45 мин').strip() or '45 мин',
                equipment=request.form.get('equipment', '').strip() or None,
                structure=request.form.get('structure', '').strip() or None,
                homework=request.form.get('homework', '').strip() or None,
                criteria=request.form.get('criteria', '').strip() or None,
                teacher_id=current_user.id,
            ))
            db.session.commit()
            flash(f'План-конспект «{title}» сохранён', 'success')
            return redirect(url_for('lesson_plans.lesson_plans_list'))

    return render_template('lesson_plans/lesson_plan_form.html', item=None, classes=classes)


@plans_bp.route('/lesson-plans/<int:item_id>/edit', methods=['GET', 'POST'])
@staff_required
def lesson_plan_edit(item_id):
    item = db.session.get(LessonPlan, item_id)
    if item is None:
        flash('План-конспект не найден', 'danger')
        return redirect(url_for('lesson_plans.lesson_plans_list'))

    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Укажите тему урока', 'danger')
        else:
            item.title = title
            item.topic = request.form.get('topic', '').strip() or None
            item.goal = request.form.get('goal', '').strip() or None
            item.tasks = request.form.get('tasks', '').strip() or None
            item.lesson_type = request.form.get('lesson_type', item.lesson_type)
            class_id = request.form.get('class_id')
            item.class_id = int(class_id) if class_id else None
            item.lesson_date = _parse_date(request.form.get('lesson_date'))
            item.duration = request.form.get('duration', item.duration).strip()
            item.equipment = request.form.get('equipment', '').strip() or None
            item.structure = request.form.get('structure', '').strip() or None
            item.homework = request.form.get('homework', '').strip() or None
            item.criteria = request.form.get('criteria', '').strip() or None
            db.session.commit()
            flash('План-конспект обновлён', 'success')
            return redirect(url_for('lesson_plans.lesson_plans_list'))

    return render_template('lesson_plans/lesson_plan_form.html', item=item, classes=classes)


@plans_bp.route('/lesson-plans/<int:item_id>/delete', methods=['POST'])
@staff_required
def lesson_plan_delete(item_id):
    item = db.session.get(LessonPlan, item_id)
    if item is None:
        flash('План-конспект не найден', 'danger')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('План-конспект удалён', 'success')
    return redirect(url_for('lesson_plans.lesson_plans_list'))


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
