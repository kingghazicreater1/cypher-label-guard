import sqlite3
import base64
import cv2
import numpy as np

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()
c.execute("SELECT image_url FROM job_records WHERE job_number LIKE '%816775%'")
row = c.fetchone()
conn.close()

b64_data = row[0].split(',', 1)[1]
img_bytes = base64.b64decode(b64_data)
nparr = np.frombuffer(img_bytes, np.uint8)
img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
h, w, _ = img.shape

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower_red1 = np.array([0, 70, 50])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 70, 50])
upper_red2 = np.array([180, 255, 255])
mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))

contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for idx, cnt in enumerate(contours_red):
    if cv2.contourArea(cnt) > 400:
        rx, ry, rw, rh = cv2.boundingRect(cnt)
        pct_x = round((rx / w) * 100, 1)
        pct_y = round((ry / h) * 100, 1)
        pct_w = round((rw / w) * 100, 1)
        pct_h = round((rh / h) * 100, 1)
        print(f"Red Tomato #{idx+1}: x={pct_x}%, y={pct_y}%, w={pct_w}%, h={pct_h}%")

lower_green = np.array([25, 40, 40])
upper_green = np.array([85, 255, 255])
mask_green = cv2.inRange(hsv, lower_green, upper_green)
contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for idx, cnt in enumerate(contours_green):
    if cv2.contourArea(cnt) > 2000:
        gx, gy, gw, gh = cv2.boundingRect(cnt)
        pct_x = round((gx / w) * 100, 1)
        pct_y = round((gy / h) * 100, 1)
        pct_w = round((gw / w) * 100, 1)
        pct_h = round((gh / h) * 100, 1)
        print(f"Green Vegetable #{idx+1}: x={pct_x}%, y={pct_y}%, w={pct_w}%, h={pct_h}%")
