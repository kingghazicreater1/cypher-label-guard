import json
import os
from PIL import Image

with open('scratch/pixabay_1000_hard_labeled_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")

# Let's check entries where skin_ratio was between 9% and 15% (edge cases)
borderline_humans = [d for d in data if 9.0 <= d['skin_ratio_pct'] <= 15.0]
print(f"Borderline Human classifications (9-15% skin tone): {len(borderline_humans)}")
for d in borderline_humans[:8]:
    print(f"  #{d['index']} {d['filename'][:20]}... | Skin: {d['skin_ratio_pct']}% | Red: {d['red_ratio_pct']}% | Green: {d['green_ratio_pct']}% | Cat: {d['primary_category']}")

# Check entries where red_ratio was high
high_red = [d for d in data if d['red_ratio_pct'] > 20.0]
print(f"\nHigh Red images: {len(high_red)}")
for d in high_red[:8]:
    print(f"  #{d['index']} {d['filename'][:20]}... | Cat: {d['primary_category']} | Skin: {d['skin_ratio_pct']}% | Red: {d['red_ratio_pct']}% | Edible: {d['is_edible']}")
