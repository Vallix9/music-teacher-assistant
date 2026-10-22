"""Проверка журнала, планов-конспектов и отчётов."""
from datetime import date, timedelta

import app as app_module
from app import db
from app.models import (Attendance, Grade, LessonPlan, SchoolClass, Student)

app = app_module.create_app()
app.config['TESTING'] = True
client = app.test_client()
errors = []


def check(name, cond, detail=''):
    if not cond:
        errors.append(f'{name}: {detail}')


client.post('/login', data={'username': 'teacher', 'password': 'teacher123'}, follow_redirects=True)

# --- страницы открываются ---
for url in ['/journal', '/journal?class_id=1', '/lesson-plans', '/reports', '/reports?class_id=1',
            '/reports?class_id=1&period=month', '/reports?class_id=1&period=term']:
    r = client.get(url)
    check(f'GET {url}', r.status_code == 200, r.status_code)

# --- сохранение журнала ---
with app.app_context():
    school_class = SchoolClass.query.first()
    class_id = school_class.id
    student = school_class.students[0]
    student_id = student.id
    second_student = school_class.students[1].id
    schedule_item = school_class.schedule[0]
    schedule_id = schedule_item.id

today = date.today().isoformat()
r = client.post('/journal/save', data={
    'class_id': class_id,
    'lesson_date': today,
    'schedule_id': schedule_id,
    f'att_{student_id}': 'present',
    f'grade_{student_id}': '5',
    f'category_{student_id}': 'За урок',
    f'att_{second_student}': 'absent',
    f'grade_{second_student}': '3',
    f'category_{second_student}': 'За урок',
}, follow_redirects=True)
check('journal save', r.status_code == 200, r.status_code)

with app.app_context():
    att = Attendance.query.filter_by(student_id=student_id, lesson_date=date.today()).first()
    check('attendance saved', att is not None and att.status == 'present', att.status if att else None)
    g = Grade.query.filter_by(student_id=student_id, lesson_date=date.today()).first()
    check('grade saved', g is not None and g.value == 5, g.value if g else None)

# --- повторное сохранение не плодит дубликаты ---
r = client.post('/journal/save', data={
    'class_id': class_id, 'lesson_date': today, 'schedule_id': schedule_id,
    f'att_{student_id}': 'late', f'grade_{student_id}': '4', f'category_{student_id}': 'За урок',
}, follow_redirects=True)
with app.app_context():
    count = Attendance.query.filter_by(student_id=student_id, lesson_date=date.today()).count()
    check('no duplicate attendance', count == 1, count)
    att = Attendance.query.filter_by(student_id=student_id, lesson_date=date.today()).first()
    check('attendance updated', att.status == 'late', att.status)

# --- журнал ученика ---
r = client.get(f'/journal/student/{student_id}')
check('student journal', r.status_code == 200, r.status_code)

# --- план-конспект ---
r = client.post('/lesson-plans/create', data={
    'title': 'Тестовый конспект', 'topic': 'Тема', 'goal': 'Цель', 'tasks': 'Задачи',
    'lesson_type': 'Урок', 'class_id': class_id, 'lesson_date': today, 'duration': '45 мин',
    'equipment': 'Фортепиано', 'structure': 'Ход урока', 'homework': 'ДЗ', 'criteria': 'Критерии',
}, follow_redirects=True)
check('create plan', r.status_code == 200, r.status_code)
with app.app_context():
    plan = LessonPlan.query.filter_by(title='Тестовый конспект').first()
    check('plan in db', plan is not None)
    plan_id = plan.id if plan else None

r = client.get(f'/lesson-plans/{plan_id}')
check('plan detail', r.status_code == 200, r.status_code)

r = client.post(f'/lesson-plans/{plan_id}/edit', data={
    'title': 'Тестовый конспект 2', 'class_id': class_id, 'lesson_date': today, 'duration': '45 мин',
}, follow_redirects=True)
with app.app_context():
    plan = db.session.get(LessonPlan, plan_id)
    check('plan updated', plan.title == 'Тестовый конспект 2', plan.title)

r = client.post(f'/lesson-plans/{plan_id}/delete', follow_redirects=True)
with app.app_context():
    check('plan deleted', db.session.get(LessonPlan, plan_id) is None)

# --- отчёт и CSV ---
r = client.get(f'/reports/export?class_id={class_id}')
check('csv export', r.status_code == 200, r.status_code)
check('csv has data', 'ФИО ученика' in r.data.decode('utf-8-sig'), r.data[:60])

# --- доступ родителя ---
client.get('/logout')
client.post('/login', data={'username': 'parent', 'password': 'parent123'}, follow_redirects=True)
r = client.get('/journal')
check('parent journal ok', r.status_code == 200, r.status_code)
r = client.post('/journal/save', data={'class_id': class_id, 'lesson_date': today})
check('parent cannot save journal', r.status_code == 403, r.status_code)
r = client.get('/reports')
check('parent reports ok', r.status_code == 200, r.status_code)

print('FAILED:' if errors else 'ALL NEW MODULES OK')
for e in errors:
    print(' -', e)
