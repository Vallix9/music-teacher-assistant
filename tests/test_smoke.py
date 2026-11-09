"""Дымовые тесты: вход и доступность страниц для каждой роли."""
import pytest

from tests.conftest import login

PAGES = [
    '/',
    '/classes',
    '/schedule',
    '/repertoire',
    '/materials',
    '/events',
    '/journal',
    '/lesson-plans',
    '/reports',
    '/search?q=музыка',
]

ACCOUNTS = [
    ('admin', 'admin', 'admin123'),
    ('teacher', 'teacher', 'teacher123'),
    ('parent', 'parent', 'parent123'),
]


@pytest.mark.parametrize('role,username,password', ACCOUNTS)
def test_login_and_pages(app, role, username, password):
    client = app.test_client()
    response = login(client, username, password)
    assert response.status_code == 200
    assert 'Выход' in response.get_data(as_text=True)

    for url in PAGES:
        response = client.get(url)
        assert response.status_code == 200, f'{role}: {url} -> {response.status_code}'


@pytest.mark.parametrize('role,username,password', ACCOUNTS)
def test_users_page_is_admin_only(app, role, username, password):
    client = app.test_client()
    login(client, username, password)
    expected = 200 if role == 'admin' else 403
    assert client.get('/users').status_code == expected


@pytest.mark.parametrize('role,username,password', ACCOUNTS)
def test_login_page_redirects_authenticated_user(app, role, username, password):
    client = app.test_client()
    login(client, username, password)
    assert client.get('/login').status_code == 302


def test_anonymous_is_redirected_to_login(app):
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
