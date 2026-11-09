from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models import Repertoire, SchoolClass
from app.utils.access import accessible_classes, parent_class_ids
from app.utils.decorators import staff_required

repertoire_bp = Blueprint('repertoire', __name__)


@repertoire_bp.route('/repertoire')
@login_required
def repertoire_list():
    classes = accessible_classes()
    class_id = request.args.get('class_id', type=int)
    q = request.args.get('q', '').strip()

    query = Repertoire.query
    if current_user.is_parent:
        query = query.filter(
            db.or_(Repertoire.class_id.in_(parent_class_ids()),
                   Repertoire.class_id.is_(None)))
    if class_id:
        query = query.filter_by(class_id=class_id)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Repertoire.title.ilike(like), Repertoire.composer.ilike(like)))

    items = query.order_by(Repertoire.class_id.is_(None), Repertoire.title).all()
    return render_template('repertoire/repertoire.html', items=items, classes=classes,
                           selected_class=class_id, q=q)


@repertoire_bp.route('/repertoire/create', methods=['GET', 'POST'])
@staff_required
def repertoire_create():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Укажите название произведения', 'danger')
        else:
            class_id = request.form.get('class_id')
            db.session.add(Repertoire(
                title=title,
                composer=request.form.get('composer', '').strip() or None,
                genre=request.form.get('genre', '').strip() or None,
                class_id=int(class_id) if class_id else None,
                year=request.form.get('year', '2025/2026').strip(),
                difficulty=request.form.get('difficulty', 'Средний'),
                duration=request.form.get('duration', '').strip() or None,
                link=request.form.get('link', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
            ))
            db.session.commit()
            flash(f'Произведение «{title}» добавлено в репертуар', 'success')
            return redirect(url_for('repertoire.repertoire_list'))

    return render_template('repertoire/repertoire_form.html', item=None, classes=classes)


@repertoire_bp.route('/repertoire/<int:item_id>/edit', methods=['GET', 'POST'])
@staff_required
def repertoire_edit(item_id):
    item = db.session.get(Repertoire, item_id)
    if item is None:
        flash('Произведение не найдено', 'danger')
        return redirect(url_for('repertoire.repertoire_list'))

    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Укажите название произведения', 'danger')
        else:
            item.title = title
            item.composer = request.form.get('composer', '').strip() or None
            item.genre = request.form.get('genre', '').strip() or None
            class_id = request.form.get('class_id')
            item.class_id = int(class_id) if class_id else None
            item.year = request.form.get('year', item.year).strip()
            item.difficulty = request.form.get('difficulty', item.difficulty)
            item.duration = request.form.get('duration', '').strip() or None
            item.link = request.form.get('link', '').strip() or None
            item.notes = request.form.get('notes', '').strip() or None
            db.session.commit()
            flash('Произведение обновлено', 'success')
            return redirect(url_for('repertoire.repertoire_list'))

    return render_template('repertoire/repertoire_form.html', item=item, classes=classes)


@repertoire_bp.route('/repertoire/<int:item_id>/delete', methods=['POST'])
@staff_required
def repertoire_delete(item_id):
    item = db.session.get(Repertoire, item_id)
    if item is None:
        flash('Произведение не найдено', 'danger')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('Произведение удалено из репертуара', 'success')
    return redirect(url_for('repertoire.repertoire_list'))
