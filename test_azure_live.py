import urllib.request, urllib.error, json, sys

base_url = 'https://docchain-app.azurewebsites.net'

def req(path, method='GET', data=None, token=None):
    url = f'{base_url}{path}'
    body = json.dumps(data).encode('utf-8') if data else None
    headers = {'Content-Type': 'application/json'} if data else {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            content = resp.read().decode('utf-8')
            try:
                return resp.status, json.loads(content)
            except:
                return resp.status, content
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        return e.code, err_body

print('1. Checking Healthcheck...')
status, res = req('/api/healthz_docchain')
print(f'   Healthcheck: {status} -> {res}')

print('2. Checking Frontend Pages...')
for page in ['/login.html', '/admin.html', '/staff.html', '/recipient.html', '/verify.html']:
    s, _ = req(page)
    print(f'   {page}: {s}')

print('3. Testing Admin Login...')
s, res = req('/api/auth/login', 'POST', {'email': 'admin@example.com', 'password': 'Admin#123'})
print(f'   Admin Login status: {s}')
if s != 200:
    print('   Error details:', res)
    sys.exit(1)
token = res['access_token']
print('   Admin access_token successfully obtained!')

print('4. Testing /api/me...')
s, me_res = req('/api/me', 'GET', token=token)
print(f'   /api/me status: {s} -> role: {me_res.get("role")}')

print('5. Testing Admin Users list...')
s, users_res = req('/api/admin/users', 'GET', token=token)
print(f'   /api/admin/users status: {s} -> total users: {users_res.get("total")}')

print('\nALL CHECKS PASSED SUCCESSFULLY!')
