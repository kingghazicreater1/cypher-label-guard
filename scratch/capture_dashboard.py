import subprocess
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data = os.path.abspath(r"scratch\chrome_temp_profile")
out_file = os.path.abspath(r"scratch\screen_dashboard_updated.png")

cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    f"--user-data-dir={user_data}",
    f"--screenshot={out_file}",
    "--window-size=1440,900",
    "http://localhost:5173"
]

res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print("Return code:", res.returncode)
print("File exists:", os.path.exists(out_file))
if os.path.exists(out_file):
    print("Size:", os.path.getsize(out_file), "bytes")
