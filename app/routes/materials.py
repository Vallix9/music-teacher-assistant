import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Material, SchoolClass
from app.utils.access import accessible_classes, parent_class_ids
from app.utils.decorators import staff_required

materials_bp = Blueprint('materials', __name__)

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'jpg', 'jpeg', 'png', 'gif', 'mp3', 'wav', 'ogg', 'midi', 'mid',
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@materials_bp.route('/materials')
@login_required
def materials_list():
    classes = accessible_classes()
    class_id = request.args.get('class_id', type=int)
    lesson_type = request.args.get('lesson_type', '').strip()

    query = Material.query
    if current_user.is_parent:
        query = query.filter(Material.class_id.in_(parent_class_ids()) | (Material.class_id.is_(None)))
    if class_id:
        query = query.filter_by(class_id=class_id)
    if lesson_type:
        query = query.filter_by(lesson_type=lesson_type)

    items = query.order_by(Material.created_at.desc()).all()
    return render_template('materials/materials.html', items=items, classes=classes,
                           selected_class=class_id, selected_type=lesson_type,
                           lesson_types=Material.LESSON_TYPES)


@materials_bp.route('/materials/create', methods=['GET', 'POST'])
@staff_required
def material_create():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        file = request.files.get('file')

        if not title:
            flash('Укажите название материала', 'danger')
        elif file and file.filename and not allowed_file(file.filename):
            flash('Недопустимый тип файла', 'danger')
        else:
            file_name = None
            file_path = None
            if file and file.filename:
                file_name = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{file_name}"
                upload_dir = os.path.join(current_app_upload_dir(), 'materials')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, unique_name))
                file_name = file.filename
                file_path = f"materials/{unique_name}"

            class_id = request.form.get('class_id')
            db.session.add(Material(
                title=title,
                description=request.form.get('description', '').strip() or None,
                lesson_type=request.form.get('lesson_type', 'Урок'),
                class_id=int(class_id) if class_id else None,
                teacher_id=current_user.id,
                file_name=file_name,
                file_path=file_path,
                link=request.form.get('link', '').strip() or None,
            ))
            db.session.commit()
            flash(f'Материал «{title}» добавлен', 'success')
            return redirect(url_for('materials.materials_list'))

    return render_template('materials/material_form.html', item=None, classes=classes)


@materials_bp.route('/materials/<int:item_id>/edit', methods=['GET', 'POST'])
@staff_required
def material_edit(item_id):
    item = db.session.get(Material, item_id)
    if item is None:
        flash('Материал не найден', 'danger')
        return redirect(url_for('materials.materials_list'))

    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Укажите название материала', 'danger')
        else:
            item.title = title
            item.description = request.form.get('description', '').strip() or None
            item.lesson_type = request.form.get('lesson_type', item.lesson_type)
            class_id = request.form.get('class_id')
            item.class_id = int(class_id) if class_id else None
            item.link = request.form.get('link', '').strip() or None
            db.session.commit()
            flash('Материал обновлён', 'success')
            return redirect(url_for('materials.materials_list'))

    return render_template('materials/material_form.html', item=item, classes=classes)


@materials_bp.route('/materials/<int:item_id>/delete', methods=['POST'])
@staff_required
def material_delete(item_id):
    item = db.session.get(Material, item_id)
    if item is None:
        flash('Материал не найден', 'danger')
    else:
        if item.file_path:
            try:
                os.remove(os.path.join(current_app_upload_dir(), item.file_path))
            except OSError:
                pass
        db.session.delete(item)
        db.session.commit()
        flash('Материал удалён', 'success')
    return redirect(url_for('materials.materials_list'))


@materials_bp.route('/materials/download/<int:item_id>')
@login_required
def material_download(item_id):
    item = db.session.get(Material, item_id)
    if item is None or not item.file_path:
        flash('Файл не найден', 'danger')
        return redirect(url_for('materials.materials_list'))

    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        if item.class_id is not None and item.class_id not in child_class_ids:
            flash('Нет доступа к этому материалу', 'danger')
            return redirect(url_for('materials.materials_list'))

    return send_from_directory(current_app_upload_dir(), item.file_path, as_attachment=True,
                               download_name=item.file_name)


def current_app_upload_dir():
    from flask import current_app
    return current_app.config['UPLOAD_FOLDER']
