import io
import json
import requests
from PIL import Image

def generate_test_image():
    # 200x200 synthetic Brooks running shoe image: white background, royal blue shoe body
    img = Image.new("RGB", (200, 200), color=(250, 250, 250))
    for x in range(30, 170):
        for y in range(80, 150):
            img.putpixel((x, y), (25, 75, 210))  # Royal Blue

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    import base64
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"

def test_job():
    img_data = generate_test_image()
    payload = {
        "text": "Visual payload: brooks_ghost_running_shoe.jpg (42.1 KB)",
        "modality": "IMAGE",
        "depth_tier": "Standard",
        "image_data": img_data,
        "criteria": [
            {"name": "Product name", "type": "Free Text", "range": "Open descriptive title"},
            {"name": "Product color", "type": "Enum", "range": "Red, Blue, Green, Black, White"},
            {"name": "Price", "type": "Range", "range": "PKR 10,000 - 50,000"},
            {"name": "Quality description", "type": "Free Text", "range": "Physical surface condition"}
        ]
    }

    url = "http://127.0.0.1:8000/api/v2/infer"
    resp = requests.post(url, json=payload, timeout=25)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("Success:", data.get("success"))
        print("Anomaly Detected:", data.get("data", {}).get("consensus", {}).get("anomaly_detected"))
        print("Criteria Results:")
        for c in data.get("data", {}).get("criteria_results", []):
            print(f"  - {c.get('name')}: {c.get('value')} (Conf: {c.get('confidence')}%, Agreement: {c.get('agreement')})")
    else:
        print("Error Detail:", resp.text)

if __name__ == "__main__":
    test_job()
