"""CRUD-тесты всех модулей системы."""
import io
import os

from app import db
from app.models import (Event, Material, Repertoire, Schedule, SchoolClass,
                        Student, User)


def create_class(client, name='8В', grade='8'):
    response = client.post(
        '/classes/create',
        data={'name': name, 'grade': grade, 'year': '2025/2026'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return name


def get_class_id(app, name):
    with app.app_context():
        school_class = SchoolClass.query.filter_by(name=name).first()
        assert school_class is not None
        return school_class.id


def test_class_crud(app, teacher_client):
    name = create_class(teacher_client)
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        f'/classes/{class_id}/edit',
        data={'name': '8Г', 'grade': '8', 'year': '2025/2026'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(SchoolClass, class_id).name == '8Г'

    response = teacher_client.post(f'/classes/{class_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(SchoolClass, class_id) is None


def test_student_crud(app, teacher_client):
    name = create_class(teacher_client, name='9А', grade='9')
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        '/students/create',
        data={'full_name': 'Тестовый Ученик', 'class_id': class_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        student = Student.query.filter_by(full_name='Тестовый Ученик').first()
        assert student is not None
        student_id = student.id

    response = teacher_client.post(
        f'/students/{student_id}/edit',
        data={'full_name': 'Тестовый Ученик 2', 'class_id': class_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Student, student_id).full_name == 'Тестовый Ученик 2'

    response = teacher_client.post(f'/students/{student_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Student, student_id) is None


def test_schedule_crud(app, teacher_client):
    name = create_class(teacher_client, name='9Б', grade='9')
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        '/schedule/create',
        data={
            'class_id': class_id, 'day_of_week': '3', 'lesson_number': '5',
            'start_time': '14:00', 'end_time': '14:45', 'subject': 'Музыка',
            'room': 'каб. 9', 'year': '2025/2026',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        item = Schedule.query.filter_by(class_id=class_id).first()
        assert item is not None
        item_id = item.id

    response = teacher_client.post(
        f'/schedule/{item_id}/edit',
        data={
            'class_id': class_id, 'day_of_week': '4', 'lesson_number': '6',
            'start_time': '15:00', 'end_time': '15:45', 'subject': 'Музыка',
            'room': 'каб. 10', 'year': '2025/2026',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        item = db.session.get(Schedule, item_id)
        assert item.day_of_week == 4 and item.lesson_number == 6

    response = teacher_client.post(f'/schedule/{item_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Schedule, item_id) is None


def test_repertoire_crud(app, teacher_client):
    name = create_class(teacher_client, name='9В', grade='9')
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        '/repertoire/create',
        data={
            'title': 'Тестовая песня', 'composer': 'Композитор Тестов',
            'genre': 'Фольклор', 'class_id': class_id, 'difficulty': 'Средний',
            'duration': '2 мин', 'year': '2025/2026',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        item = Repertoire.query.filter_by(title='Тестовая песня').first()
        assert item is not None
        item_id = item.id

    response = teacher_client.post(f'/repertoire/{item_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Repertoire, item_id) is None


def test_material_upload_download_and_delete(app, teacher_client):
    name = create_class(teacher_client, name='9Г', grade='9')
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        '/materials/create',
        data={
            'title': 'Тестовый материал',
            'lesson_type': 'Урок',
            'class_id': class_id,
            'file': (io.BytesIO(b'test content'), 'test.txt'),
        },
        content_type='multipart/form-data',
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        item = Material.query.filter_by(title='Тестовый материал').first()
        assert item is not None
        assert item.file_path
        stored = os.path.join(app.config['UPLOAD_FOLDER'], item.file_path)
        assert os.path.exists(stored)
        item_id = item.id

    response = teacher_client.get(f'/materials/download/{item_id}')
    assert response.status_code == 200
    assert response.data == b'test content'
    response.close()

    response = teacher_client.post(f'/materials/{item_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Material, item_id) is None
    assert not os.path.exists(stored)


def test_material_rejects_forbidden_extension(app, teacher_client):
    name = create_class(teacher_client, name='9Д', grade='9')
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        '/materials/create',
        data={
            'title': 'Опасный файл',
            'lesson_type': 'Урок',
            'class_id': class_id,
            'file': (io.BytesIO(b'<script>'), 'payload.exe'),
        },
        content_type='multipart/form-data',
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Material.query.filter_by(title='Опасный файл').first() is None


def test_event_crud(app, teacher_client):
    name = create_class(teacher_client, name='9Е', grade='9')
    class_id = get_class_id(app, name)

    response = teacher_client.post(
        '/events/create',
        data={
            'title': 'Тестовый концерт', 'event_date': '2026-05-15',
            'event_time': '12:00', 'place': 'Актовый зал',
            'class_id': class_id, 'status': 'Запланировано',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        item = Event.query.filter_by(title='Тестовый концерт').first()
        assert item is not None
        item_id = item.id

    response = teacher_client.post(f'/events/{item_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Event, item_id) is None


def test_user_crud(app, admin_client):
    response = admin_client.post(
        '/users/create',
        data={
            'username': 'test_user', 'email': 'test@school.ru',
            'full_name': 'Тестовый Пользователь', 'password': 'secret123',
            'role': 'teacher',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='test_user').first()
        assert user is not None
        assert user.check_password('secret123')
        user_id = user.id

    response = admin_client.post(
        f'/users/{user_id}/edit',
        data={
            'email': 'test2@school.ru', 'full_name': 'Тестовый Пользователь 2',
            'role': 'teacher', 'password': '',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(User, user_id).email == 'test2@school.ru'

    response = admin_client.post(f'/users/{user_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(User, user_id) is None


def test_parent_cannot_modify_data(app, parent_client):
    assert parent_client.get('/users').status_code == 403

    response = parent_client.post(
        '/classes/create',
        data={'name': 'Хак', 'grade': '1'},
        follow_redirects=True,
    )
    assert response.status_code == 403
    with app.app_context():
        assert SchoolClass.query.filter_by(name='Хак').first() is None
