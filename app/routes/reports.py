from datetime import date, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app import db
from app.models import Attendance, Grade, SchoolClass, Student

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def reports():
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        classes = [c for c in classes if c.id in child_class_ids]

    class_id = request.args.get('class_id', type=int)
    period = request.args.get('period', 'all')

    date_from = None
    if period == 'month':
        today = date.today()
        date_from = today - timedelta(days=30)
    elif period == 'term':
        date_from = date.today() - timedelta(days=120)

    school_class = db.session.get(SchoolClass, class_id) if class_id else None

    attendance_rows = []
    grade_rows = []
    class_stats = None
    student_rows = []
    grade_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}

    if school_class:
        students = sorted(school_class.students, key=lambda s: s.full_name)
        student_ids = [s.id for s in students]

        att_query = Attendance.query.filter(Attendance.student_id.in_(student_ids))
        grade_query = Grade.query.filter(Grade.student_id.in_(student_ids))
        if date_from:
            att_query = att_query.filter(Attendance.lesson_date >= date_from)
            grade_query = grade_query.filter(Grade.lesson_date >= date_from)

        attendance_rows = att_query.order_by(Attendance.lesson_date.desc()).all()
        all_grades = grade_query.order_by(Grade.lesson_date.desc()).all()

        for g in all_grades:
            if g.value in grade_distribution:
                grade_distribution[g.value] += 1

        for student in students:
            s_att = [a for a in attendance_rows if a.student_id == student.id]
            s_grades = [g for g in all_grades if g.student_id == student.id]
            total = len(s_att)
            absent = sum(1 for a in s_att if a.is_absent)
            late = sum(1 for a in s_att if a.status == 'late')
            percent = round((total - absent) / total * 100, 1) if total else None
            avg = round(sum(g.value for g in s_grades) / len(s_grades), 2) if s_grades else None
            student_rows.append({
                'student': student,
                'total': total,
                'absent': absent,
                'late': late,
                'percent': percent,
                'avg': avg,
                'grades_count': len(s_grades),
            })

        total_att = len(attendance_rows)
        total_absent = sum(1 for a in attendance_rows if a.is_absent)
        total_late = sum(1 for a in attendance_rows if a.status == 'late')
        class_stats = {
            'total': total_att,
            'absent': total_absent,
            'late': total_late,
            'percent': round((total_att - total_absent) / total_att * 100, 1) if total_att else None,
            'avg_grade': round(sum(g.value for g in all_grades) / len(all_grades), 2) if all_grades else None,
            'grades_count': len(all_grades),
        }

    # Сводка по всем классам
    class_summary = []
    for c in classes:
        ids = [s.id for s in c.students]
        att = Attendance.query.filter(Attendance.student_id.in_(ids))
        grd = Grade.query.filter(Grade.student_id.in_(ids))
        if date_from:
            att = att.filter(Attendance.lesson_date >= date_from)
            grd = grd.filter(Grade.lesson_date >= date_from)
        a_list = att.all()
        g_list = grd.all()
        t = len(a_list)
        ab = sum(1 for a in a_list if a.is_absent)
        class_summary.append({
            'school_class': c,
            'total': t,
            'absent': ab,
            'percent': round((t - ab) / t * 100, 1) if t else None,
            'avg_grade': round(sum(g.value for g in g_list) / len(g_list), 2) if g_list else None,
            'grades_count': len(g_list),
        })

    return render_template('reports/reports.html', classes=classes, school_class=school_class,
                           selected_class=class_id, period=period, class_stats=class_stats,
                           student_rows=student_rows, grade_distribution=grade_distribution,
                           class_summary=class_summary)


@reports_bp.route('/reports/export')
@login_required
def reports_export():
    """Выгрузка отчёта по классу в CSV."""
    classes = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    if current_user.is_parent:
        child_class_ids = [s.class_id for s in current_user.students]
        classes = [c for c in classes if c.id in child_class_ids]

    class_id = request.args.get('class_id', type=int)
    school_class = db.session.get(SchoolClass, class_id) if class_id else None
    if school_class is None:
        from flask import flash, redirect, url_for
        flash('Выберите класс для выгрузки', 'warning')
        return redirect(url_for('reports.reports'))

    import csv
    import io
    from flask import Response

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['ФИО ученика', 'Уроков всего', 'Пропусков', 'Опозданий',
                     'Посещаемость, %', 'Средний балл', 'Оценок'])

    for student in sorted(school_class.students, key=lambda s: s.full_name):
        att = Attendance.query.filter_by(student_id=student.id).all()
        grd = Grade.query.filter_by(student_id=student.id).all()
        total = len(att)
        absent = sum(1 for a in att if a.is_absent)
        late = sum(1 for a in att if a.status == 'late')
        percent = round((total - absent) / total * 100, 1) if total else 0
        avg = round(sum(g.value for g in grd) / len(grd), 2) if grd else 0
        writer.writerow([student.full_name, total, absent, late, percent, avg, len(grd)])

    filename = f'otchet_klass_{school_class.name.replace(" ", "_")}.csv'
    return Response(
        '\ufeff' + buffer.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )
