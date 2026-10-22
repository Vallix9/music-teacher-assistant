from datetime import date, timedelta

from app import db
from app.models import (Attendance, Event, Grade, LessonPlan, Material, Repertoire,
                        Role, Schedule, SchoolClass, Student, User)

DEFAULT_YEAR = '2025/2026'


def seed_data():
    """Наполняет базу демонстрационными данными при первом запуске."""
    if User.query.first() is not None:
        return

    admin = User(username='admin', email='admin@school.ru', full_name='Иванова Мария Петровна',
                 role=Role.ADMIN, phone='+7 900 000-00-01')
    admin.set_password('admin123')

    teacher = User(username='teacher', email='teacher@school.ru', full_name='Петров Сергей Николаевич',
                   role=Role.TEACHER, phone='+7 900 000-00-02')
    teacher.set_password('teacher123')

    teacher2 = User(username='teacher2', email='teacher2@school.ru', full_name='Смирнова Ольга Ивановна',
                    role=Role.TEACHER, phone='+7 900 000-00-03')
    teacher2.set_password('teacher123')

    parent = User(username='parent', email='parent@school.ru', full_name='Кузнецова Анна Викторовна',
                  role=Role.PARENT, phone='+7 900 000-00-04')
    parent.set_password('parent123')

    parent2 = User(username='parent2', email='parent2@school.ru', full_name='Волков Дмитрий Сергеевич',
                   role=Role.PARENT, phone='+7 900 000-00-05')
    parent2.set_password('parent123')

    db.session.add_all([admin, teacher, teacher2, parent, parent2])
    db.session.flush()

    classes = []
    for name, grade in [('1А', 1), ('2Б', 2), ('3А', 3), ('4Б', 4), ('5А', 5), ('6А', 6), ('7Б', 7)]:
        school_class = SchoolClass(name=name, grade=grade, year=DEFAULT_YEAR,
                                    teacher_id=teacher.id if grade % 2 else teacher2.id)
        classes.append(school_class)
        db.session.add(school_class)
    db.session.flush()

    students_data = [
        ('Алексеев Максим Витальевич', 0, parent.id),
        ('Белова Дарья Сергеевна', 0, parent2.id),
        ('Виноградов Кирилл Андреевич', 1, None),
        ('Гусева Софья Романовна', 1, parent.id),
        ('Дроздов Егор Павлович', 2, None),
        ('Егорова Полина Максимовна', 2, parent2.id),
        ('Жуков Никита Ильич', 3, None),
        ('Зайцева Алиса Романовна', 3, None),
        ('Ильин Артём Данилович', 4, parent.id),
        ('Ковалёва Вера Сергеевна', 4, None),
        ('Лебедев Матвей Егорович', 5, parent2.id),
        ('Морозова Ульяна Дмитриевна', 5, None),
        ('Никитин Богдан Олегович', 6, None),
        ('Орлова Ева Александровна', 6, parent.id),
    ]
    for name, class_index, parent_id in students_data:
        db.session.add(Student(full_name=name, class_id=classes[class_index].id,
                                parent_id=parent_id,
                                birth_date=date(2015 + (class_index // 2), 3 + (class_index % 8), 12)))
    db.session.flush()

    schedule_plan = [
        (classes[0], 1, 1, '08:30', '09:15', 'каб. 12'),
        (classes[1], 1, 3, '10:05', '10:50', 'каб. 12'),
        (classes[2], 2, 2, '09:25', '10:10', 'каб. 14'),
        (classes[3], 2, 4, '11:00', '11:45', 'каб. 14'),
        (classes[4], 3, 1, '08:30', '09:15', 'каб. 3'),
        (classes[5], 3, 3, '10:05', '10:50', 'каб. 3'),
        (classes[6], 4, 2, '09:25', '10:10', 'каб. 5'),
        (classes[0], 4, 5, '12:15', '13:00', 'каб. 12'),
        (classes[2], 5, 2, '09:25', '10:10', 'каб. 14'),
    ]
    for school_class, day, number, start, end, room in schedule_plan:
        db.session.add(Schedule(class_id=school_class.id,
                                teacher_id=school_class.teacher_id,
                                subject='Музыка',
                                day_of_week=day,
                                lesson_number=number,
                                start_time=start,
                                end_time=end,
                                room=room,
                                year=DEFAULT_YEAR))

    repertoire_data = [
        ('Марш', 'Шарман Ш.', 'Фольклор', classes[0].id, 'Лёгкий', '1 мин 20 с'),
        ('Светит месяц', 'Народная песня', 'Фольклор', classes[0].id, 'Лёгкий', '2 мин 05 с'),
        ('Кукушка', 'И. С. Певзняков', 'Детская песня', classes[1].id, 'Лёгкий', '1 мин 50 с'),
        ('В траве сидел кузнечик', 'В. Шибаев', 'Детская песня', classes[1].id, 'Средний', '2 мин 10 с'),
        ('Осенние листья', 'М. Исаковский', 'Хоровая', classes[2].id, 'Средний', '2 мин 40 с'),
        ('Дили-дили', 'Р. шотландская народная песня', 'Фольклор', classes[2].id, 'Средний', '1 мин 55 с'),
        ('Соловушка', 'Б. Трофимов', 'Хоровая', classes[3].id, 'Средний', '2 мин 30 с'),
        ('Лучинушка', 'И. Дудеревский', 'Хоровая', classes[3].id, 'Сложный', '3 мин 15 с'),
        ('В горнице', 'А. Алябьев', 'Русская народная песня', classes[4].id, 'Средний', '3 мин'),
        ('Бульба', 'Б. Трофимов', 'Хоровая', classes[4].id, 'Сложный', '3 мин 40 с'),
        ('Ручеёк', 'В. Голицын', 'Сюита', classes[5].id, 'Средний', '3 мин 20 с'),
        ('Баллада о солдаке', 'В. Круглов', 'Хоровая', classes[6].id, 'Сложный', '4 мин 10 с'),
        ('Симфония №1 «Классическая»', 'Д. Шостакович', 'Инструментальная', None, 'Сложный', '22 мин'),
    ]
    for title, composer, genre, class_id, difficulty, duration in repertoire_data:
        db.session.add(Repertoire(title=title, composer=composer, genre=genre, class_id=class_id,
                                  year=DEFAULT_YEAR, difficulty=difficulty, duration=duration))

    materials_data = [
        ('Конспект урока «Знакомство с народными инструментами»', 'Урок', classes[0].id, teacher.id,
         'Подробный план-конспект урока с ходом занятия.'),
        ('Слушание: Симфония №1 Шостаковича', 'Урок', classes[5].id, teacher.id,
         'Аудиозапись для анализа музыкального образа.'),
        ('Практикум по синкопе', 'Практика', classes[3].id, teacher2.id,
         'Ритмические упражнения для отработки синкопы.'),
        ('Карточки по теории: интервалы', 'Практика', None, teacher.id,
         'Раздаточный материал для повторения интервалов.'),
        ('Проект «Мой музыкальный инструмент»', 'Проект', classes[1].id, teacher.id,
         'Задание для творческой работы учеников.'),
        ('Сценарий концерта «Весенняя пастораль»', 'Концерт', None, teacher.id,
         'Сценарий школьного концерта с репертуаром.'),
        ('Контрольная работа по слушанию', 'Контрольная', classes[6].id, teacher2.id,
         'Тестовые задания по музыкальной грамоте.'),
    ]
    for title, lesson_type, class_id, teacher_id, description in materials_data:
        db.session.add(Material(title=title, description=description, lesson_type=lesson_type,
                                class_id=class_id, teacher_id=teacher_id))

    today = date.today()
    events_data = [
        ('Концерт «Весенняя пастораль»', today + timedelta(days=7), '11:00', 'Актовый зал',
         'Выступление 4 класса с хоровыми номерами.', classes[3].id, 'Запланировано'),
        ('Открытый урок музыки', today + timedelta(days=14), '10:00', 'каб. 14',
         'Открытое занятие для родителей 3 класса.', classes[2].id, 'Запланировано'),
        ('Смотр музыкальных кружков', today + timedelta(days=21), '14:00', 'Актовый зал',
         'Показ достижений учеников музыкальных кружков.', None, 'Запланировано'),
        ('Посещение концерта в ДК', today + timedelta(days=30), '16:00', 'ДК «Юность»',
         'Экскурсия на концерт симфонического оркестра.', classes[6].id, 'Запланировано'),
        ('Праздник «Осенины»', today - timedelta(days=14), '10:00', 'Актовый зал',
         'Праздничное мероприятие для 1 класса.', classes[0].id, 'Проведено'),
    ]
    for title, event_date, event_time, place, description, class_id, status in events_data:
        db.session.add(Event(title=title, description=description, event_date=event_date,
                             event_time=event_time, place=place, class_id=class_id,
                             teacher_id=teacher.id, status=status))

    # --- Журнал посещаемости и оценок ---
    all_students = Student.query.all()
    schedule_items = Schedule.query.all()
    past_offsets = [7, 14, 21, 28, 35, 42]
    status_cycle = ['present', 'present', 'present', 'late', 'present',
                    'absent', 'present', 'excused', 'present', 'present']
    grade_cycle = [5, 4, 5, 4, 3, 5, 4, 5, 3, 4]
    grade_categories = ['За урок', 'Практическая работа', 'Теоретический ответ']

    for index, student in enumerate(all_students):
        student_lessons = [s for s in schedule_items if s.class_id == student.class_id]
        for lesson_index, schedule_item in enumerate(student_lessons):
            for day_index, offset in enumerate(past_offsets):
                day = today - timedelta(days=offset)
                status = status_cycle[(index + lesson_index + day_index) % len(status_cycle)]
                db.session.add(Attendance(student_id=student.id,
                                          schedule_id=schedule_item.id,
                                          lesson_date=day,
                                          status=status,
                                          teacher_id=schedule_item.teacher_id))
                if status in ('present', 'late'):
                    value = grade_cycle[(index + lesson_index + day_index) % len(grade_cycle)]
                    db.session.add(Grade(student_id=student.id,
                                         schedule_id=schedule_item.id,
                                         lesson_date=day,
                                         category=grade_categories[day_index % len(grade_categories)],
                                         value=value,
                                         teacher_id=schedule_item.teacher_id))

    # --- Планы-конспекты уроков ---
    plans_data = [
        ('Знакомство с народными инструментами', classes[0].id,
         'Народные инструменты: знакомство',
         'Познакомить обучающихся с народными музыкальными инструментами; научить различать их по звучанию.',
         'Образовательные: познакомить с народными инструментами и их особенностями.\n'
         'Развивающие: развивать слух, чувство ритма, музыкальную память.\n'
         'Воспитательные: воспитывать интерес к народной музыке и культуре.',
         '1. Организационный момент. Приветствие, настрой на работу.\n'
         '2. Повторение: жанры народной музыки, загадки о инструментах.\n'
         '3. Изучение нового материала: демонстрация гусли, балалайки, свистульки, кастаньет.\n'
         '4. Физкультминутка «Весёлый музыкант».\n'
         '5. Практическая работа: определение инструмента по звучанию, игра на гусях.\n'
         '6. Итог урока, домашнее задание.',
         'Фортепиано, гусли, балалайка, свистулька, карточки с изображениями инструментов, '
         'музыкальные инструменты для слушания, проектор.',
         'Выучить загадки о народных инструментах; нарисовать любимый народный инструмент.',
         '5 — верно определил инструмент по звучанию, активное участие;\n'
         '4 — верно определил с помощью учителя;\n'
         '3 — затрудняется в определении, пассивное участие.'),
        ('Строение песни. Куплет и припев', classes[1].id,
         'Строение музыкального произведения',
         'Сформировать представление о строении песни (куплет, припев) на материале русских народных песен.',
         'Образовательные: научить различать куплет и припев.\n'
         'Развивающие: развивать слух, умение анализировать музыкальное произведение.\n'
         'Воспитательные: воспитывать умение слушать и понимать музыку.',
         '1. Организационный момент.\n'
         '2. Актуализация знаний: разминка «Слова-подсказки».\n'
         '3. Открытие нового: слушание песни «В траве сидел кузнечик», выделение повторов.\n'
         '4. Работа с текстом: разметка куплетов и припевов.\n'
         '5. Практическая работа: разметить куплеты и припевы в «Кукушке».\n'
         '6. Рефлексия, домашнее задание.',
         'Проектор, аудиозаписи, тексты песен с куплетами и припевами, цветные карандаши.',
         'Разметить куплеты и припевы в народной песне, выученной на прошлом уроке.',
         '5 — верно разметил и объяснил; 4 — верно разметил с помощью; 3 — допустил ошибки.'),
        ('Музыкальный фольклор России', classes[4].id,
         'Народные песни: песни разных регионов',
         'Познакомить обучающихся с народными песнями разных регионов России, сравнить их характер.',
         'Образовательные: познакомить с песнями разных регионов.\n'
         'Развивающие: развивать тембровый слух, умение сравнивать.\n'
         'Воспитательные: воспитывать уважение к традициям разных народов.',
         '1. Организационный момент.\n'
         '2. Повторение изученных песен.\n'
         '3. Слушание: «В горнице», «Бульба», сравнение характера.\n'
         '4. Проблемная ситуация: чем отличаются песни разных регионов?\n'
         '5. Практическая работа: подбор песен для своего региона.\n'
         '6. Итог урока.',
         'Компьютер, презентация, аудиозаписи песен разных регионов, карта России.',
         'Подготовить сообщение о музыкальной традиции своего региона (3–4 предложения).',
         '5 — верно сравнил, подобрал пример; 4 — сравнил с помощью учителя; 3 — ответ неполный.'),
    ]
    for title, class_id, topic, goal, tasks, structure, equipment, homework, criteria in plans_data:
        db.session.add(LessonPlan(title=title, topic=topic, goal=goal, tasks=tasks,
                                  lesson_type='Урок', class_id=class_id,
                                  lesson_date=today, duration='45 мин',
                                  equipment=equipment, structure=structure,
                                  homework=homework, criteria=criteria,
                                  teacher_id=teacher.id))

    db.session.commit()
