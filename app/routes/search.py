from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.models import (Event, LessonPlan, Material, Repertoire, SchoolClass,
                        Student)

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    results = {'classes': [], 'students': [], 'repertoire': [],
               'materials': [], 'events': [], 'plans': []}

    if q:
        like = f'%{q}%'
        results['classes'] = SchoolClass.query.filter(
            SchoolClass.name.ilike(like)).limit(20).all()
        results['students'] = Student.query.filter(
            Student.full_name.ilike(like)).limit(20).all()
        results['repertoire'] = Repertoire.query.filter(
            db_or(Repertoire.title.ilike(like), Repertoire.composer.ilike(like))).limit(20).all()
        results['materials'] = Material.query.filter(
            Material.title.ilike(like)).limit(20).all()
        results['events'] = Event.query.filter(
            Event.title.ilike(like)).limit(20).all()
        results['plans'] = LessonPlan.query.filter(
            db_or(LessonPlan.title.ilike(like), LessonPlan.topic.ilike(like))).limit(20).all()

        if current_user.is_parent:
            child_class_ids = {s.class_id for s in current_user.students}
            child_ids = {s.id for s in current_user.students}
            results['classes'] = [c for c in results['classes'] if c.id in child_class_ids]
            results['students'] = [s for s in results['students'] if s.id in child_ids]
            results['materials'] = [m for m in results['materials']
                                    if m.class_id is None or m.class_id in child_class_ids]
            results['events'] = [e for e in results['events']
                                 if e.class_id is None or e.class_id in child_class_ids]
            results['plans'] = [p for p in results['plans']
                                if p.class_id is None or p.class_id in child_class_ids]

    total = sum(len(v) for v in results.values())
    return render_template('search/results.html', q=q, results=results, total=total)


def db_or(*conditions):
    from app import db
    return db.or_(*conditions)
