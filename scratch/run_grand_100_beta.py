import os
import sys
import json
import time
import base64
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

folder1 = r"C:\Users\Friends\Desktop\PixabayImages"
folder2 = r"C:\Users\Friends\Desktop\Pixabay1000"

imgs1 = sorted([os.path.join(folder1, f) for f in os.listdir(folder1) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])[:50]
imgs2 = sorted([os.path.join(folder2, f) for f in os.listdir(folder2) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])[:50]

all_100_images = []
for idx, path in enumerate(imgs1):
    all_100_images.append({
        "id": idx + 1,
        "source": "PixabayImages",
        "filename": os.path.basename(path),
        "path": path,
    })

for idx, path in enumerate(imgs2):
    all_100_images.append({
        "id": idx + 51,
        "source": "Pixabay1000",
        "filename": os.path.basename(path),
        "path": path,
    })

print(f"Selected {len(all_100_images)} images:")
print(f"  - 50 from {folder1}")
print(f"  - 50 from {folder2}")

# Save the dataset manifest
manifest_path = os.path.join(os.path.dirname(__file__), "selected_100_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(all_100_images, f, indent=2)

print(f"Manifest written to {manifest_path}")
