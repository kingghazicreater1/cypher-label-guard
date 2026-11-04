import subprocess
import os
import re

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
html = res.stdout

# Look for <main or <div class="main-content
main_matches = re.findall(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
if main_matches:
    print("Main content:", main_matches[0][:1000])
else:
    print("No <main> tag found. Searching for error...")
    error_matches = re.findall(r'(Error:[^\n<]+)', html)
    print("Errors in HTML:", error_matches)
    # Check if there's any text in the body
    body = re.findall(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if body:
        print("Body snippet:", body[0][:1000])
