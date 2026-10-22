"""Проверка CRUD-операций всех модулей системы."""
import os
import tempfile

import app as app_module
from app import db
from app.models import Event, Material, Repertoire, Schedule, SchoolClass, Student, User

app = app_module.create_app()
app.config['TESTING'] = True
client = app.test_client()

errors = []


def check(name, cond, detail=''):
    if not cond:
        errors.append(f'{name}: {detail}')


# --- логин учителя ---
r = client.post('/login', data={'username': 'teacher', 'password': 'teacher123'}, follow_redirects=True)
check('login teacher', r.status_code == 200, r.status_code)

# --- создание класса ---
r = client.post('/classes/create', data={'name': '8В', 'grade': '8', 'year': '2025/2026'}, follow_redirects=True)
check('create class', 'Класс 8В добавлен'.encode('cp1251', 'ignore') in r.data or b'8' in r.data, r.status_code)
with app.app_context():
    sc = SchoolClass.query.filter_by(name='8В').first()
    check('class in db', sc is not None)
    new_class_id = sc.id if sc else None

# --- создание ученика ---
r = client.post('/students/create', data={'full_name': 'Тестовый Ученик', 'class_id': new_class_id},
                follow_redirects=True)
check('create student', r.status_code == 200, r.status_code)
with app.app_context():
    st = Student.query.filter_by(full_name='Тестовый Ученик').first()
    check('student in db', st is not None)
    student_id = st.id if st else None

r = client.post(f'/students/{student_id}/edit', data={'full_name': 'Тестовый Ученик 2', 'class_id': new_class_id},
                follow_redirects=True)
check('edit student', r.status_code == 200, r.status_code)
with app.app_context():
    st = db.session.get(Student, student_id)
    check('student updated', st.full_name == 'Тестовый Ученик 2', st.full_name)

r = client.post(f'/students/{student_id}/delete', follow_redirects=True)
check('delete student', r.status_code == 200, r.status_code)
with app.app_context():
    check('student deleted', db.session.get(Student, student_id) is None)

# --- расписание ---
r = client.post('/schedule/create', data={'class_id': new_class_id, 'day_of_week': '3', 'lesson_number': '5',
                                          'start_time': '14:00', 'end_time': '14:45', 'subject': 'Музыка',
                                          'room': 'каб. 9', 'year': '2025/2026'}, follow_redirects=True)
check('create schedule', r.status_code == 200, r.status_code)
with app.app_context():
    sch = Schedule.query.filter_by(class_id=new_class_id).first()
    check('schedule in db', sch is not None)
    sched_id = sch.id if sch else None

r = client.post(f'/schedule/{sched_id}/edit', data={'class_id': new_class_id, 'day_of_week': '4',
                                                    'lesson_number': '6', 'start_time': '15:00',
                                                    'end_time': '15:45', 'subject': 'Музыка',
                                                    'room': 'каб. 10', 'year': '2025/2026'},
                follow_redirects=True)
check('edit schedule', r.status_code == 200, r.status_code)

r = client.post(f'/schedule/{sched_id}/delete', follow_redirects=True)
check('delete schedule', r.status_code == 200, r.status_code)

# --- репертуар ---
r = client.post('/repertoire/create', data={'title': 'Тестовая песня', 'composer': 'Композитор Тестов',
                                            'genre': 'Фольклор', 'class_id': new_class_id,
                                            'difficulty': 'Средний', 'duration': '2 мин',
                                            'year': '2025/2026'}, follow_redirects=True)
check('create repertoire', r.status_code == 200, r.status_code)
with app.app_context():
    rep = Repertoire.query.filter_by(title='Тестовая песня').first()
    check('repertoire in db', rep is not None)
    rep_id = rep.id if rep else None
r = client.post(f'/repertoire/{rep_id}/delete', follow_redirects=True)
check('delete repertoire', r.status_code == 200, r.status_code)

# --- материал с файлом ---
tmp = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
tmp.write(b'test content')
tmp.close()
with open(tmp.name, 'rb') as fh:
    r = client.post('/materials/create', data={'title': 'Тестовый материал', 'lesson_type': 'Урок',
                                               'class_id': new_class_id, 'file': (fh, 'test.txt')},
                    content_type='multipart/form-data', follow_redirects=True)
check('create material', r.status_code == 200, r.status_code)
with app.app_context():
    mat = Material.query.filter_by(title='Тестовый материал').first()
    check('material in db', mat is not None)
    check('material file saved', mat and mat.file_path and os.path.exists(
        os.path.join(app.config['UPLOAD_FOLDER'], mat.file_path)), mat.file_path if mat else None)
    mat_id = mat.id if mat else None
    if mat:
        r = client.get(f'/materials/download/{mat_id}')
        check('material download', r.status_code == 200, r.status_code)
r = client.post(f'/materials/{mat_id}/delete', follow_redirects=True)
check('delete material', r.status_code == 200, r.status_code)
os.unlink(tmp.name)

# --- мероприятие ---
r = client.post('/events/create', data={'title': 'Тестовый концерт', 'event_date': '2026-05-15',
                                        'event_time': '12:00', 'place': 'Актовый зал',
                                        'class_id': new_class_id, 'status': 'Запланировано'},
                follow_redirects=True)
check('create event', r.status_code == 200, r.status_code)
with app.app_context():
    ev = Event.query.filter_by(title='Тестовый концерт').first()
    check('event in db', ev is not None)
    ev_id = ev.id if ev else None
r = client.post(f'/events/{ev_id}/delete', follow_redirects=True)
check('delete event', r.status_code == 200, r.status_code)

# --- удаление класса ---
r = client.post(f'/classes/{new_class_id}/delete', follow_redirects=True)
check('delete class', r.status_code == 200, r.status_code)

# --- доступ родителя ---
client.get('/logout')
r = client.post('/login', data={'username': 'parent', 'password': 'parent123'}, follow_redirects=True)
check('login parent', r.status_code == 200, r.status_code)
r = client.get('/users')
check('parent blocked from users', r.status_code == 403, r.status_code)
r = client.post('/classes/create', data={'name': 'Хак', 'grade': '1'}, follow_redirects=True)
with app.app_context():
    check('parent cannot create class', SchoolClass.query.filter_by(name='Хак').first() is None)

print('FAILED:' if errors else 'ALL CRUD OK')
for e in errors:
    print(' -', e)
