# -*- coding: utf-8 -*-
"""Capture UI screenshots for the coursework report."""
import os
import sqlite3
import time

import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"
OUT = os.path.join("docs", "report", "img")
os.makedirs(OUT, exist_ok=True)

for _ in range(60):
    try:
        requests.get(BASE + "/login", timeout=1)
        break
    except Exception:
        time.sleep(0.5)
else:
    raise SystemExit("server is not running")

con = sqlite3.connect(os.path.join("instance", "music_assistant.db"))
classes = [r[0] for r in con.execute("SELECT id FROM school_classes ORDER BY id")]
students = [r[0] for r in con.execute("SELECT id FROM students ORDER BY id")]
con.close()
print("classes:", classes, "students:", students[:5])

SHOTS = []


def shot(page, name):
    page.wait_for_timeout(700)
    path = os.path.join(OUT, name)
    page.screenshot(path=path)
    SHOTS.append(path)
    print("saved", path)


def login(page, user, password):
    page.context.clear_cookies()
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill("input[name=username]", user)
    page.fill("input[name=password]", password)
    page.evaluate("document.querySelector('form').submit()")
    page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)


def clean(page):
    for _ in range(5):
        try:
            page.add_style_tag(content="*{animation:none!important;transition:none!important}")
            page.evaluate("window.scrollTo(0,0)")
            return
        except Exception:
            page.wait_for_timeout(500)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
    page = ctx.new_page()

    # 1. Login page (dark)
    page.goto(BASE + "/login", wait_until="networkidle")
    clean(page)
    shot(page, "01-login.png")

    # 2. Teacher dashboard
    login(page, "teacher", "teacher123")
    clean(page)
    shot(page, "02-dashboard-teacher.png")

    # 3. Classes
    page.goto(BASE + "/classes", wait_until="networkidle")
    clean(page)
    shot(page, "03-classes.png")

    # 4. Class students
    page.goto(BASE + f"/classes/{classes[0]}/students", wait_until="networkidle")
    clean(page)
    shot(page, "04-class-students.png")

    # 5. Schedule
    page.goto(BASE + "/schedule", wait_until="networkidle")
    clean(page)
    shot(page, "05-schedule.png")

    # 6. Journal
    page.goto(BASE + f"/journal?class_id={classes[0]}", wait_until="networkidle")
    clean(page)
    shot(page, "06-journal.png")

    # 7. Reports
    page.goto(BASE + f"/reports?class_id={classes[0]}", wait_until="networkidle")
    clean(page)
    shot(page, "07-reports.png")

    # 8. Materials
    page.goto(BASE + "/materials", wait_until="networkidle")
    clean(page)
    shot(page, "08-materials.png")

    # 9. Lesson plans
    page.goto(BASE + "/lesson-plans", wait_until="networkidle")
    clean(page)
    shot(page, "09-lesson-plans.png")

    # 10. Repertoire
    page.goto(BASE + "/repertoire", wait_until="networkidle")
    clean(page)
    shot(page, "10-repertoire.png")

    # 11. Events
    page.goto(BASE + "/events", wait_until="networkidle")
    clean(page)
    shot(page, "11-events.png")

    # 12. Search results
    page.goto(BASE + "/search?q=музыка", wait_until="networkidle")
    clean(page)
    shot(page, "12-search.png")

    # 13. Light theme on dashboard
    page.goto(BASE + "/", wait_until="networkidle")
    page.evaluate("localStorage.setItem('ma-theme','light')")
    page.reload(wait_until="networkidle")
    clean(page)
    shot(page, "13-dashboard-light.png")
    page.evaluate("localStorage.setItem('ma-theme','dark')")

    # 14. Parent dashboard
    login(page, "parent", "parent123")
    clean(page)
    shot(page, "14-dashboard-parent.png")

    # 15. Users (admin)
    login(page, "admin", "admin123")
    page.goto(BASE + "/users", wait_until="networkidle")
    clean(page)
    shot(page, "15-users.png")

    # 16. Student card (teacher)
    login(page, "teacher", "teacher123")
    page.goto(BASE + f"/journal/student/{students[0]}", wait_until="networkidle")
    clean(page)
    shot(page, "16-student-card.png")

    browser.close()

print("total", len(SHOTS))
