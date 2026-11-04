import subprocess
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data = os.path.abspath(r"scratch\chrome_temp_profile")

cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    f"--user-data-dir={user_data}",
    "--dump-dom",
    "http://localhost:5173/tenants"
]

res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print("DOM Length:", len(res.stdout))
if "Workspaces & Billing" in res.stdout:
    print("[FOUND] 'Workspaces & Billing' in DOM!")
else:
    print("[NOT FOUND] 'Workspaces & Billing' NOT in DOM.")
    # Print root app inner HTML snippet
    start = res.stdout.find('id="root"')
    if start != -1:
        print("Root snippet:", res.stdout[start:start+500])
    else:
        print("Stdout snippet:", res.stdout[:500])
