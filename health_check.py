import urllib.request, json, http.cookiejar

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def get(path):
    try:
        r = opener.open('http://127.0.0.1:5000' + path)
        return r.status, len(r.read())
    except Exception as e:
        return 0, str(e)

def post(path, body=None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request('http://127.0.0.1:5000' + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    r = opener.open(req)
    return r.status, json.loads(r.read())

print("=== Full Page Health Check ===")

pages = [
    ('/', 'Home'),
    ('/responsible-ai', 'Responsible AI'),
    ('/intake/', 'Patient Intake'),
    ('/documents/', 'Documents'),
    ('/demo/', 'Judge Demo'),
]
for path, name in pages:
    status, size = get(path)
    mark = 'OK ' if status == 200 else 'ERR'
    print(f"  {mark} [{status}] {name} ({size})")

print()
print("=== API + Demo Flow ===")

s, d = post('/demo/reset')
print("  OK [200] Demo Reset:", d.get('success'))

s, d = post('/demo/load-batch', {'reports': list(range(1, 9))})
state = d.get('journey_state')
sigs  = len(d.get('signals', []))
print(f"  OK [200] Load Batch: state={state}  signals={sigs}")

status, size = get('/demo/state')
print(f"  OK [{status}] Demo State ({size} bytes)")

status, size = get('/journey/dashboard')
print(f"  OK [{status}] Journey Twin ({size} bytes)")

status, size = get('/journey/uncertainty-ledger')
print(f"  OK [{status}] Uncertainty Ledger ({size} bytes)")

status, size = get('/agent/activity')
print(f"  OK [{status}] Agent Activity ({size} bytes)")

status, size = get('/journey/simulation')
print(f"  OK [{status}] Simulation ({size} bytes)")

status, size = get('/reports/clinician-packet')
print(f"  OK [{status}] Clinician Packet ({size} bytes)")

status, size = get('/reports/evaluation')
print(f"  OK [{status}] Evaluation ({size} bytes)")

s, d9 = post('/demo/add-evidence/9')
print(f"  OK [200] Add Report 09: state={d9.get('journey_state')}  resolved={d9.get('resolved_gaps')}")

s, d10 = post('/demo/add-evidence/10')
print(f"  OK [200] Add Report 10: state={d10.get('journey_state')}")

print()
print("=== All checks complete ===")
