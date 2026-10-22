from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Role:
    ADMIN = 'admin'
    TEACHER = 'teacher'
    PARENT = 'parent'

    LABELS = {
        ADMIN: 'Администратор',
        TEACHER: 'Учитель музыки',
        PARENT: 'Родитель',
    }


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.TEACHER)
    phone = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship('Student', backref='parent', lazy=True, foreign_keys='Student.parent_id')
    lessons = db.relationship('Schedule', backref='teacher', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_parent(self):
        return self.role == Role.PARENT

    @property
    def role_label(self):
        return Role.LABELS.get(self.role, self.role)

    def __repr__(self):
        return f'<User {self.username}>'


class SchoolClass(db.Model):
    __tablename__ = 'school_classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    grade = db.Column(db.Integer, nullable=False)
    year = db.Column(db.String(16), nullable=False, default='2025/2026')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    teacher = db.relationship('User', backref='classes')
    students = db.relationship('Student', backref='school_class', lazy=True, cascade='all, delete-orphan')

    @property
    def student_count(self):
        return len(self.students)

    def __repr__(self):
        return f'<SchoolClass {self.name}>'


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(32))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Student {self.full_name}>'


class Schedule(db.Model):
    __tablename__ = 'schedule'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(64), nullable=False, default='Музыка')
    day_of_week = db.Column(db.Integer, nullable=False)  # 1 = понедельник
    lesson_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    room = db.Column(db.String(32))
    year = db.Column(db.String(16), nullable=False, default='2025/2026')

    school_class = db.relationship('SchoolClass', backref='schedule')

    DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    @property
    def day_name(self):
        return self.DAYS[self.day_of_week - 1] if 1 <= self.day_of_week <= 7 else '-'

    def __repr__(self):
        return f'<Schedule {self.class_id} day={self.day_of_week}>'


class Repertoire(db.Model):
    __tablename__ = 'repertoire'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    composer = db.Column(db.String(180))
    genre = db.Column(db.String(64))
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'))
    year = db.Column(db.String(16), default='2025/2026')
    difficulty = db.Column(db.String(16), default='Средний')
    duration = db.Column(db.String(16))
    link = db.Column(db.String(300))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school_class = db.relationship('SchoolClass', backref='repertoire')

    DIFFICULTIES = ['Лёгкий', 'Средний', 'Сложный']

    @property
    def class_name(self):
        return self.school_class.name if self.school_class else 'Общий'

    def __repr__(self):
        return f'<Repertoire {self.title}>'


class Material(db.Model):
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    lesson_type = db.Column(db.String(32), default='Урок')
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school_class = db.relationship('SchoolClass', backref='materials')
    teacher = db.relationship('User', backref='materials')

    LESSON_TYPES = ['Урок', 'Практика', 'Контрольная', 'Проект', 'Концерт', 'Прочее']

    @property
    def class_name(self):
        return self.school_class.name if self.school_class else 'Все классы'

    def __repr__(self):
        return f'<Material {self.title}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(5))
    place = db.Column(db.String(180))
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(16), default='Запланировано')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school_class = db.relationship('SchoolClass', backref='events')
    teacher = db.relationship('User', backref='events')

    STATUSES = ['Запланировано', 'Проведено', 'Отменено']

    @property
    def class_name(self):
        return self.school_class.name if self.school_class else 'Все классы'

    def __repr__(self):
        return f'<Event {self.title}>'


class Attendance(db.Model):
    """Запись журнала посещаемости по ученику за конкретный урок."""

    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    lesson_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(16), nullable=False, default='present')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    note = db.Column(db.String(255))

    student = db.relationship('Student', backref='attendance')
    schedule = db.relationship('Schedule', backref='attendance')

    STATUSES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('excused', 'Пропуск по уважительной причине'),
    ]

    STATUS_LABELS = dict(STATUSES)

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def is_absent(self):
        return self.status in ('absent', 'excused')

    def __repr__(self):
        return f'<Attendance {self.student_id} {self.lesson_date}>'


class Grade(db.Model):
    """Оценка ученика за урок или вид деятельности."""

    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    lesson_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(32), nullable=False, default='За урок')
    value = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment = db.Column(db.String(255))

    student = db.relationship('Student', backref='grades')
    teacher = db.relationship('User', backref='grades')

    CATEGORIES = ['За урок', 'Теоретический ответ', 'Практическая работа',
                   'Самостоятельная работа', 'Проект', 'Контрольная работа']

    VALUES = [5, 4, 3, 2, 1]

    @property
    def value_label(self):
        return {5: 'отлично', 4: 'хорошо', 3: 'удовлетворительно',
                2: 'неудовлетворительно', 1: 'неудовлетворительно'}.get(self.value, str(self.value))

    def __repr__(self):
        return f'<Grade {self.student_id} {self.value}>'


class LessonPlan(db.Model):
    """План-конспект урока музыки."""

    __tablename__ = 'lesson_plans'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    topic = db.Column(db.String(180))
    goal = db.Column(db.Text)
    tasks = db.Column(db.Text)
    lesson_type = db.Column(db.String(32), default='Урок')
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    lesson_date = db.Column(db.Date)
    duration = db.Column(db.String(32), default='45 мин')
    equipment = db.Column(db.Text)
    structure = db.Column(db.Text)
    homework = db.Column(db.Text)
    criteria = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school_class = db.relationship('SchoolClass', backref='lesson_plans')
    teacher = db.relationship('User', backref='lesson_plans')

    LESSON_TYPES = ['Урок', 'Повторение', 'Закрепление', 'Контрольный', 'Проектный', 'Праздничный']

    @property
    def class_name(self):
        return self.school_class.name if self.school_class else 'Все классы'

    def __repr__(self):
        return f'<LessonPlan {self.title}>'
