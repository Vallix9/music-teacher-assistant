"""Тесты журнала, планов-конспектов и отчётов."""
from datetime import date

from app import db
from app.models import Attendance, Grade, LessonPlan, SchoolClass, Student


def first_class_data(app):
    with app.app_context():
        school_class = SchoolClass.query.order_by(SchoolClass.id).first()
        assert school_class is not None
        return {
            'class_id': school_class.id,
            'student_id': school_class.students[0].id,
            'second_student_id': school_class.students[1].id,
            'schedule_id': school_class.schedule[0].id,
        }


def test_journal_pages_open(teacher_client):
    for url in ['/journal', '/journal?class_id=1', '/lesson-plans', '/reports',
                '/reports?class_id=1', '/reports?class_id=1&period=month',
                '/reports?class_id=1&period=term']:
        assert teacher_client.get(url).status_code == 200, url


def test_journal_save_and_update(app, teacher_client):
    data = first_class_data(app)
    today = date.today().isoformat()

    response = teacher_client.post('/journal/save', data={
        'class_id': data['class_id'],
        'lesson_date': today,
        'schedule_id': data['schedule_id'],
        f"att_{data['student_id']}": 'present',
        f"grade_{data['student_id']}": '5',
        f"category_{data['student_id']}": 'За урок',
        f"att_{data['second_student_id']}": 'absent',
        f"grade_{data['second_student_id']}": '3',
        f"category_{data['second_student_id']}": 'За урок',
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        attendance = Attendance.query.filter_by(
            student_id=data['student_id'], lesson_date=date.today()).first()
        grade = Grade.query.filter_by(
            student_id=data['student_id'], lesson_date=date.today()).first()
        assert attendance is not None and attendance.status == 'present'
        assert grade is not None and grade.value == 5

    response = teacher_client.post('/journal/save', data={
        'class_id': data['class_id'],
        'lesson_date': today,
        'schedule_id': data['schedule_id'],
        f"att_{data['student_id']}": 'late',
        f"grade_{data['student_id']}": '4',
        f"category_{data['student_id']}": 'За урок',
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        count = Attendance.query.filter_by(
            student_id=data['student_id'], lesson_date=date.today()).count()
        assert count == 1
        attendance = Attendance.query.filter_by(
            student_id=data['student_id'], lesson_date=date.today()).first()
        assert attendance.status == 'late'


def test_student_journal(app, teacher_client):
    data = first_class_data(app)
    response = teacher_client.get(f"/journal/student/{data['student_id']}")
    assert response.status_code == 200


def test_lesson_plan_crud(app, teacher_client):
    data = first_class_data(app)
    today = date.today().isoformat()

    response = teacher_client.post('/lesson-plans/create', data={
        'title': 'Тестовый конспект', 'topic': 'Тема', 'goal': 'Цель',
        'tasks': 'Задачи', 'lesson_type': 'Урок', 'class_id': data['class_id'],
        'lesson_date': today, 'duration': '45 мин', 'equipment': 'Фортепиано',
        'structure': 'Ход урока', 'homework': 'ДЗ', 'criteria': 'Критерии',
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        plan = LessonPlan.query.filter_by(title='Тестовый конспект').first()
        assert plan is not None
        plan_id = plan.id

    assert teacher_client.get(f'/lesson-plans/{plan_id}').status_code == 200

    response = teacher_client.post(f'/lesson-plans/{plan_id}/edit', data={
        'title': 'Тестовый конспект 2', 'class_id': data['class_id'],
        'lesson_date': today, 'duration': '45 мин',
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(LessonPlan, plan_id).title == 'Тестовый конспект 2'

    response = teacher_client.post(f'/lesson-plans/{plan_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(LessonPlan, plan_id) is None


def test_reports_and_csv_export(app, teacher_client):
    data = first_class_data(app)

    response = teacher_client.get(f"/reports?class_id={data['class_id']}")
    assert response.status_code == 200

    response = teacher_client.get(f"/reports/export?class_id={data['class_id']}")
    assert response.status_code == 200
    body = response.data.decode('utf-8-sig')
    assert 'ФИО ученика' in body
    assert ';' in body


def test_parent_journal_access(app, parent_client):
    data = first_class_data(app)
    today = date.today().isoformat()

    assert parent_client.get('/journal').status_code == 200
    assert parent_client.get('/reports').status_code == 200

    response = parent_client.post('/journal/save', data={
        'class_id': data['class_id'], 'lesson_date': today,
    })
    assert response.status_code == 403


def test_parent_cannot_open_other_student_journal(app, parent_client):
    with app.app_context():
        other_student = Student.query.filter(Student.parent_id.is_(None)).first()
        assert other_student is not None
        other_student_id = other_student.id

    assert parent_client.get(f'/journal/student/{other_student_id}').status_code == 403
