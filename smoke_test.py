import app as app_module

app = app_module.create_app()
client = app.test_client()

pages = [
    ('/login', 'get', None),
    ('/', 'get', None),
    ('/classes', 'get', None),
    ('/schedule', 'get', None),
    ('/repertoire', 'get', None),
    ('/materials', 'get', None),
    ('/events', 'get', None),
    ('/users', 'get', None),
]

failed = []
admin_only = {'/users', '/users/create'}

for role, login, pwd in [('admin', 'admin', 'admin123'),
                          ('teacher', 'teacher', 'teacher123'),
                          ('parent', 'parent', 'parent123')]:
    r = client.post('/login', data={'username': login, 'password': pwd}, follow_redirects=True)
    if r.status_code != 200:
        failed.append(f'LOGIN {role}: {r.status_code}')

    for url, method, data in pages:
        resp = client.get(url)
        expected = 200
        if url == '/login':
            expected = 302
        if url in admin_only and role != 'admin':
            expected = 403
        if resp.status_code != expected:
            failed.append(f'{role} GET {url}: {resp.status_code} (expected {expected})')

    for url in ['/classes/create', '/schedule/create', '/repertoire/create', '/materials/create', '/events/create']:
        resp = client.get(url)
        expected = 403 if role == 'parent' else 200
        if resp.status_code != expected:
            failed.append(f'{role} GET {url}: {resp.status_code} (expected {expected})')

    client.get('/logout')

print('FAILED:' if failed else 'ALL OK')
for f in failed:
    print(' -', f)
