"""Интеграционный тест через настоящий HTTP-сервер с включённой CSRF-защитой."""
import http.cookiejar
import re
import threading
import urllib.error
import urllib.parse
import urllib.request

from werkzeug.serving import make_server

from app import create_app
from config import Config


def test_real_http_with_csrf(tmp_path):
    class HttpConfig(Config):
        TESTING = True
        SECRET_KEY = 'http-test-secret'
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'http.db'}"
        UPLOAD_FOLDER = str(tmp_path / 'uploads')

    app = create_app(HttpConfig)
    server = make_server('127.0.0.1', 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{port}'

    try:
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

        response = opener.open(f'{base}/login')
        html = response.read().decode('utf-8')
        assert response.status == 200
        assert 'name="password"' in html
        assert 'teacher123' in html

        token_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        assert token_match is not None, 'в форме входа нет CSRF-токена'
        token = token_match.group(1)

        response = urllib.request.urlopen(f'{base}/')
        assert response.status == 200

        # POST без токена должен быть отклонён с кодом 400
        anonymous = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        try:
            anonymous.open(urllib.request.Request(
                f'{base}/login',
                data=urllib.parse.urlencode(
                    {'username': 'teacher', 'password': 'teacher123'}).encode(),
                method='POST'))
        except urllib.error.HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError('POST без CSRF-токена не был отклонён')

        data = urllib.parse.urlencode({
            'username': 'teacher',
            'password': 'teacher123',
            'csrf_token': token,
        }).encode()
        response = opener.open(
            urllib.request.Request(f'{base}/login', data=data, method='POST'))
        assert response.status == 200

        for path in ['/', '/classes', '/schedule', '/repertoire', '/materials',
                     '/events', '/journal', '/lesson-plans', '/reports']:
            response = opener.open(f'{base}{path}')
            assert response.status == 200, path

        response = opener.open(f'{base}/reports?class_id=1')
        body = response.read().decode('utf-8')
        assert 'Средний балл' in body or 'средний балл' in body.lower()
    finally:
        server.shutdown()
        thread.join(timeout=5)
