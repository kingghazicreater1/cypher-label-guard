import sqlite3
import base64
import io
from PIL import Image

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()
c.execute("SELECT image_url FROM job_records WHERE job_number LIKE '%816775%'")
row = c.fetchone()
if row and row[0]:
    data_uri = row[0]
    header, b64_data = data_uri.split(',', 1)
    img_bytes = base64.b64decode(b64_data)
    im = Image.open(io.BytesIO(img_bytes))
    print(f"Image format: {im.format}, size: {im.size} (width x height), mode: {im.mode}")
conn.close()
