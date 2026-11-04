import requests
import time

r_login = requests.post('http://127.0.0.1:8000/api/v2/auth/login', json={'email': 'realuser@test.com', 'password': 'Secr3tPassword!'})
token = r_login.json()['token']
headers = {'Authorization': 'Bearer ' + token}

test_png = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
images = [{'name': f'batchA_photo_{i:02d}.png', 'data': test_png} for i in range(1, 13)]

payload = {
    'name': 'Batch_A Inspection (12 Photos)',
    'folder_name': 'test01',
    'depth_tier': 'Fast',
    'criteria': [
        {'name': 'Dominant Color', 'type': 'Enum', 'range': 'Red, Blue, Green'},
        {'name': 'Defect Detected?', 'type': 'Boolean', 'range': 'Yes / No'}
    ],
    'images': images
}

r_start = requests.post('http://127.0.0.1:8000/api/v2/batch/images/start', json=payload, headers=headers)
print('Start Batch Response:', r_start.status_code, r_start.json())
batch_id = r_start.json().get('batch_id')

if batch_id:
    for i in range(30):
        time.sleep(1)
        r_status = requests.get(f'http://127.0.0.1:8000/api/v2/batch/images/status/{batch_id}', headers=headers)
        st = r_status.json()
        print(f"Poll {i+1}: done {st.get('done')}/{st.get('total')} ({st.get('progress_pct')}%) - Status: {st.get('status')}")
        if st.get('status') in ['COMPLETED', 'FAILED']:
            break

    for fmt in ['json', 'csv', 'pdf']:
        r_rep = requests.get(f'http://127.0.0.1:8000/api/v2/batch/images/report/{batch_id}?format={fmt}', headers=headers)
        print(f"Report {fmt.upper()} status: {r_rep.status_code}, type: {r_rep.headers.get('content-type')}, bytes: {len(r_rep.content)}")
