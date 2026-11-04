import subprocess
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
screenshot_file = os.path.abspath(r"scratch\browser_capture.png")
user_data = os.path.abspath(r"scratch\chrome_temp_profile")

cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    f"--user-data-dir={user_data}",
    f"--screenshot={screenshot_file}",
    "--window-size=1440,900",
    "http://localhost:5173"
]

print("Running command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
print("Exists:", os.path.exists(screenshot_file))
if os.path.exists(screenshot_file):
    print("Size:", os.path.getsize(screenshot_file), "bytes")
