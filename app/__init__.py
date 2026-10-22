import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.students import students_bp
    from app.routes.schedule import schedule_bp
    from app.routes.repertoire import repertoire_bp
    from app.routes.materials import materials_bp
    from app.routes.events import events_bp
    from app.routes.journal import journal_bp
    from app.routes.lesson_plans import plans_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(repertoire_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(plans_bp)
    app.register_blueprint(reports_bp)

    with app.app_context():
        from app import seed
        db.create_all()
        seed.seed_data()

    @app.errorhandler(403)
    def forbidden(_e):
        from flask import render_template
        return render_template('errors/error.html', code=403, title='Доступ запрещён',
                               message='У вас нет прав для просмотра этой страницы.'), 403

    @app.errorhandler(404)
    def not_found(_e):
        from flask import render_template
        return render_template('errors/error.html', code=404, title='Страница не найдена',
                               message='Запрошенная страница не существует.'), 404

    @app.errorhandler(500)
    def server_error(_e):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/error.html', code=500, title='Внутренняя ошибка сервера',
                               message='Произошла непредвиденная ошибка. Попробуйте повторить действие.'), 500

    return app
