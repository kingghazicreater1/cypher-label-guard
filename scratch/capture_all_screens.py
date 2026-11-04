import subprocess
import os
import time

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data = os.path.abspath(r"scratch\chrome_temp_profile")

screens = [
    ("tenants", "http://localhost:5173/tenants", r"scratch\screen_tenants_billing.png"),
    ("jobs", "http://localhost:5173/jobs", r"scratch\screen_jobs_history.png"),
    ("parliament", "http://localhost:5173/parliament", r"scratch\screen_parliament.png"),
]

for name, url, out_rel in screens:
    out_file = os.path.abspath(out_rel)
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={user_data}",
        f"--screenshot={out_file}",
        "--window-size=1440,1100",
        url
    ]
    print(f"Capturing {name} from {url}...")
    subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if os.path.exists(out_file):
        print(f"  [OK] {out_file} ({os.path.getsize(out_file)} bytes)")
    else:
        print(f"  [FAIL] {out_file} not generated")
