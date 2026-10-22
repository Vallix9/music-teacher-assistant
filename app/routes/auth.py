from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, Role
from app.utils.decorators import admin_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Добро пожаловать, {user.full_name}!', 'success')
            nxt = request.args.get('next')
            return redirect(nxt or url_for('main.index'))
        flash('Неверный логин или пароль', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/users')
@admin_required
def users_list():
    return render_template('auth/users.html', users=User.query.order_by(User.role, User.full_name).all())


@auth_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def user_create():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', Role.TEACHER)

        if not username or not email or not full_name or not password:
            flash('Заполните все обязательные поля', 'danger')
        elif User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Пользователь с таким логином или e-mail уже существует', 'danger')
        else:
            user = User(username=username, email=email, full_name=full_name, role=role,
                        phone=request.form.get('phone', '').strip() or None)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'Пользователь {full_name} создан', 'success')
            return redirect(url_for('auth.users_list'))

    return render_template('auth/user_form.html', user=None)


@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('auth.users_list'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        if not email or not full_name:
            flash('Заполните все обязательные поля', 'danger')
        else:
            existing = User.query.filter(User.email == email, User.id != user.id).first()
            if existing:
                flash('Этот e-mail уже используется', 'danger')
            else:
                user.email = email
                user.full_name = full_name
                user.role = request.form.get('role', user.role)
                user.phone = request.form.get('phone', '').strip() or None
                password = request.form.get('password', '')
                if password:
                    user.set_password(password)
                    flash('Пароль обновлён', 'info')
                db.session.commit()
                flash('Данные пользователя обновлены', 'success')
                return redirect(url_for('auth.users_list'))

    return render_template('auth/user_form.html', user=user)


@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash('Пользователь не найден', 'danger')
    elif user.id == current_user.id:
        flash('Нельзя удалить собственную учётную запись', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь удалён', 'success')
    return redirect(url_for('auth.users_list'))
