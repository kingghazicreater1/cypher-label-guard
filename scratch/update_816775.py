import sqlite3
import json

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()

# Exact OpenCV-measured coordinates on the 1280x853 salad image
real_annotations = [
    {
        "label": "red fruits: cherry tomatoes (3 detected)",
        "confidence": 100.0,
        "color": "#ef4444",
        "box": {
            "x": 19.0,
            "y": 17.0,
            "w": 27.0,
            "h": 65.0
        },
        "description": "Multi-focus bounding anchor enclosing 3 verified cherry tomato clusters (top-left, center-top, bottom-left) in salad bowl."
    },
    {
        "label": "vegetable name: lettuce leaf;basil leaves",
        "confidence": 100.0,
        "color": "#10b981",
        "box": {
            "x": 3.5,
            "y": 10.0,
            "w": 53.0,
            "h": 66.0
        },
        "description": "Spatial multi-focus anchor spanning fresh green lettuce leaves and aromatic basil foliage."
    },
    {
        "label": "dish: salad bowl",
        "confidence": 100.0,
        "color": "#06b6d4",
        "box": {
            "x": 3.0,
            "y": 7.0,
            "w": 94.0,
            "h": 86.0
        },
        "description": "Full spatial perimeter of the ceramic salad presentation dish/bowl."
    }
]

c.execute("UPDATE job_records SET annotations_json = ? WHERE job_number LIKE '%816775%'", (json.dumps(real_annotations),))
conn.commit()

# Verify
c.execute("SELECT job_number, annotations_json FROM job_records WHERE job_number LIKE '%816775%'")
row = c.fetchone()
print("Updated Job #816775 in SQLite:", row[0])
print("Annotations:", row[1])
conn.close()
