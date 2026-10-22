"""Реальная проверка через HTTP-сервер (werkzeug) в отдельном потоке."""
import threading
import time
import urllib.request
import urllib.error

from app import create_app

app = create_app()
server = None


def run():
    global server
    from werkzeug.serving import make_server
    server = make_server('127.0.0.1', 5055, app)
    server.serve_forever()


t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

base = 'http://127.0.0.1:5055'
checks = []

try:
    r = urllib.request.urlopen(f'{base}/login')
    html = r.read().decode('utf-8')
    checks.append(('GET /login', r.status == 200))
    checks.append(('форма входа', 'name="password"' in html))
    checks.append(('подсказка с демо-аккаунтами', 'teacher123' in html))

    r = urllib.request.urlopen(f'{base}/')
    checks.append(('GET / без авторизации -> редирект', r.status == 200))

    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    data = b'username=teacher&password=teacher123'
    req = urllib.request.Request(f'{base}/login', data=data, method='POST')
    r = opener.open(req)
    checks.append(('POST /login', r.status == 200))

    for path in ['/', '/classes', '/schedule', '/repertoire', '/materials', '/events',
                 '/journal', '/lesson-plans', '/reports']:
        r = opener.open(f'{base}{path}')
        checks.append((f'GET {path}', r.status == 200))

    r = opener.open(f'{base}/reports?class_id=1')
    body = r.read().decode('utf-8')
    checks.append(('отчёт содержит таблицу', 'Средний балл' in body or 'средний балл' in body.lower()))
finally:
    if server:
        server.shutdown()

print('FAILED:' if any(not ok for _, ok in checks) else 'HTTP OK')
for name, ok in checks:
    print(('  OK  ' if ok else ' FAIL '), name)
